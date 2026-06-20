"""AI Decision Audit (Human-in-the-Loop) router."""
from datetime import datetime
from typing import Literal, Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai-audit"])


# ── Schema ──────────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    """Human review action on an AI decision."""
    status: Literal["approved", "flagged", "overridden"]
    review_by: str = "admin"
    override_reason: Optional[str] = None
    override_output: Optional[str] = None


class HitlSettings(BaseModel):
    """Admin HITL configuration payload."""
    auto_approve_enabled: bool
    auto_approve_threshold: float  # 0.0 – 1.0
    notify_on_flag: bool
    notify_recipients: str        # e.g. "leader" | "all"
    review_required_types: str    # comma-separated, e.g. "todo_match,anomaly"


# ── Decisions ───────────────────────────────────────────────────────────────

@router.get("/decisions")
async def list_decisions(
    status: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return all AI decisions, optionally filtered by status."""
    if status:
        rows = await (
            await db.execute(
                "SELECT * FROM ai_decisions WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        ).fetchall()
    else:
        rows = await (
            await db.execute(
                "SELECT * FROM ai_decisions ORDER BY created_at DESC"
            )
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/decisions/stats")
async def decision_stats(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Summary counts for admin panel."""
    rows = await (
        await db.execute(
            """SELECT status, COUNT(*) as cnt
               FROM ai_decisions GROUP BY status"""
        )
    ).fetchall()
    stats = {r["status"]: r["cnt"] for r in rows}
    total = sum(stats.values())
    return {
        "total": total,
        "pending": stats.get("pending", 0),
        "approved": stats.get("approved", 0),
        "flagged": stats.get("flagged", 0),
        "overridden": stats.get("overridden", 0),
    }


@router.post("/decisions/{decision_id}/review")
async def review_decision(
    decision_id: int,
    body: ReviewRequest,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Human review: approve / flag / override an AI decision."""
    row = await (
        await db.execute(
            "SELECT id FROM ai_decisions WHERE id = ?", (decision_id,)
        )
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Decision not found")

    await db.execute(
        """UPDATE ai_decisions
           SET status = ?, review_by = ?, override_reason = ?,
               override_output = ?, reviewed_at = ?
           WHERE id = ?""",
        (
            body.status,
            current_user.get("name") or current_user.get("username") or body.review_by,
            body.override_reason,
            body.override_output,
            datetime.utcnow().isoformat(),
            decision_id,
        ),
    )
    await db.commit()
    return {"ok": True, "id": decision_id, "status": body.status}


# ── HITL Settings ────────────────────────────────────────────────────────────

@router.get("/hitl-settings")
async def get_hitl_settings(
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return current HITL admin configuration."""
    rows = await (
        await db.execute("SELECT key, value FROM hitl_settings")
    ).fetchall()
    return {r["key"]: r["value"] for r in rows}


@router.put("/hitl-settings")
async def update_hitl_settings(
    body: HitlSettings,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Overwrite HITL settings (admin only)."""
    if current_user.get("role") != "leader":
        raise HTTPException(status_code=403, detail="Leader role required")

    now = datetime.utcnow().isoformat()
    updates = [
        ("auto_approve_enabled",  "1" if body.auto_approve_enabled else "0"),
        ("auto_approve_threshold", str(body.auto_approve_threshold)),
        ("notify_on_flag",         "1" if body.notify_on_flag else "0"),
        ("notify_recipients",      body.notify_recipients),
        ("review_required_types",  body.review_required_types),
    ]
    for key, value in updates:
        await db.execute(
            """INSERT INTO hitl_settings (key, value, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value, now),
        )
    await db.commit()
    return {"ok": True}


# ── Mail preview data ─────────────────────────────────────────────────────────

@router.get("/mail-preview/{user_id}")
async def mail_preview(
    user_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return structured data for the team-member email preview."""
    user = await (
        await db.execute(
            "SELECT id, username, name FROM users WHERE id = ?", (user_id,)
        )
    ).fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    todos_rows = await (
        await db.execute(
            """SELECT dt.id, dt.title, dt.status,
                      ta.confidence, ta.relation, p.title AS premise_title
               FROM daily_todos dt
               LEFT JOIN todo_analysis ta ON ta.todo_id = dt.id
               LEFT JOIN premises p ON p.id = ta.premise_id
               WHERE dt.user_id = ? AND dt.todo_date = date('now')
               ORDER BY dt.id""",
            (user_id,),
        )
    ).fetchall()

    pending_decisions = await (
        await db.execute(
            """SELECT COUNT(*) as cnt FROM ai_decisions
               WHERE status = 'pending'"""
        )
    ).fetchone()

    return {
        "user": dict(user),
        "todos": [dict(r) for r in todos_rows],
        "pending_ai_decisions": pending_decisions["cnt"] if pending_decisions else 0,
    }
