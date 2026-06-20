"""Team dashboard endpoint."""
from datetime import date

import aiosqlite
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models import TeamDashboard, MemberTodaySummary
from app.routers.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{team_id}", response_model=TeamDashboard)
async def team_dashboard(
    team_id: int,
    todo_date: date | None = None,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Team leader dashboard: per-member todo summary + AI contribution + unsubmitted list.
    """
    target_date = todo_date or date.today()

    # All team members
    members_rows = await (
        await db.execute(
            "SELECT id, username, avatar_url FROM users WHERE team_id=?", (team_id,)
        )
    ).fetchall()

    summaries = []
    unsubmitted = []

    for member in members_rows:
        uid = member["id"]

        # Count todos
        todos = await (
            await db.execute(
                "SELECT id, status FROM daily_todos WHERE user_id=? AND todo_date=?",
                (uid, target_date.isoformat()),
            )
        ).fetchall()

        total = len(todos)
        done = sum(1 for t in todos if t["status"] == "done")

        if total == 0:
            unsubmitted.append(member["username"])

        # Count AI analysis contributions
        todo_ids = [t["id"] for t in todos]
        grand_related = 0
        small_related = 0

        for tid in todo_ids:
            analysis = await (
                await db.execute(
                    "SELECT relation FROM todo_analysis WHERE todo_id=? ORDER BY analyzed_at DESC LIMIT 1",
                    (tid,),
                )
            ).fetchone()
            if analysis:
                if analysis["relation"] == "grand":
                    grand_related += 1
                elif analysis["relation"] == "small":
                    small_related += 1

        summaries.append(
            MemberTodaySummary(
                user_id=uid,
                username=member["username"],
                avatar_url=member["avatar_url"],
                total=total,
                done=done,
                grand_related=grand_related,
                small_related=small_related,
            )
        )

    return TeamDashboard(
        date=target_date,
        team_id=team_id,
        members=summaries,
        unsubmitted=unsubmitted,
    )
