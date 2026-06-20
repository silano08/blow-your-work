import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db, DB_PATH
from app.routers.auth import router as auth_router
from app.routers.teams import router as teams_router
from app.routers.premises import router as premises_router
from app.routers.daily_todos import router as daily_todos_router
from app.routers.dashboard import router as dashboard_router
from app.routers.analysis import router as analysis_router
from app.routers.slack import router as slack_router
from app.routers.ai_audit import router as ai_audit_router
from app.routers.ai_suggest import router as ai_suggest_router

load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"
_START_TIME = time.time()
VERSION = "0.3.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Hivemind — 집단지성이 목표를 완성한다",
    description="전사 업무 연관 그래프 · AI 의사결정 감사 · 비동기 데일리 스크럼",
    version=VERSION,
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(premises_router)
app.include_router(daily_todos_router)
app.include_router(dashboard_router)
app.include_router(analysis_router)
app.include_router(slack_router)
app.include_router(ai_audit_router)
app.include_router(ai_suggest_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", tags=["system"])
async def health() -> JSONResponse:
    """Liveness + readiness probe — DB, uptime, version."""
    uptime_sec = int(time.time() - _START_TIME)
    db_ok = False
    db_tables = 0
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            row = await (await db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )).fetchone()
            db_tables = row[0] if row else 0
            db_ok = db_tables > 0
    except Exception:
        pass

    status = "ok" if db_ok else "degraded"
    payload = {
        "status": status,
        "version": VERSION,
        "uptime_sec": uptime_sec,
        "uptime_human": _fmt_uptime(uptime_sec),
        "db": {"ok": db_ok, "tables": db_tables},
        "url": os.getenv("FRONTEND_URL", "https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io"),
    }
    code = 200 if db_ok else 503
    return JSONResponse(content=payload, status_code=code)


@app.get("/ready", tags=["system"])
async def ready() -> dict:
    """Kubernetes-style readiness probe (lightweight)."""
    return {"ready": True}


def _fmt_uptime(sec: int) -> str:
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    """Serve the SPA."""
    return FileResponse(STATIC_DIR / "index.html")
