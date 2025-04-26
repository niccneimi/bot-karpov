import asyncpg
from typing import Union
import json

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

        CREATE TABLE IF NOT EXISTS crypto_addresses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            address VARCHAR(255),
            token VARCHAR(10),
            standart VARCHAR(10) DEFAULT 'BEP20',
            result VARCHAR(20) DEFAULT 'pending',
            address_type VARCHAR(20) DEFAULT 'default',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS crypto_transactions (
            id SERIAL PRIMARY KEY,
            txid VARCHAR(255),
            transaction_type VARCHAR(12) DEFAULT 'IN',
            confirmations INTEGER DEFAULT 0,
            token VARCHAR(10),
            amount DECIMAL(20, 8),
            from_address VARCHAR(42),
            standart VARCHAR(10) DEFAULT 'BEP20',
            user_crypto_address_id INTEGER REFERENCES crypto_addresses(id),
            address VARCHAR(42),
            paid BOOLEAN DEFAULT FALSE,
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(txid, address)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            amount DECIMAL(20, 8) NOT NULL,
            currency VARCHAR(10) NOT NULL,
            paid BOOLEAN DEFAULT FALSE,
            extra JSONB,
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

    async def get_address_by_user_and_token(self, user_id: int, token: str):
        sql = """
        SELECT id, address 
        FROM crypto_addresses 
        WHERE user_id = $1 AND token = $2 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, user_id, token)
            return {'id': row['id'], 'address': row['address']} if row else None

    async def get_transaction_by_txid_and_address(self, txid: str, address: str):
        sql = """
        SELECT * 
        FROM crypto_transactions 
        WHERE txid = $1 AND address = $2
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(sql, txid, address)

    async def add_transaction(self, txid: str, transaction_type: str, confirmations: int,
                            token: str, amount: str, from_address: str, standart: str,
                            user_crypto_address_id: int, address: str, paid: bool, status: str):
        sql = """
        INSERT INTO crypto_transactions 
        (txid, transaction_type, confirmations, token, amount, from_address, 
         standart, user_crypto_address_id, address, paid, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, txid, transaction_type, confirmations, token,
                             amount, from_address, standart, user_crypto_address_id,
                             address, paid, status)

    async def update_order_status(self, user_id: int, paid: bool, extra: dict):
        sql = """
        UPDATE orders 
        SET paid = $1, extra = $2 
        WHERE id = (
            SELECT id 
            FROM orders 
            WHERE user_id = $3 AND paid = false 
            ORDER BY created_at DESC 
            LIMIT 1
        )
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, paid, json.dumps(extra), user_id)

    async def add_crypto_address(self, user_id: int, token: str, standart: str, result: str, address_type: str):
        """Добавляет новый крипто-адрес для пользователя"""
        sql = """
        INSERT INTO crypto_addresses (user_id, token, standart, result, address_type)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, user_id, token, standart, result, address_type)

    async def update_crypto_address(self, user_id: int, address: str, token: str):
        """Обновляет адрес для пользователя и токена"""
        sql = """
        UPDATE crypto_addresses 
        SET address = $1, result = 'success'
        WHERE user_id = $2 AND token = $3
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, address, user_id, token)