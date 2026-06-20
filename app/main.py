from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers.auth import router as auth_router
from app.routers.teams import router as teams_router
from app.routers.premises import router as premises_router
from app.routers.daily_todos import router as daily_todos_router
from app.routers.dashboard import router as dashboard_router
from app.routers.analysis import router as analysis_router
from app.routers.slack import router as slack_router

load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="TeamFlow — AI 팀 생산성 플랫폼",
    description="팀의 할일과 목표를 Copilot SDK AI로 연결하는 생산성 앱",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(premises_router)
app.include_router(daily_todos_router)
app.include_router(dashboard_router)
app.include_router(analysis_router)
app.include_router(slack_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    """Serve the SPA."""
    return FileResponse(STATIC_DIR / "index.html")
