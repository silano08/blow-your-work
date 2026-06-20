import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "tasks.db")


async def get_db() -> aiosqlite.Connection:
    """Yield a DB connection with row_factory set."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    """Create all tables on startup."""
    async with aiosqlite.connect(DB_PATH) as db:
        # ── Users ──────────────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id  TEXT UNIQUE NOT NULL,
                username   TEXT NOT NULL,
                name       TEXT,
                avatar_url TEXT,
                role       TEXT DEFAULT 'member',   -- member | leader | admin
                team_id    INTEGER REFERENCES teams(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Teams ──────────────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Premises (이니셔티브 / 목표) ────────────────────────────────
        # type: 'initiative'(구 grand) | 'goal'(구 small)
        # parent_id: 목표(goal)가 이니셔티브(initiative)를 참조
        await db.execute("""
            CREATE TABLE IF NOT EXISTS premises (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT NOT NULL CHECK(type IN ('initiative', 'goal', 'grand', 'small')),
                title       TEXT NOT NULL,
                description TEXT,
                team_id     INTEGER REFERENCES teams(id),
                created_by  INTEGER REFERENCES users(id),
                parent_id   INTEGER REFERENCES premises(id) ON DELETE SET NULL,
                is_active   INTEGER DEFAULT 1,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 기존 DB에 parent_id 컬럼 안전하게 추가 (멱등)
        try:
            await db.execute("ALTER TABLE premises ADD COLUMN parent_id INTEGER REFERENCES premises(id) ON DELETE SET NULL")
        except Exception:
            pass

        # ── Daily Todos ─────────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_todos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                title       TEXT NOT NULL,
                detail      TEXT,
                status      TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'done')),
                todo_date   DATE NOT NULL DEFAULT (date('now')),
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME
            )
        """)

        # ── Todo AI Analysis ────────────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todo_analysis (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                todo_id      INTEGER NOT NULL REFERENCES daily_todos(id) ON DELETE CASCADE,
                premise_id   INTEGER REFERENCES premises(id),
                relation     TEXT CHECK(relation IN ('grand', 'small', 'none')),
                confidence   REAL DEFAULT 0.0,
                reason       TEXT,
                analyzed_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Sessions (GitHub OAuth) ─────────────────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL
            )
        """)

        # ── AI Decisions (Human-in-the-Loop 감사 테이블) ─────────────────
        # decision_type: todo_match | priority_score | team_assign | anomaly
        # status: pending | approved | flagged | overridden
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_type   TEXT NOT NULL,
                input_summary   TEXT NOT NULL,
                ai_output       TEXT NOT NULL,
                reasoning       TEXT,
                confidence      REAL DEFAULT 0.0,
                ref_todo_id     INTEGER REFERENCES daily_todos(id) ON DELETE SET NULL,
                ref_premise_id  INTEGER REFERENCES premises(id) ON DELETE SET NULL,
                status          TEXT DEFAULT 'pending'
                                    CHECK(status IN ('pending','approved','flagged','overridden')),
                review_by       TEXT,
                override_reason TEXT,
                override_output TEXT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_at     DATETIME
            )
        """)

        # ── HITL Settings (어드민 설정 KV 스토어) ────────────────────────
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hitl_settings (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_by TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 기본값 삽입 (멱등)
        await db.execute("""
            INSERT OR IGNORE INTO hitl_settings (key, value) VALUES
                ('auto_approve_enabled', '0'),
                ('auto_approve_threshold', '0.95'),
                ('notify_on_flag', '1'),
                ('notify_recipients', 'leader'),
                ('review_required_types', 'todo_match,anomaly')
        """)

        await db.commit()
        await _seed(db)


async def _seed(db: aiosqlite.Connection) -> None:
    """Insert demo data only if tables are empty (idempotent)."""
    # Skip if data already exists
    row = await (await db.execute("SELECT COUNT(*) FROM teams")).fetchone()
    if row and row[0] > 0:
        return

    from datetime import date
    today = date.today().isoformat()

    # ── Teams ──────────────────────────────────────────────────────────────
    await db.executemany(
        "INSERT OR IGNORE INTO teams (id, name) VALUES (?,?)",
        [
            (1, "결제 플랫폼 팀"),
            (2, "프로덕트 팀"),
        ],
    )

    # ── Users ──────────────────────────────────────────────────────────────
    await db.executemany(
        "INSERT OR IGNORE INTO users (id, github_id, username, name, avatar_url, role, team_id) VALUES (?,?,?,?,?,?,?)",
        [
            (1, "demo_001", "김지훈",  "김지훈 (팀장)", "https://api.dicebear.com/7.x/avataaars/svg?seed=jihun",   "leader", 1),
            (2, "demo_002", "이수아",  "이수아",         "https://api.dicebear.com/7.x/avataaars/svg?seed=sua",     "member", 1),
            (3, "demo_003", "박민준",  "박민준",         "https://api.dicebear.com/7.x/avataaars/svg?seed=minjun",  "member", 1),
            (4, "demo_004", "최서연",  "최서연",         "https://api.dicebear.com/7.x/avataaars/svg?seed=seoyeon", "member", 1),
            (5, "demo_005", "정태양",  "정태양",         "https://api.dicebear.com/7.x/avataaars/svg?seed=taeyang", "member", 2),
        ],
    )

    # ── Premises ──────────────────────────────────────────────────────────
    # 대전제 = 구체적인 카테고리 업무 (예: "DML 처리 자동화하기")
    # 이니셔티브(initiative) = 큰 방향의 카테고리 업무
    # 목표(goal) = 이니셔티브 안의 구체 실행 목표 (parent_id로 이니셔티브에 연결)
    await db.executemany(
        "INSERT OR IGNORE INTO premises (id, type, title, description, team_id, created_by, parent_id, is_active) VALUES (?,?,?,?,?,?,?,?)",
        [
            # 이니셔티브 (구 대전제)
            (1, "initiative", "반복 업무 자동화하기",         "DML 처리, 배포, 리포트 등 반복되는 업무를 자동화",           1, 1, None, 1),
            (2, "initiative", "팀 커뮤니케이션 효율화하기",   "매일 답장, 미팅 정리, 공유 문서 자동화",                    1, 1, None, 1),
            (3, "initiative", "결제 안정성 높이기",           "오류 감지, 모니터링, 빠른 핫픽스 대응",                     1, 1, None, 1),
            (4, "initiative", "사용자 경험 개선하기",         "UX 리서치 → 프로토타입 → 반영 사이클 단축",                1, 3, None, 1),
            # 목표 (구 소전제) — parent_id로 이니셔티브에 연결
            (5, "goal", "DML 처리 자동화하기",          "수동 DB 작업을 스크립트로 전환",           1, 2, 1, 1),
            (6, "goal", "매일 답장 자동화하기",          "Slack 봇으로 정기 메시지 자동 발송",        1, 1, 2, 1),
            (7, "goal", "배포 파이프라인 구축하기",      "GitHub Actions → 스테이징 자동 배포",      1, 3, 1, 1),
            (8, "goal", "결제 오류 실시간 알림 만들기",  "에러 발생 시 Slack 즉시 알림",              1, 2, 3, 1),
            (9, "goal", "결제 UX 인터뷰 5건 완료하기",  "실사용자 인터뷰로 페인포인트 도출",         1, 4, 4, 1),
        ],
    )

    # ── Daily Todos ────────────────────────────────────────────────────────
    await db.executemany(
        "INSERT OR IGNORE INTO daily_todos (id, user_id, title, detail, status, todo_date) VALUES (?,?,?,?,?,?)",
        [
            # 김지훈 (팀장)
            (1,  1, "Slack 일일 리포트 봇 메시지 템플릿 작성",   "매일 답장 자동화 작업",                      "done",  today),
            (2,  1, "팀 주간 기여도 분석 문서 업데이트",          "이번 주 대전제별 기여 현황 정리",             "done",  today),
            (3,  1, "결제 오류 알림 Slack 채널 설정",             "에러 임계치 기준 정의",                       "todo",  today),
            (4,  1, "신규 팀원 온보딩 체크리스트 자동화",         "Notion 템플릿 → GitHub Actions 연동",        "todo",  today),
            # 이수아
            (5,  2, "DML 배치 스크립트 작성 (고객 등급 업데이트)","매월 실행되는 수동 DB 작업 자동화",           "done",  today),
            (6,  2, "결제 실패 에러 코드별 Slack 알림 구현",      "PG사 응답코드 → 실시간 알림 매핑",            "todo",  today),
            (7,  2, "정산 데이터 추출 쿼리 자동화",               "매일 오전 9시 자동 실행 스케줄링",            "todo",  today),
            # 박민준
            (8,  3, "GitHub Actions 스테이징 배포 파이프라인 완성","PR 머지 시 자동 배포 트리거",                "done",  today),
            (9,  3, "Docker 멀티스테이지 빌드로 이미지 최적화",   "빌드 시간 40% 단축 목표",                    "todo",  today),
            (10, 3, "매일 오전 스탠드업 참석",                    "9시 팀 스크럼",                               "done",  today),
            # 최서연
            (11, 4, "결제 UX 인터뷰 2건 진행",                   "사용자 페인포인트 인터뷰 (오늘 목표 2건)",    "todo",  today),
            (12, 4, "인터뷰 결과 인사이트 문서 작성",             "어제 인터뷰 3건 정리 완료",                   "done",  today),
            (13, 4, "간편결제 UX 개선안 프로토타입 Figma 작성",   "인터뷰 인사이트 기반 와이어프레임",           "todo",  today),
        ],
    )

    # ── AI Analysis ────────────────────────────────────────────────────────
    await db.executemany(
        "INSERT OR IGNORE INTO todo_analysis (todo_id, premise_id, relation, confidence, reason) VALUES (?,?,?,?,?)",
        [
            (1,  6, "small", 0.94, "Slack 봇 메시지 템플릿은 '매일 답장 자동화하기' 소전제의 핵심 작업"),
            (2,  1, "grand", 0.88, "기여도 분석 문서는 '반복 업무 자동화하기' 대전제 진행 현황 파악에 기여"),
            (3,  8, "small", 0.95, "결제 오류 알림 설정은 '결제 오류 실시간 알림 만들기' 소전제와 직결"),
            (4,  2, "grand", 0.80, "온보딩 자동화는 '팀 커뮤니케이션 효율화하기' 대전제 기여"),
            (5,  5, "small", 0.97, "DML 배치 스크립트는 'DML 처리 자동화하기' 소전제 그 자체"),
            (6,  8, "small", 0.92, "결제 실패 알림 구현은 '결제 오류 실시간 알림 만들기' 소전제 직결"),
            (7,  5, "small", 0.86, "정산 쿼리 자동화는 'DML 처리 자동화하기' 소전제 기여"),
            (8,  7, "small", 0.96, "GitHub Actions 파이프라인은 '배포 파이프라인 구축하기' 소전제 핵심"),
            (9,  7, "small", 0.83, "Docker 최적화는 배포 효율화 소전제 기여"),
            (10, None, "none", 0.12, "스탠드업 미팅 — 직접적 목표 기여 낮음"),
            (11, 9, "small", 0.93, "UX 인터뷰 진행은 '결제 UX 인터뷰 5건 완료하기' 소전제 직결"),
            (12, 9, "small", 0.91, "인터뷰 결과 정리는 UX 인터뷰 소전제 기여"),
            (13, 4, "grand", 0.87, "UX 프로토타입은 '사용자 경험 개선하기' 대전제 기여"),
        ],
    )

    # ── AI Decisions seed (빈 테이블일 때만 삽입) ─────────────────────────
    _cnt = (await (await db.execute("SELECT COUNT(*) FROM ai_decisions")).fetchone())[0]
    if _cnt == 0:
        await db.executemany(
        """INSERT OR IGNORE INTO ai_decisions
           (id, decision_type, input_summary, ai_output, reasoning, confidence,
            ref_todo_id, ref_premise_id, status)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            (1, 'todo_match',
             'Slack 일일 리포트 봇 메시지 템플릿 작성',
             '목표: 매일 답장 자동화하기 (신뢰도 94%)',
             "'Slack', '봇', '메시지 템플릿' 키워드가 '매일 답장 자동화하기' 목표와 94% 유사도. 이니셔티브 '팀 커뮤니케이션 효율화하기' 연결.",
             0.94, 1, 6, 'approved'),
            (2, 'todo_match',
             'DML 배치 스크립트 작성 (고객 등급 업데이트)',
             '목표: DML 처리 자동화하기 (신뢰도 97%)',
             "'DML', '배치', '스크립트', 'DB 작업' 키워드 조합으로 'DML 처리 자동화하기' 목표와 97% 매칭.",
             0.97, 5, 5, 'approved'),
            (3, 'todo_match',
             '매일 오전 스탠드업 참석',
             '목표 연결 없음 (신뢰도 12%)',
             "반복 일정성 활동으로 판단. '스탠드업', '참석' 키워드가 어떤 목표와도 직접 매칭되지 않음. 생산성 기여 낮음으로 분류.",
             0.12, 10, None, 'flagged'),
            (4, 'todo_match',
             '신규 팀원 온보딩 체크리스트 자동화',
             '이니셔티브: 팀 커뮤니케이션 효율화하기 (신뢰도 80%)',
             "'온보딩', '체크리스트', 'Notion 템플릿' 키워드로 커뮤니케이션 효율화 이니셔티브에 매칭. 단, 특정 목표 없음.",
             0.80, 4, 2, 'pending'),
            (5, 'priority_score',
             '결제 오류 알림 Slack 채널 설정',
             '우선순위: HIGH (긴급도 0.88)',
             "'결제', '오류', '알림' 키워드 조합으로 비즈니스 임팩트 HIGH 판정. 실시간 고객 영향 가능성 감지.",
             0.88, 3, 8, 'pending'),
            (6, 'todo_match',
             '인터뷰 결과 인사이트 문서 작성',
             '목표: 결제 UX 인터뷰 5건 완료하기 (신뢰도 91%)',
             "'인터뷰', '인사이트', '문서' 키워드로 UX 인터뷰 목표에 연결. 단, 직접 인터뷰가 아닌 문서화 작업임.",
             0.91, 12, 9, 'pending'),
            (7, 'team_assign',
             'GitHub Actions 스테이징 배포 파이프라인 완성',
             '담당팀: 결제 플랫폼 팀 (신뢰도 96%)',
             "'GitHub Actions', 'CI/CD', '배포' 키워드로 개발팀 작업으로 분류. 반복업무 자동화 이니셔티브의 핵심.",
             0.96, 8, 7, 'approved'),
            (8, 'anomaly',
             'Docker 멀티스테이지 빌드로 이미지 최적화',
             '⚠️ 목표 연결 불확실 (신뢰도 83% / 유사 목표 2개 감지)',
             "'Docker', '이미지 최적화'가 '배포 파이프라인 구축하기'와 83% 매칭. 단, '반복업무 자동화'와도 78% 유사. 중복 가능성 있음.",
             0.83, 9, 7, 'pending'),
        ]
        )

    await db.commit()

