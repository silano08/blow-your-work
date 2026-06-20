import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "tasks.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,
                detail    TEXT,
                priority  TEXT DEFAULT 'medium',
                status    TEXT DEFAULT 'pending',
                parent_id INTEGER REFERENCES tasks(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
