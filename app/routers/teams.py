"""Teams management endpoints."""
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models import TeamCreate, TeamOut, UserOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/", response_model=list[TeamOut])
async def list_teams(db: aiosqlite.Connection = Depends(get_db)):
    """List all teams."""
    rows = await (await db.execute("SELECT * FROM teams ORDER BY name")).fetchall()
    return [dict(r) for r in rows]


@router.post("/", response_model=TeamOut, status_code=201)
async def create_team(
    body: TeamCreate,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Create a new team."""
    cur = await db.execute("INSERT INTO teams (name) VALUES (?)", (body.name,))
    await db.commit()
    row = await (await db.execute("SELECT * FROM teams WHERE id=?", (cur.lastrowid,))).fetchone()
    return dict(row)


@router.get("/{team_id}/members", response_model=list[UserOut])
async def list_members(
    team_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """List team members."""
    rows = await (
        await db.execute("SELECT * FROM users WHERE team_id=? ORDER BY username", (team_id,))
    ).fetchall()
    return [dict(r) for r in rows]


@router.patch("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: int,
    user_id: int,
    role: str,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a member's role. Only admin or leader allowed."""
    if current_user["role"] not in ("admin", "leader"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if role not in ("member", "leader", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.execute(
        "UPDATE users SET role=? WHERE id=? AND team_id=?", (role, user_id, team_id)
    )
    await db.commit()
    return {"ok": True}


@router.post("/join/{team_id}")
async def join_team(
    team_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Join a team."""
    row = await (await db.execute("SELECT id FROM teams WHERE id=?", (team_id,))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    await db.execute("UPDATE users SET team_id=? WHERE id=?", (team_id, current_user["id"]))
    await db.commit()
    return {"ok": True}
