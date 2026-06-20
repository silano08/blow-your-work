"""Daily Todos endpoints."""
from datetime import date, datetime

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models import DailyTodoCreate, DailyTodoOut, DailyTodoUpdate, DailyTodoWithAnalysis
from app.routers.auth import get_current_user

router = APIRouter(prefix="/daily-todos", tags=["daily-todos"])


@router.get("/", response_model=list[DailyTodoWithAnalysis])
async def list_todos(
    todo_date: date | None = None,
    user_id: int | None = None,
    team_id: int | None = None,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List todos.
    - No filters: own todos today
    - user_id: specific user's todos (same team required)
    - team_id: all team members' todos
    """
    target_date = todo_date or date.today()

    if team_id:
        # Fetch all team members' todos
        rows = await (
            await db.execute(
                """SELECT dt.*, u.username, u.avatar_url
                   FROM daily_todos dt
                   JOIN users u ON dt.user_id = u.id
                   WHERE u.team_id = ? AND dt.todo_date = ?
                   ORDER BY u.username, dt.created_at""",
                (team_id, target_date.isoformat()),
            )
        ).fetchall()
    elif user_id:
        rows = await (
            await db.execute(
                "SELECT * FROM daily_todos WHERE user_id=? AND todo_date=? ORDER BY created_at",
                (user_id, target_date.isoformat()),
            )
        ).fetchall()
    else:
        rows = await (
            await db.execute(
                "SELECT * FROM daily_todos WHERE user_id=? AND todo_date=? ORDER BY created_at",
                (current_user["id"], target_date.isoformat()),
            )
        ).fetchall()

    results = []
    for row in rows:
        todo = dict(row)
        # Attach latest analysis
        analysis_row = await (
            await db.execute(
                "SELECT * FROM todo_analysis WHERE todo_id=? ORDER BY analyzed_at DESC LIMIT 1",
                (todo["id"],),
            )
        ).fetchone()
        todo["analysis"] = dict(analysis_row) if analysis_row else None
        results.append(todo)
    return results


@router.post("/", response_model=DailyTodoOut, status_code=201)
async def create_todo(
    body: DailyTodoCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a daily todo for the current user."""
    todo_date = body.todo_date or date.today()
    cur = await db.execute(
        "INSERT INTO daily_todos (user_id, title, detail, todo_date) VALUES (?,?,?,?)",
        (current_user["id"], body.title, body.detail, todo_date.isoformat()),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM daily_todos WHERE id=?", (cur.lastrowid,))
    ).fetchone()
    return dict(row)


@router.patch("/{todo_id}", response_model=DailyTodoOut)
async def update_todo(
    todo_id: int,
    body: DailyTodoUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a todo (owner only)."""
    row = await (
        await db.execute("SELECT * FROM daily_todos WHERE id=?", (todo_id,))
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    if dict(row)["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your todo")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if updates.get("status") == "done":
        updates["completed_at"] = datetime.utcnow().isoformat()

    set_clause = ", ".join(f"{k}=?" for k in updates)
    await db.execute(
        f"UPDATE daily_todos SET {set_clause} WHERE id=?",
        (*updates.values(), todo_id),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM daily_todos WHERE id=?", (todo_id,))
    ).fetchone()
    return dict(row)


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete own todo."""
    row = await (
        await db.execute("SELECT user_id FROM daily_todos WHERE id=?", (todo_id,))
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    if dict(row)["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your todo")
    await db.execute("DELETE FROM daily_todos WHERE id=?", (todo_id,))
    await db.commit()


@router.get("/history", response_model=list[DailyTodoWithAnalysis])
async def todo_history(
    skip: int = 0,
    limit: int = 50,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Past completed todos for the current user."""
    rows = await (
        await db.execute(
            """SELECT * FROM daily_todos
               WHERE user_id=? AND status='done'
               ORDER BY completed_at DESC LIMIT ? OFFSET ?""",
            (current_user["id"], limit, skip),
        )
    ).fetchall()
    results = []
    for row in rows:
        todo = dict(row)
        analysis_row = await (
            await db.execute(
                "SELECT * FROM todo_analysis WHERE todo_id=? ORDER BY analyzed_at DESC LIMIT 1",
                (todo["id"],),
            )
        ).fetchone()
        todo["analysis"] = dict(analysis_row) if analysis_row else None
        results.append(todo)
    return results
