# 🌊 TaskWave

**업무의 흐름을 탄다**

> 전사 지식 공유 플랫폼 — 팀원의 할일이 회사 목표와 어떻게 연결되는지 AI가 실시간으로 분석하고, 흐름이 막힌 곳을 먼저 감지합니다.

🌐 **Live**: http://byw-teamflow.eastasia.azurecontainer.io  
📖 **API Docs**: http://byw-teamflow.eastasia.azurecontainer.io/docs

[![Deploy to Azure](https://github.com/silano08/blow-your-work/actions/workflows/deploy.yml/badge.svg)](https://github.com/silano08/blow-your-work/actions/workflows/deploy.yml)

---

## ✨ 핵심 기능

| 기능 | 설명 |
|------|------|
| 🌊 **전사 업무 흐름 지도** | 팀 간 업무 연결을 실시간 노드 그래프로 시각화 |
| 🤖 **AI Todo 추천** | 팀 목표 기반으로 오늘 해야 할 일을 Azure OpenAI가 추천 |
| 🔍 **AI 감사 (HITL)** | AI 분류 결과를 사람이 검토·이의제기·수정 가능 |
| 🎯 **목표 관리** | 이니셔티브→목표 계층 구조로 팀 전략 정렬 (팀장 전용) |
| 📊 **비동기 데일리 스크럼** | 회의 없이 텍스트 한 줄로 전원 현황 공유 |
| ✉️ **AI 리포트 메일** | 일일 업무 분석 결과를 이메일로 발송 |

---

## 🏗️ 기술 스택

```
Frontend   : Vanilla JS SPA (index.html)
Backend    : Python 3.11 / FastAPI
AI         : GitHub Copilot SDK + Azure OpenAI (gpt-4o)
Database   : SQLite (aiosqlite)
Auth       : GitHub OAuth 2.0
Deploy     : Azure Container Instances (ACI) via GitHub Actions
Registry   : Azure Container Registry (ACR)
```

---

## 🚀 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env에 GITHUB_TOKEN, GH_CLIENT_ID, GH_CLIENT_SECRET 입력

# 3. 서버 실행
uvicorn app.main:app --reload --port 8001

# 4. 데모 모드 (로그인 없이)
open "http://localhost:8001/?demo=1"
```

---

## 🔑 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub Copilot SDK 인증 토큰 | ✅ |
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID | ✅ |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret | ✅ |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 URL | 선택 |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API 키 | 선택 |
| `FRONTEND_URL` | 프론트엔드 베이스 URL (콜백 리다이렉트용) | 선택 |

---

## 📁 프로젝트 구조

```
blow-your-work/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── database.py          # DB 초기화 + 시드 데이터
│   ├── models.py            # Pydantic 모델
│   ├── azure_ai_service.py  # Azure OpenAI 연동
│   ├── routers/
│   │   ├── auth.py          # GitHub OAuth
│   │   ├── todos.py         # Todo CRUD
│   │   ├── premises.py      # 목표/이니셔티브 관리
│   │   ├── analysis.py      # Copilot SDK AI 분석
│   │   ├── ai_audit.py      # HITL 감사
│   │   └── ai_suggest.py    # AI Todo 추천
│   └── static/
│       ├── index.html       # SPA 메인 (전체 UI)
│       └── graph-b.html     # 전사 흐름 그래프
├── .github/workflows/
│   └── deploy.yml           # Azure ACI 자동 배포
├── Dockerfile
└── requirements.txt
```

---

## 🎯 심사 기준 대응

| 항목 | 구현 내용 | 가중치 |
|------|-----------|--------|
| Copilot SDK | `/analysis/trigger` 실제 SDK 호출, 스트리밍 분석 | 25% |
| Productivity Impact | 데일리 스크럼 자동화, AI Todo 추천, 목표 정렬 | 18% |
| Azure AI & Cloud | ACI 배포 + Azure OpenAI gpt-4o 연동 | 18% |
| Functionality | E2E 동작, CRUD API, HITL 감사 루프 | 16% |
| UX | 반응형 SPA, 데모 모드, 로딩/에러 처리 | 12% |
| Responsible AI | HITL 검토, 분류 신뢰도 표시, 이의제기 기능 | 6% |
| Innovation | 전사 흐름 지도 + AI 감사 결합 | 5% |

---

## 🌐 배포

GitHub `main` 브랜치 push 시 자동 배포:

1. Docker 이미지 빌드 → Azure ACR 푸시
2. Azure ACI 컨테이너 재생성 (FQDN 고정: `byw-teamflow.eastasia.azurecontainer.io`)
3. 헬스체크 통과 확인

```bash
# 수동 배포
gh workflow run "Deploy to Azure" --ref main
```
