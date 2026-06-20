# Agent Rules

AI agent가 이 저장소에서 작업할 때 따라야 할 규칙입니다.

## 프로젝트 개요

- **프로젝트명**: blow-your-work
- **언어/프레임워크**: Python / FastAPI
- **가상환경**: `.venv/`
- **주요 디렉토리**: `app/` (라우터, 모델, 서비스)

## 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload
```

## 코딩 컨벤션

- Python 타입 힌트 필수 사용
- 함수/클래스 docstring 작성
- 라우터는 `app/routers/`에 분리
- 환경변수는 `.env` 파일로 관리

## 작업 규칙

- 코드 변경 전 기존 테스트가 있으면 반드시 실행
- 새 파일 생성 시 기존 프로젝트 구조를 따름
- 불필요한 파일/주석을 남기지 않음

## 금지 사항

- 시크릿/API 키 하드코딩 금지
- `.env` 파일 커밋 금지
- 기존 동작을 깨는 변경 금지 (테스트 확인 필수)
