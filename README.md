# 🌊 TaskWave

**업무의 흐름을 탄다**

> 전사 지식 공유 플랫폼 — 팀원의 할일이 회사 목표와 어떻게 연결되는지 AI가 실시간으로 분석하고, 흐름이 막힌 곳을 먼저 감지합니다.

🌐 **Live**: https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io  
🔍 **Demo (로그인 없이)**: https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/?demo=1  
📖 **API Docs**: https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/docs

[![Deploy to Azure](https://github.com/silano08/blow-your-work/actions/workflows/deploy.yml/badge.svg)](https://github.com/silano08/blow-your-work/actions/workflows/deploy.yml)

---

## ✨ 핵심 기능

| 기능 | 설명 |
|------|------|
| 🤖 **AI 기여도 분석** | GitHub Copilot SDK가 Todo를 이니셔티브/목표에 자동 매핑, 신뢰도(%) + 한국어 근거 제공 |
| 🌊 **전사 업무 흐름 지도** | 팀 간 업무 연결을 Force / 방사형 / 트리 3가지 노드 그래프로 시각화 |
| 🔍 **AI 감사 (HITL)** | AI 분류 결과를 사람이 승인 / 이의제기 / 수정 가능 — Responsible AI 핵심 루프 |
| 🎯 **목표 관리** | 이니셔티브 → 목표 2계층 구조, 진척도 요약 (팀장 전용) |
| 📊 **비동기 데일리 스크럼** | 회의 없이 "완료 / 목표 / 블로커" 텍스트 한 줄로 전원 현황 공유 |
| 📈 **기여 히트맵** | 이니셔티브 × 팀원 기여도 매트릭스 실시간 계산 |
| 💡 **AI Todo 추천** | 이니셔티브 연관도 기반 오늘 집중 할일 추천 |
| ✉️ **메일 미리보기** | 팀원별 주간 업무 현황 HTML 미리보기 (팀장 검토 후 발송) |
| ⚙️ **어드민 HITL 설정** | 자동승인 임계치, AI 결정 큐 현황, 실시간 AI 요청 로그 |

---

## 🏗️ 기술 스택

```
Frontend   : Vanilla JS SPA (index.html + graph-b.html)
Backend    : Python 3.12 / FastAPI
AI (주)    : GitHub Copilot SDK — 스트리밍 세션 기반 Todo 분류
AI (보조)  : Azure OpenAI gpt-4o — Todo 추천 및 폴백
Database   : SQLite (aiosqlite) — 로컬 파일 DB, 외부 서비스 불필요
Auth       : GitHub OAuth 2.0 (session_token 쿠키 / X-Session-Token 헤더)
Deploy     : Azure Container Apps (ACA) via GitHub Actions + ACR
Security   : CSP · HSTS · X-Frame-Options · Referrer-Policy (미들웨어 적용)
```

---

## 🚀 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env에 아래 값 입력 (필수 항목 참고)

# 3. 서버 실행
uvicorn app.main:app --reload --port 8001

# 4. 데모 모드 (GitHub 로그인 없이 전체 UI 탐색)
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
| `FRONTEND_URL` | 프론트엔드 베이스 URL (OAuth 콜백 리다이렉트용) | 선택 |

> Azure OpenAI 환경변수가 없으면 규칙 기반 폴백으로 동작합니다.

---

## 📁 프로젝트 구조

```
blow-your-work/
├── app/
│   ├── main.py                # FastAPI 앱 진입점 + 미들웨어 (보안헤더, 요청로그)
│   ├── database.py            # DB 초기화 + 시드 데이터
│   ├── models.py              # Pydantic 모델
│   ├── copilot_service.py     # GitHub Copilot SDK 분석 서비스
│   ├── azure_ai_service.py    # Azure OpenAI 연동 (보조/폴백)
│   ├── routers/
│   │   ├── auth.py            # GitHub OAuth + 세션 관리
│   │   ├── daily_todos.py     # Todo CRUD
│   │   ├── premises.py        # 이니셔티브/목표 관리
│   │   ├── analysis.py        # Copilot SDK AI 기여도 분석
│   │   ├── ai_audit.py        # HITL 감사 (승인/이의제기/수정)
│   │   ├── ai_suggest.py      # AI Todo 추천
│   │   ├── teams.py           # 팀원 현황
│   │   ├── dashboard.py       # 대시보드 집계
│   │   └── slack.py           # Slack 알림 연동
│   └── static/
│       ├── index.html         # SPA 메인 (전체 UI)
│       └── graph-b.html       # 전사 흐름 그래프
├── .github/workflows/
│   └── deploy.yml             # Azure ACA 자동 배포 (ACR 푸시 → 재배포 → 헬스체크)
├── Dockerfile
└── requirements.txt
```

---

## 🔒 보안 구현 현황

| 항목 | 상태 |
|------|------|
| CSP / HSTS / X-Frame-Options | ✅ `SecurityHeadersMiddleware` 적용 |
| 요청 로깅 | ✅ `RequestLoggingMiddleware` 적용 |
| GitHub OAuth state 검증 | ✅ 5분 TTL state store |
| 모든 API 인증 | ✅ `get_current_user` 의존성 |
| 프롬프트 인젝션 방어 | ✅ 입력 길이 제한 + 제어문자 제거 |
| 시크릿 하드코딩 금지 | ✅ `.env` / GitHub Secrets |
| Key Vault / Managed Identity | 🔲 v0.4.0 예정 |

---

## 🎯 심사 기준 대응

| 항목 | 구현 내용 | 가중치 |
|------|-----------|--------|
| Copilot SDK | `/analysis/trigger` 실제 SDK 스트리밍 호출, 구조화 JSON + 한국어 근거 | 25% |
| Productivity Impact | 데일리 스크럼 비동기화, AI 목표 정렬, 집단지성 그래프 | 18% |
| Azure AI & Cloud | Azure Container Apps 배포, ACR/GitHub Actions 파이프라인, OpenAI 폴백 | 18% |
| Functionality | E2E 동작, CRUD API, HITL 감사 루프, `/health` + `/ready` | 16% |
| UX | 반응형 SPA, 데모 모드, 신뢰도 배지, 토스트, 빈 상태 처리 | 12% |
| Responsible AI | HITL 검토, 신뢰도 표시, 이의제기, 프롬프트 인젝션 방어 | 6% |
| Innovation | 전사 흐름 그래프 3뷰 + AI 감사 결합 | 5% |

---

## 🌐 배포

GitHub `main` 브랜치 push 시 자동 배포:

1. Docker 이미지 빌드 → Azure Container Registry(ACR) 푸시
2. Azure Container Apps 재배포 (FQDN 고정)
3. `/health` 헬스체크 통과 확인

```bash
# 수동 배포
gh workflow run "Deploy to Azure" --ref main
```

| 환경 | URL |
|------|-----|
| Production | https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io |
| Health | https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/health |
| API Docs | https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/docs |
