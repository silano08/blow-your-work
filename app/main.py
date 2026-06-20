import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("taskwave")

STATIC_DIR = Path(__file__).parent / "static"
_START_TIME = time.time()
VERSION = "0.3.0"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://d3js.org https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://avatars.githubusercontent.com https://github.com; "
            "connect-src 'self' https://api.github.com; "
            "frame-src 'self';"
        )
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each request with method, path, status, and duration."""
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "%s %s %s %dms",
            request.method, request.url.path,
            response.status_code, duration_ms,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    logger.info("TaskWave v%s starting up", VERSION)
    await init_db()
    logger.info("DB initialized")
    yield
    logger.info("TaskWave shutting down")


app = FastAPI(
    title="TaskWave — 업무의 흐름을 탄다",
    description="전사 지식 공유 플랫폼 · AI 업무 흐름 분석 · 비동기 데일리 스크럼",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

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
