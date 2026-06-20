from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers.tasks import router as tasks_router
from app.routers.ai import router as ai_router
from app.routers.speech import router as speech_router

load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Blow Your Work — Smart Task Manager",
    description="자연어 목표를 Copilot SDK가 세부 태스크로 분해해주는 생산성 앱",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(tasks_router)
app.include_router(ai_router)
app.include_router(speech_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def serve_frontend() -> FileResponse:
    """Serve the SPA."""
    return FileResponse(STATIC_DIR / "index.html")
