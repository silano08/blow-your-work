"""Azure OpenAI 기반 팀 할일 추천 엔드포인트."""
from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, Query

from app.azure_ai_service import suggest_team_todos
from app.database import get_db

router = APIRouter(prefix="/ai", tags=["ai-suggest"])


@router.get("/suggest-todos")
async def suggest_todos(
    team_id: int = Query(..., description="팀 ID"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """팀 OKR 전제 기반으로 오늘 할일 4개를 Azure OpenAI 로 추천합니다.

    - Azure 환경변수 설정 시: Azure OpenAI / Foundry gpt-4o 사용
    - 미설정 시: 규칙형 폴백 응답 반환 (데모 호환)
    """
    rows = await (
        await db.execute(
            "SELECT id, type, title, description, is_active FROM premises WHERE team_id=? AND is_active=1",
            (team_id,),
        )
    ).fetchall()
    premises = [dict(r) for r in rows]

    suggestions = await suggest_team_todos(team_id, premises)
    return {
        "team_id": team_id,
        "model": "azure-openai/gpt-4o",
        "suggestions": suggestions,
        "count": len(suggestions),
    }
