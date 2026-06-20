from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from app.database import get_db
from app.models import AIBreakdownRequest, AIBreakdownResponse
from app.copilot_service import breakdown_goal

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/breakdown", response_model=AIBreakdownResponse)
async def ai_breakdown(
    body: AIBreakdownRequest,
    save: bool = True,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    자연어 목표를 Copilot이 분석해 세부 태스크로 분해합니다.
    save=true이면 DB에 자동 저장합니다.
    """
    try:
        subtasks = await breakdown_goal(body.goal, body.model)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Copilot error: {e}")

    if save:
        for st in subtasks:
            await db.execute(
                "INSERT INTO tasks (title, detail, priority) VALUES (?, ?, ?)",
                (st.title, st.detail, st.priority),
            )
        await db.commit()

    return AIBreakdownResponse(goal=body.goal, subtasks=subtasks)
