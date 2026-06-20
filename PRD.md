# TaskWave PRD
> **캐치프라이즈**: 업무의 흐름을 탄다 — 집단지성이 목표를 완성한다

> **버전**: 0.3.0 · **최종 수정**: 2026-06-20 · **상태**: 배포 운영 중

---

## 1. 제품 개요

### 한 줄 정의
> *"업무의 흐름을 탄다 — 전사 모든 팀원의 할일이 하나의 목표 그래프로 연결되고, AI가 정렬을 감시하고 의사결정을 돕는 플랫폼"*

### 배경과 목적
기존 Jira·Notion 기반 업무 관리는 아래 문제를 해결하지 못한다:

| 문제 | 현상 |
|---|---|
| **목표 단절** | 팀원이 매일 할일을 작성하지만, 그 일이 회사/팀 목표에 기여하는지 아무도 모름 |
| **데일리 스크럼 피로** | 형식적인 회의, 누가 뭘 하는지 파악에만 30분 소요 |
| **팀 간 연결 부재** | A팀이 B팀 업무를 막고 있어도 서로 모르는 채로 지연됨 |
| **AI 블랙박스** | AI 추천이 왜 나왔는지 설명 없음, 잘못됐을 때 수정 불가 |

Hivemind는 이 문제를 **이니셔티브 → 목표 → 오늘 할일** 3계층 구조 + AI 자동 매핑으로 해결한다.

---

## 2. 타깃 유저

| 페르소나 | 역할 | 핵심 니즈 |
|---|---|---|
| **팀장 (리더)** | 팀 목표 수립, 진척도 감시 | "우리 팀이 이번 주 목표를 달성하고 있는가?" |
| **팀원 (멤버)** | 데일리 할일 작성, 목표 기여 | "내 오늘 일이 어디에 기여하는지 알고 싶다" |
| **경영진 (옵저버)** | 전사 이니셔티브 진척 모니터링 | "전사적으로 공통 목표가 얼마나 진행됐는가?" |

---

## 3. 핵심 개념 (용어 정의)

```
이니셔티브 (대전제)
  └── 분기 또는 연간 단위 전사/팀 목표
  예) "Q3 매출 30% 성장", "DML 처리 자동화"

목표 (소전제)
  └── 이니셔티브를 달성하기 위한 구체적 세부 목표
  예) "DML 배치 스크립트 완성", "고객 응대 자동화 봇 배포"

오늘의 할일 (Todo)
  └── 목표를 향해 오늘 실행할 개인 단위 작업
  예) "배치 스크립트 에러 핸들링 추가", "봇 템플릿 3개 작성"
```

AI가 Todo 작성 시 어떤 이니셔티브/목표에 기여하는지 자동 분류하고 신뢰도(confidence)를 표시한다.

---

## 4. Jira 대비 차별화 포인트

| 차별화 | Hivemind | Jira |
|---|---|---|
| **① AI 감사 (HITL)** | AI가 왜 그렇게 분류했는지 설명 + 인간이 이의제기·수정 가능 | 없음 |
| **② 비동기 팀 리듬** | 데일리 스크럼을 비동기 텍스트로 대체, 상호 감시 구조 | 스프린트 기반, 동기 회의 의존 |
| **③ 전사 집단지성 그래프** | 전 팀원 할일을 노드 그래프로 연결, 타팀 진척도 실시간 가시화 | 팀 단위 칸반 보드만 제공 |

---

## 5. 핵심 기능

### 5-1. 홈 (데일리 스크럼)
- 오늘 할일 CRUD
- AI confidence 배지 (AI ✓ 95% / AI ~ 82% / AI ? 55%)
- 비동기 스크럼 배너: 오늘 완료 / 오늘 목표 / 블로커
- AI 추천 할일 (이니셔티브 연관도 기반)
- `오늘 집중 1개` 하이라이트 (기여도 최상위 Todo)

### 5-2. 팀 탭 (집단지성 대시보드)
- **나의 인사이트**: 완료율, 이니셔티브 기여율, AI 인사이트 메시지
- **팀 오늘 현황**: 팀원별 할일 현황, 미작성 알림
- **전사 업무 연관 지도**: 3가지 뷰 전환 (Force 그래프 / 방사형 / 트리)
- **기여 히트맵**: 이니셔티브별 × 팀원별 기여 매트릭스 (실시간 계산)

### 5-3. 목표 탭 (이니셔티브/목표 관리)
- 이니셔티브 생성/수정/비활성화
- 목표(소전제) → 이니셔티브 연결 매핑
- 전체 진척도 요약

### 5-4. AI 감사 탭 (HITL - Human-in-the-Loop)
- AI 의사결정 카드 목록 (분류 이유, 신뢰도 표시)
- 팀원 액션: 승인 ✅ / 이의제기 🚩 / 수정 ✏️
- 이의제기 시 수동 분류로 오버라이드

### 5-5. 메일 미리보기
- 팀원별 주간 업무 현황 메일 HTML 미리보기
- 팀장이 발송 전 내용 검토

### 5-6. 어드민 패널 (팀장 전용)
- HITL 설정: 자동승인 임계치, 알림 켜기/끄기, 검토 필수 유형 설정
- AI 결정 큐 현황 (대기 / 검토중 / 완료)
- 디버그 패널: 실시간 AI 요청 로그

---

## 6. 기술 스택

