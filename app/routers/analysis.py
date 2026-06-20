"""Todo × 전제 AI 기여도 분석 엔드포인트."""
import asyncio
import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models import AnalysisTriggerResponse
from app.copilot_service import analyze_todo_premise, analyze_todos_batch
from app.routers.auth import get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _normalize_relation(relation: str | None) -> str:
    """Normalize legacy relation labels to the current schema."""
    normalized = (relation or "none").lower()
    if normalized == "grand":
        return "initiative"
    if normalized == "small":
        return "goal"
    if normalized not in {"initiative", "goal", "none"}:
        return "none"
    return normalized


async def _run_analysis(db: aiosqlite.Connection, todo_ids: list[int] | None = None) -> int:
    """
    실제 분석 실행 — Copilot SDK가 각 Todo를 전제와 매핑합니다.
    todo_ids=None 이면 오늘 미분석 Todo 전체 대상.
    """
    # 활성 전제 목록 조회
    premises_rows = await (
        await db.execute("SELECT id, type, title, description FROM premises WHERE is_active=1")
    ).fetchall()
    premises = [dict(r) for r in premises_rows]

    if not premises:
        return 0

    # 분석 대상 Todo 조회
    if todo_ids:
        placeholders = ",".join("?" * len(todo_ids))
        todos_rows = await (
            await db.execute(
                f"SELECT id, title, detail FROM daily_todos WHERE id IN ({placeholders})",
                todo_ids,
            )
        ).fetchall()
    else:
        # 오늘 날짜 중 아직 분석 안 된 Todo
        todos_rows = await (
            await db.execute(
                """SELECT dt.id, dt.title, dt.detail
                   FROM daily_todos dt
                   WHERE dt.todo_date = date('now')
                   AND NOT EXISTS (
                       SELECT 1 FROM todo_analysis ta WHERE ta.todo_id = dt.id
                   )"""
            )
        ).fetchall()

    todos = [dict(r) for r in todos_rows]
    if not todos:
        return 0

    # Copilot SDK 배치 분석
    results = await analyze_todos_batch(todos, premises)

    # 결과 저장
    for r in results:
        relation = _normalize_relation(r.get("relation"))
        # 기존 분석 삭제 후 재삽입 (최신 분석으로 갱신)
        await db.execute("DELETE FROM todo_analysis WHERE todo_id=?", (r["todo_id"],))
        await db.execute(
            """INSERT INTO todo_analysis
               (todo_id, premise_id, relation, confidence, reason)
               VALUES (?,?,?,?,?)""",
            (r["todo_id"], r.get("premise_id"), relation, r["confidence"], r["reason"]),
        )

    await db.commit()
    return len(results)


async def _stream_analysis(current_user: dict, db: aiosqlite.Connection) -> StreamingResponse:
    """SSE 스트리밍으로 분석 진행 상황을 실시간 전송."""

    async def event_generator():
        todos_rows = await (
            await db.execute(
                """SELECT dt.id, dt.title, dt.detail
                   FROM daily_todos dt
                   WHERE dt.todo_date = date('now')
                   AND NOT EXISTS (
                       SELECT 1 FROM todo_analysis ta WHERE ta.todo_id = dt.id
                   )"""
            )
        ).fetchall()
        todos = [dict(r) for r in todos_rows]

        if not todos:
            yield f"data: {json.dumps({'type': 'done', 'analyzed': 0, 'message': '분석할 Todo가 없습니다'}, ensure_ascii=False)}\n\n"
            return

        premises_rows = await (
            await db.execute("SELECT id, type, title, description FROM premises WHERE is_active=1")
        ).fetchall()
        premises = [dict(r) for r in premises_rows]

        yield f"data: {json.dumps({'type': 'start', 'total': len(todos)}, ensure_ascii=False)}\n\n"

        analyzed = 0
        for todo in todos:
            yield (
                f"data: {json.dumps({'type': 'progress', 'todo_id': todo['id'], 'title': todo['title'], 'current': analyzed + 1, 'total': len(todos)}, ensure_ascii=False)}\n\n"
            )

            try:
                result = await asyncio.wait_for(
                    analyze_todo_premise(todo["title"], todo.get("detail", ""), premises),
                    timeout=30,
                )
                relation = _normalize_relation(result.get("relation"))

                await db.execute("DELETE FROM todo_analysis WHERE todo_id=?", (todo["id"],))
                await db.execute(
                    """INSERT INTO todo_analysis
                       (todo_id, premise_id, relation, confidence, reason)
                       VALUES (?,?,?,?,?)""",
                    (
                        todo["id"],
                        result.get("premise_id"),
                        relation,
                        result.get("confidence", 0.0),
                        result.get("reason", ""),
                    ),
                )
                await db.commit()
                analyzed += 1
                yield (
                    f"data: {json.dumps({'type': 'result', 'todo_id': todo['id'], 'relation': relation, 'confidence': result.get('confidence', 0.0), 'reason': result.get('reason', '')}, ensure_ascii=False)}\n\n"
                )
            except Exception as e:
                yield (
                    f"data: {json.dumps({'type': 'error', 'todo_id': todo['id'], 'message': str(e)[:100]}, ensure_ascii=False)}\n\n"
                )

        yield f"data: {json.dumps({'type': 'done', 'analyzed': analyzed}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/trigger", response_model=AnalysisTriggerResponse)
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    todo_ids: list[int] | None = None,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    AI 기여도 분석 수동 트리거.
    - todo_ids 지정: 해당 Todo만 분석
    - todo_ids 없음: 오늘 미분석 Todo 전체 분석
    """
    try:
        count = await _run_analysis(db, todo_ids)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Copilot 분석 오류: {e}")

    return AnalysisTriggerResponse(
        message=f"AI 분석 완료",
        analyzed=count,
    )


@router.post("/trigger/stream")
async def trigger_analysis_stream(
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """POST 호환 SSE 분석 스트리밍 엔드포인트."""
    return await _stream_analysis(current_user, db)


@router.get("/trigger/stream")
async def trigger_analysis_stream_get(
    current_user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    """EventSource 호환 SSE 분석 스트리밍 엔드포인트."""
    return await _stream_analysis(current_user, db)


@router.post("/trigger-one/{todo_id}", response_model=AnalysisTriggerResponse)
async def trigger_one(
    todo_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Todo 하나에 대한 즉시 분석 (Todo 작성 직후 호출)."""
    try:
        count = await _run_analysis(db, [todo_id])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Copilot 분석 오류: {e}")

    # 분석 결과 반환
    row = await (
        await db.execute(
            "SELECT * FROM todo_analysis WHERE todo_id=? ORDER BY analyzed_at DESC LIMIT 1",
            (todo_id,),
        )
    ).fetchone()

    return AnalysisTriggerResponse(
        message="분석 완료" if row else "전제와 연관성 없음",
        analyzed=count,
    )
