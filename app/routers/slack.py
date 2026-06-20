"""Slack 알림 — 일일 요약 + 미작성 팀원 리마인더."""
import os
from datetime import date, datetime

import aiosqlite
import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/slack", tags=["slack"])

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


# ── 공통 헬퍼 ─────────────────────────────────────────────────────────────

async def _post_slack(payload: dict) -> bool:
    """Slack Incoming Webhook으로 메시지를 전송합니다."""
    if not SLACK_WEBHOOK_URL:
        return False
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(SLACK_WEBHOOK_URL, json=payload)
        return r.status_code == 200


def _relation_emoji(relation: str | None) -> str:
    return {"initiative": "🚀", "goal": "🎯", "grand": "🚀", "small": "🎯"}.get(relation or "none", "—")


# ── 일일 요약 ──────────────────────────────────────────────────────────────

async def _build_daily_summary(db: aiosqlite.Connection, team_id: int, target_date: date) -> dict:
    """팀 일일 요약 Slack 블록을 생성합니다."""
    # 팀 정보
    team = await (
        await db.execute("SELECT name FROM teams WHERE id=?", (team_id,))
    ).fetchone()
    team_name = team["name"] if team else f"팀 {team_id}"

    # 팀원별 현황
    members = await (
        await db.execute(
            "SELECT id, username FROM users WHERE team_id=? ORDER BY username",
            (team_id,),
        )
    ).fetchall()

    lines = []
    total_todos = done_todos = grand_count = small_count = 0
    unsubmitted = []

    for m in members:
        todos = await (
            await db.execute(
                """SELECT dt.id, dt.title, dt.status, ta.relation
                   FROM daily_todos dt
                   LEFT JOIN todo_analysis ta ON ta.todo_id = dt.id
                   WHERE dt.user_id=? AND dt.todo_date=?""",
                (m["id"], target_date.isoformat()),
            )
        ).fetchall()

        if not todos:
            unsubmitted.append(m["username"])
            lines.append(f"  • *{m['username']}* ⚠️ 미작성")
            continue

        done = sum(1 for t in todos if t["status"] == "done")
        initiative = sum(1 for t in todos if t["relation"] in ("initiative", "grand"))
        goal = sum(1 for t in todos if t["relation"] in ("goal", "small"))
        total_todos += len(todos)
        done_todos += done
        grand_count += initiative
        small_count += goal

        pct = int(done / len(todos) * 100)
        bar = "█" * (pct // 20) + "░" * (5 - pct // 20)
        lines.append(
            f"  • *{m['username']}* `{bar}` {done}/{len(todos)} 완료"
            f"  🚀{initiative} 🎯{goal}"
        )

    total_pct = int(done_todos / total_todos * 100) if total_todos else 0
    contrib_pct = int((grand_count + small_count) / total_todos * 100) if total_todos else 0

    member_text = "\n".join(lines) or "  팀원 없음"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📋 {team_name} 일일 현황 — {target_date.strftime('%m/%d (%a)')}"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*✅ 팀 완료율*\n`{total_pct}%` ({done_todos}/{total_todos})"},
                {"type": "mrkdwn", "text": f"*🎯 목표 기여율*\n`{contrib_pct}%` (이니셔티브+목표 연관)"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*팀원별 진행 현황*\n{member_text}"},
        },
    ]

    if unsubmitted:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ *미작성 팀원* ({len(unsubmitted)}명): {', '.join(unsubmitted)}\n할일을 아직 등록하지 않았어요!",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"_TeamFlow AI · {datetime.now().strftime('%Y-%m-%d %H:%M')} 발송_"}],
    })

    return {"blocks": blocks}


@router.post("/daily-summary")
async def send_daily_summary(
    team_id: int,
    todo_date: date | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    팀 일일 요약을 Slack으로 전송합니다.
    팀장/어드민만 호출 가능.
    """
    if current_user["role"] not in ("leader", "admin"):
        raise HTTPException(status_code=403, detail="팀장만 요약을 발송할 수 있습니다")

    target_date = todo_date or date.today()
    payload = await _build_daily_summary(db, team_id, target_date)

    if not SLACK_WEBHOOK_URL:
        # Webhook 미설정 시 페이로드만 반환 (디버그용)
        return {"ok": False, "reason": "SLACK_WEBHOOK_URL 미설정", "preview": payload}

    ok = await _post_slack(payload)
    if not ok:
        raise HTTPException(status_code=502, detail="Slack 전송 실패")

    return {"ok": True, "date": target_date.isoformat(), "team_id": team_id}


# ── 미작성 리마인더 ────────────────────────────────────────────────────────

async def _build_reminder(username: str, team_name: str) -> dict:
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"⏰ *{username}님, 오늘 할일을 아직 등록하지 않으셨어요!*\n"
                        f"_{team_name}의 팀원들이 기다리고 있어요. "
                        f"TeamFlow에서 오늘의 할일을 작성해주세요_ 💪"
                    ),
                },
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": "_TeamFlow AI 자동 리마인더_"}],
            },
        ]
    }


@router.post("/remind-unsubmitted")
async def remind_unsubmitted(
    team_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    오늘 할일을 미작성한 팀원들에게 Slack 리마인더를 발송합니다.
    """
    if current_user["role"] not in ("leader", "admin"):
        raise HTTPException(status_code=403, detail="팀장만 리마인더를 발송할 수 있습니다")

    today = date.today().isoformat()

    team = await (await db.execute("SELECT name FROM teams WHERE id=?", (team_id,))).fetchone()
    team_name = team["name"] if team else f"팀 {team_id}"

    members = await (
        await db.execute("SELECT id, username FROM users WHERE team_id=?", (team_id,))
    ).fetchall()

    reminded = []
    for m in members:
        count = await (
            await db.execute(
                "SELECT COUNT(*) FROM daily_todos WHERE user_id=? AND todo_date=?",
                (m["id"], today),
            )
        ).fetchone()
        if count and count[0] == 0:
            payload = await _build_reminder(m["username"], team_name)
            if SLACK_WEBHOOK_URL:
                await _post_slack(payload)
            reminded.append(m["username"])

    return {
        "ok": True,
        "reminded": reminded,
        "count": len(reminded),
        "slack_sent": bool(SLACK_WEBHOOK_URL),
    }
