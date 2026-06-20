"""Premises (대전제/소전제) endpoints."""
from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models import PremiseCreate, PremiseOut, PremiseUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/premises", tags=["premises"])


@router.get("/", response_model=list[PremiseOut])
async def list_premises(
    type: str | None = None,
    team_id: int | None = None,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """List premises filtered by type and/or team."""
    query = "SELECT * FROM premises WHERE 1=1"
    params: list = []
    if type:
        query += " AND type=?"
        params.append(type)
    if team_id:
        query += " AND team_id=?"
        params.append(team_id)
    query += " ORDER BY created_at DESC"
    rows = await (await db.execute(query, params)).fetchall()
    return [dict(r) for r in rows]


@router.post("/", response_model=PremiseOut, status_code=201)
async def create_premise(
    body: PremiseCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a grand or small premise."""
    cur = await db.execute(
        "INSERT INTO premises (type, title, description, team_id, created_by, parent_id) VALUES (?,?,?,?,?,?)",
        (body.type, body.title, body.description, body.team_id, current_user["id"], body.parent_id),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM premises WHERE id=?", (cur.lastrowid,))
    ).fetchone()
    return dict(row)


@router.patch("/{premise_id}", response_model=PremiseOut)
async def update_premise(
    premise_id: int,
    body: PremiseUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Update a premise."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    # is_active bool → int
    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])
    updates["updated_at"] = datetime.utcnow().isoformat()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    await db.execute(
        f"UPDATE premises SET {set_clause} WHERE id=?",
        (*updates.values(), premise_id),
    )
    await db.commit()
    row = await (
        await db.execute("SELECT * FROM premises WHERE id=?", (premise_id,))
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Premise not found")
    return dict(row)


@router.delete("/{premise_id}", status_code=204)
async def delete_premise(
    premise_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Delete a premise."""
    await db.execute("DELETE FROM premises WHERE id=?", (premise_id,))
    await db.commit()
