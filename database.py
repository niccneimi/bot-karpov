import asyncpg
from typing import Union

class Database:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._pool: Union[asyncpg.Pool, None] = None

    async def create_pool(self):
        self._pool = await asyncpg.create_pool(self.dsn)
        await self.create_tables()

    async def close_pool(self):
        if self._pool:
            await self._pool.close()

    async def create_tables(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            name VARCHAR(255),
            lang VARCHAR(100) DEFAULT 'Русский',
            free_trial_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql)

    async def add_user(self, user_id: int) -> None:
        sql = "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, user_id)

    async def user_exists(self, user_id: int) -> bool:
        sql = "SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1)"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, user_id)

    async def get_name(self, user_id: int):
        sql = "SELECT name FROM users WHERE user_id = $1"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, user_id)
        
    async def get_lang(self, user_id: int):
        sql = "SELECT lang FROM users WHERE user_id = $1"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, user_id)
        
    async def change_lang(self, user_id: int, language_to_change: str):
        sql = "UPDATE users SET lang = $1 WHERE user_id = $2"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, language_to_change, user_id)
        
    async def is_free_trial_used(self, user_id: int):
        sql = "SELECT free_trial_used FROM users WHERE user_id = $1"
        async with self._pool.acquire() as conn:
            return bool(await conn.fetchval(sql, user_id))