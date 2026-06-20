"""GitHub OAuth + session management."""
import os
import secrets
import httpx
from datetime import datetime, timedelta

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.models import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")
SESSION_TTL_HOURS = 72


# ── Helpers ───────────────────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """Dependency: validate session token from cookie/header."""
    token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    row = await (
        await db.execute(
            """SELECT s.user_id, u.id, u.github_id, u.username, u.name,
                      u.avatar_url, u.role, u.team_id, u.created_at
               FROM sessions s JOIN users u ON s.user_id = u.id
               WHERE s.token = ? AND s.expires_at > datetime('now')""",
            (token,),
        )
    ).fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return dict(row)


# ── Routes ────────────────────────────────────────────────────────────────

CALLBACK_URL = os.getenv(
    "GITHUB_CALLBACK_URL",
    "https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/auth/github/callback"
)

@router.get("/github")
async def github_login():
    """Redirect to GitHub OAuth."""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")
    state = secrets.token_urlsafe(16)
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=read:user"
        f"&state={state}"
    )
    return RedirectResponse(url)


@router.get("/callback")
@router.get("/github/callback")
async def github_callback(
    code: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Handle GitHub OAuth callback, create/update user, return session."""
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_res.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get GitHub access token")

    # Fetch user info from GitHub
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        gh_user = user_res.json()

    github_id = str(gh_user["id"])
    username = gh_user.get("login", "")
    name = gh_user.get("name", username)
    avatar_url = gh_user.get("avatar_url", "")

    # Upsert user
    existing = await (
        await db.execute("SELECT id FROM users WHERE github_id = ?", (github_id,))
    ).fetchone()

    if existing:
        await db.execute(
            "UPDATE users SET username=?, name=?, avatar_url=? WHERE github_id=?",
            (username, name, avatar_url, github_id),
        )
        user_id = existing["id"]
    else:
        cur = await db.execute(
            "INSERT INTO users (github_id, username, name, avatar_url) VALUES (?,?,?,?)",
            (github_id, username, name, avatar_url),
        )
        user_id = cur.lastrowid

    # Create session
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)
    await db.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?,?,?)",
        (session_token, user_id, expires_at.isoformat()),
    )
    await db.commit()

    response = RedirectResponse(f"{FRONTEND_URL}/?login=success")
    response.set_cookie(
        "session_token",
        session_token,
        httponly=True,
        max_age=SESSION_TTL_HOURS * 3600,
        samesite="lax",
    )
    return response


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return current user info."""
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Invalidate session."""
    token = request.cookies.get("session_token") or request.headers.get("X-Session-Token")
    if token:
        await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        await db.commit()
    response = RedirectResponse(f"{FRONTEND_URL}/")
    response.delete_cookie("session_token")
    return response