| Layer | 기술 |
|---|---|
| Backend | FastAPI + Python 3.12, aiosqlite (SQLite) |
| AI 엔진 (주) | **GitHub Copilot SDK** — 스트리밍 세션 기반 Todo 분류, 구조화 JSON + 한국어 근거 |
| AI 엔진 (보조) | Azure OpenAI gpt-4o — Todo 추천 및 폴백 (환경변수 미설정 시 규칙 기반 폴백) |
| 음성 | Azure Cognitive Services Speech (ko-KR STT) |
| 인증 | GitHub OAuth 2.0 (session_token 쿠키 / X-Session-Token 헤더, 5분 TTL state 검증) |
| 보안 | CSP · HSTS · X-Frame-Options · Referrer-Policy (SecurityHeadersMiddleware) |
| 로깅 | RequestLoggingMiddleware (메서드·경로·상태·응답시간 기록) |
| 배포 | **Azure Container Apps (ACA)** + Azure Container Registry |
| CI/CD | GitHub Actions (main 푸시 → ACR 빌드 → ACA 재배포 → 헬스체크) |
| FQDN | `byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io` |

---

## 7. 비기능 요구사항

| 항목 | 기준 | 현황 |
|---|---|---|
| 가용성 | `/health` 응답 200 OK 항상 | ✅ DB 상태 포함 liveness 체크 |
| 응답시간 | 일반 API < 500ms, AI 분석 < 5s | ✅ RequestLoggingMiddleware로 측정 |
| 보안 헤더 | CSP · HSTS · X-Frame-Options | ✅ SecurityHeadersMiddleware 적용 |
| 인증 | 모든 비공개 API에 세션 인증 | ✅ get_current_user 의존성 |
| 프롬프트 인젝션 방어 | 입력 길이 제한, 제어문자 제거 | ✅ copilot_service.py _sanitize() |
| 시크릿 관리 | 코드 하드코딩 금지, `.env` gitignore | ✅ |
| 배포 안정성 | FQDN 고정, 재배포 후에도 URL 유지 | ✅ ACA 환경 고정 |
| 디자인 시스템 | Hecto Financial 토큰 기준 (`design.md` 참조) | ✅ |
| Key Vault / Managed Identity | Azure 네이티브 시크릿 관리 | 🔲 v0.4.0 예정 |
| App Insights / Log Analytics | 클라우드 관측성 | 🔲 v0.4.0 예정 |

---

## 8. 배포 현황

| 환경 | URL |
|---|---|
| Production | `https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io` |
| Demo (로그인 불필요) | `https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/?demo=1` |
| Health | `https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/health` |
| API Docs | `https://byw-app.wittyrock-6a71193a.eastasia.azurecontainerapps.io/docs` |

---

## 9. 로드맵

### ✅ v0.3.0 (현재 완료 · 배포 운영 중)
- [x] 이니셔티브/목표/할일 3계층 구조
- [x] Copilot SDK AI 분류 + confidence 배지 (스트리밍 세션, 구조화 JSON + 한국어 근거)
- [x] 스키마 정합화 (`_normalize_relation` — legacy `grand`/`small` 레이블 자동 변환)
- [x] 전사 연관 그래프 3뷰 (Force / 방사형 / 트리)
- [x] HITL AI 감사 (승인/이의제기/수정) — 전 API 인증 적용
- [x] 비동기 스크럼 배너
- [x] 기여 히트맵 (실시간 계산)
- [x] 팀 탭 통합 (인사이트 + 히트맵 + 그래프)
- [x] AI Todo 추천
- [x] 메일 미리보기
- [x] 어드민 HITL 설정 패널
- [x] Azure ACA + ACR + GitHub Actions 자동 배포
- [x] `/health` (DB 상태 포함) + `/ready` 헬스체크
- [x] SecurityHeadersMiddleware (CSP · HSTS · X-Frame-Options 등)
- [x] RequestLoggingMiddleware (요청별 응답시간 로깅)
- [x] 프롬프트 인젝션 방어 (입력 길이 제한 + 제어문자 제거)
- [x] GitHub OAuth state 검증 (5분 TTL)

### 🔲 v0.4.0 (다음 스프린트 후보)
- [ ] Azure Key Vault + Managed Identity 적용
- [ ] App Insights / Log Analytics 연동 (클라우드 관측성)
- [ ] Azure OpenAI 라이브 환경 활성화 (현재 규칙 기반 폴백 상태)
- [ ] 비동기 스크럼 입력 저장 + 팀원 간 공유
- [ ] HTTPS 커스텀 도메인 CNAME 연결
- [ ] 팀원 메일 실제 발송 (SMTP 연동)
- [ ] 모바일 반응형 최적화
- [ ] GitHub 이슈 → Todo 자동 임포트
- [ ] AI 분석 재시도 로직 + 상세 에러 표시

---

## 10. 프로젝트 규칙 (Non-negotiable)

1. **Azure ACA 배포 필수** — 다른 클라우드 금지
2. **GitHub Copilot SDK 사용 필수** — AI 분류는 반드시 Copilot SDK 경유 (Azure OpenAI는 보조/폴백)
3. **시크릿 하드코딩 금지** — 모든 키는 `.env` 또는 GitHub Secrets
4. **디자인 토큰 준수** — `design.md` 기준 (Hecto Financial 스타일)
5. **Python 타입 힌트 필수** + 함수/클래스 docstring
6. **DB는 SQLite (aiosqlite) 로컬 파일** — 외부 DB 서비스 사용 금지
7. **모든 비공개 API에 인증 적용** — `get_current_user` 의존성 필수
