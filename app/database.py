import asyncpg

DATABASE_URL = "postgresql://urlshortener:urlshortener@localhost:5433/urlshortener"

pool: asyncpg.Pool | None = None

async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)

    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
        id BIGSERIAL PRIMARY KEY,
        short_code VARCHAR UNIQUE,
        original_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
        )
        """)

        await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_short_code ON urls (short_code)
        """)

async def close_db():
    global pool
    if pool:
        await pool.close()

async def insert_url(original_url: str) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO urls (original_url) VALUES ($1) RETURNING id",
            original_url
        )
        return row["id"]

async def update_short_code(url_id: int, short_code: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE urls SET short_code = $1 WHERE id = $2",
            short_code,
            url_id
        )

async def get_url_by_code(short_code: str) -> str | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT original_url FROM urls WHERE short_code = $1",
            short_code
        )
        return row["original_url"] if row else None