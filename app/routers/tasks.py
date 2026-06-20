from fastapi import APIRouter, Depends, HTTPException
import aiosqlite

from app.database import get_db
from app.models import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[Task])
async def list_tasks(
    status: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    if status:
        cursor = await db.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status,)
        )
    else:
        cursor = await db.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@router.post("/", response_model=Task, status_code=201)
async def create_task(
    body: TaskCreate, db: aiosqlite.Connection = Depends(get_db)
):
    cursor = await db.execute(
        "INSERT INTO tasks (title, detail, priority, parent_id) VALUES (?, ?, ?, ?)",
        (body.title, body.detail, body.priority, body.parent_id),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,))
    ).fetchone()
    return dict(row)


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: int, db: aiosqlite.Connection = Depends(get_db)):
    row = await (
        await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: int, body: TaskUpdate, db: aiosqlite.Connection = Depends(get_db)
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    await db.execute(
        f"UPDATE tasks SET {set_clause} WHERE id = ?",
        (*updates.values(), task_id),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: aiosqlite.Connection = Depends(get_db)):
    await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    await db.commit()
