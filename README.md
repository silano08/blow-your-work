# 💥 Blow Your Work

자연어 목표를 **GitHub Copilot SDK**가 실행 가능한 세부 태스크로 분해해주는 생산성 앱

🌐 **Live**: http://20.255.126.5 | 📖 **API Docs**: http://20.255.126.5/docs

## Features

- ⚡ **AI Task Breakdown** — 목표 한 줄 입력 → Copilot이 3-7개 세부 태스크로 분해
- 🎙️ **Voice Input** — Azure Speech STT (ko-KR)로 음성 목표 입력
- ✅ **Task Management** — 완료 토글, 삭제, 필터(전체/미완료/완료)
- 🚀 **Azure ACI** — Docker 컨테이너로 Azure Container Instances 배포

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Python 3.12 |
| AI | GitHub Copilot SDK (`github-copilot-sdk`) |
| Speech | Azure Cognitive Services Speech |
| DB | SQLite (aiosqlite) |
| Deploy | Azure Container Instances + ACR |
| CI/CD | GitHub Actions |

## Local Dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in GITHUB_TOKEN, AZURE_SPEECH_KEY
uvicorn app.main:app --reload
# → http://localhost:8000
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | SPA Frontend |
| GET | `/health` | Health check |
| POST | `/ai/breakdown` | Goal → subtasks (Copilot SDK) |
| GET | `/tasks/` | List all tasks |
| POST | `/tasks/` | Create task |
| PATCH | `/tasks/{id}` | Update task |
| DELETE | `/tasks/{id}` | Delete task |
| POST | `/speech/transcribe` | Audio → text (Azure STT) |

## Deploy (GitHub Actions)

`main` 브랜치 push 시 자동 배포. 필요한 Secrets:

| Secret | Description |
|--------|-------------|
| `AZURE_CREDENTIALS` | Azure SP credentials (JSON) |
| `GH_TOKEN` | GitHub token for Copilot SDK |