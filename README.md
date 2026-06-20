# 🧠 Hivemind

**집단지성이 목표를 완성한다**

모든 팀원의 데일리 할일이 회사 목표와 얼마나 연결됐는지 AI가 분석하고, 전사 그래프로 실시간 가시화합니다.

🌐 **Live**: http://byw-teamflow.eastasia.azurecontainer.io | 📖 **API Docs**: http://byw-teamflow.eastasia.azurecontainer.io/docs

---

## 핵심 개념

```
대전제 (카테고리 업무)
  예) "DML 처리 자동화하기", "매일 답장 자동화하기"
    ↓
소전제 (세부 실행 목표)
  예) "DML 배치 스크립트 완성", "Slack 봇 템플릿 구축"
    ↓
오늘의 Todo
  → Copilot SDK AI가 각 Todo를 대전제/소전제와 자동 매핑
```

---

## Features

| 기능 | 설명 |
|---|---|
| 🤖 **AI 기여도 분석** | Todo 작성 시 Copilot SDK가 어떤 대전제/소전제에 기여하는지 자동 분석 |
| ✨ **AI Todo 추천** | 급한 소전제 기반으로 오늘 해야 할 일 자동 추천 |
| 🎯 **오늘 집중 1개** | 대전제 기여도 높은 작업을 AI가 하이라이트 (Idea A) |
| 📊 **주간 인사이트** | "이번 주 할일의 N%가 목표와 무관합니다" 알림 (Idea B) |
| 🔥 **기여 히트맵** | 전제(카테고리) 선택 → 어떤 팀원이 얼마나 기여했는지 매트릭스로 시각화 (Idea C) |
| 🤖 **소전제 → Todo 분해** | Copilot이 소전제를 오늘의 Todo로 자동 분해 (Idea D) |
| 👥 **팀 대시보드** | 팀원별 할일 현황 + 미작성 알림 (팀장 뷰) |
| 📚 **히스토리** | 완료된 Todo + 복원 기능 |
| 🔔 **슬랙 알림** | 팀장에게 일일 요약, 미작성 팀원 리마인더 |

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + Python 3.12 |
| AI 분석 | GitHub Copilot SDK (`github-copilot-sdk`) |
| Speech | Azure Cognitive Services Speech (ko-KR) |
| DB | SQLite (aiosqlite) — 서버 시작 시 시드 데이터 자동 삽입 |
| Auth | GitHub OAuth |
| Deploy | Azure Container Instances + ACR |
| CI/CD | GitHub Actions (`main` 푸시 → 자동 배포) |

---

## AI 분석 흐름

```
Todo 작성
  → POST /analysis/trigger  (수동) 또는 하루 1회 배치
  → Copilot SDK가 등록된 전제 목록과 Todo를 비교
  → {"premise_id": 3, "relation": "small", "confidence": 0.94, "reason": "..."}
  → 히트맵 + 기여도 배지 업데이트
```

---

## Local Dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env에 GITHUB_TOKEN, AZURE_SPEECH_KEY, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET 입력

uvicorn app.main:app --reload
# → http://localhost:8000/?demo=1  (데모 모드)
```

---

## API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | SPA 프론트엔드 |
| GET | `/health` | 헬스체크 |
| GET | `/auth/github` | GitHub OAuth 로그인 |
| GET | `/auth/me` | 현재 유저 정보 |
| GET/POST | `/teams/` | 팀 목록/생성 |
| GET/POST | `/premises/` | 대전제/소전제 목록/생성 |
| GET/POST | `/daily-todos/` | 오늘의 할일 목록/생성 |
| GET | `/daily-todos/history` | 완료 히스토리 |
| POST | `/analysis/trigger` | AI 분석 수동 트리거 |
| GET | `/dashboard/{team_id}` | 팀 대시보드 |
| POST | `/ai/breakdown` | 목표 → Todo 분해 (Copilot SDK) |
| POST | `/speech/transcribe` | 음성 → 텍스트 (Azure STT) |

---

## GitHub Actions 배포

`main` 푸시 시 자동 배포. 필요한 Secrets:

| Secret | 설명 |
|--------|------|
| `AZURE_CREDENTIALS` | Azure SP credentials (JSON) |
| `GH_TOKEN` | GitHub token (Copilot SDK 인증) |

---

## 프로젝트 규칙

- Azure 배포 (ACI) 필수
- Copilot SDK 사용 필수
- DB는 SQLite (aiosqlite) 로컬 파일
- Python 타입 힌트 필수
- 환경변수는 `.env` 관리, 코드 하드코딩 금지