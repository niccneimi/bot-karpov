import asyncpg
from typing import Union
import json
from typing import Dict, List, Union
from datetime import datetime
import logging

def parse_json_str(value: Union[str, list]) -> list:
    return json.loads(value) if isinstance(value, str) else value

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
            package_size INTEGER,
            promocode_used BOOLEAN,
            expiration_date INTEGER,
            extra JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS servers (
            id SERIAL PRIMARY KEY,
            host VARCHAR(255) UNIQUE,
            port INTEGER DEFAULT 22,
            username VARCHAR(255),
            password VARCHAR(255),
            location VARCHAR(255),
            public_key VARCHAR(255),
            private_key VARCHAR(255),
            clients_on_server INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created INTEGER DEFAULT 0
        );
                        
        CREATE TABLE IF NOT EXISTS clients_as_keys (
            id SERIAL PRIMARY KEY,
            telegram_id VARCHAR(255),
            host VARCHAR(255),
            uuid VARCHAR(255),
            email VARCHAR(255),
            public_key VARCHAR(255),
            online_count INTEGER DEFAULT 0,
            online_ips VARCHAR(255),
            expiration_date INTEGER,
            deleted INTEGER DEFAULT 0,
            notified_2_days BOOLEAN DEFAULT FALSE,
            notified_1_day BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );  

        CREATE TABLE IF NOT EXISTS used_promocodes (
            id SERIAL PRIMARY KEY,
            telegram_id TEXT,
            promocode TEXT,
            used_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(telegram_id, promocode)
        );

        CREATE TABLE IF NOT EXISTS tarifs (
            id SERIAL PRIMARY KEY,
            price INTEGER,
            days INTEGER
        );

        CREATE TABLE IF NOT EXISTS admin_promocodes (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE,
            days INTEGER,
            creator_id BIGINT,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE,
            added_at TIMESTAMP DEFAULT NOW()
        );
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql)

    async def get_tarifs(self):
        sql = "SELECT * FROM tarifs ORDER BY days ASC"
        async with self._pool.acquire() as conn:
            records = await conn.fetch(sql)
            return [dict(record) for record in records]


    async def change_free_trial(self, user_id: int) -> None:
        sql = "UPDATE users SET free_trial_used = 1 WHERE user_id = $1"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, user_id)

    async def add_user(self, user_id: int, name: str) -> None:
        sql = "INSERT INTO users (user_id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, user_id, name)

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
    
    async def create_order(self, user_id: int, paid: bool, extra: dict, currency: str, amount, package_size, promocode_used, expiration_date):
        sql = """INSERT INTO orders (user_id, paid, extra, currency, amount, package_size, promocode_used, expiration_date) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"""
        async with self._pool.acquire() as conn:
            await conn.execute(sql, user_id, paid, json.dumps(extra), currency, amount, package_size, promocode_used, expiration_date)

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
    
    async def update_clients_on_server(self, host, value):
        sql = """
        UPDATE servers SET clients_on_server = clients_on_server + $1 WHERE host = $2
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, value, host)  
        if value < 0:
            sql = """UPDATE clients_as_keys SET deleted = 1 WHERE host = $1 AND expiration_date < EXTRACT(EPOCH FROM NOW())::bigint"""
            async with self._pool.acquire() as conn:
                await conn.execute(sql, host)  

    async def transfer_clients_change_clients_on_server(self, host, value):
        sql = """
        UPDATE servers SET clients_on_server = clients_on_server + $1 WHERE host = $2
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, value, host)

    async def add_crypto_address(self, user_id: int, token: str, standart: str, result: str, address_type: str):
        sql = """
        INSERT INTO crypto_addresses (user_id, token, standart, result, address_type)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, user_id, token, standart, result, address_type)

    async def update_crypto_address(self, user_id: int, address: str, token: str):
        sql = """
        UPDATE crypto_addresses 
        SET address = $1, result = 'success'
        WHERE user_id = $2 AND token = $3
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, address, user_id, token)

    async def get_all_client_keys(self, telegram_id):
        sql = '''
        SELECT 
            uuid,
            json_agg(
                json_build_object(
                    'id', id,
                    'telegram_id', telegram_id,
                    'host', host,
                    'email', email,
                    'public_key', public_key,
                    'created_at', created_at
                )
            ) AS records
        FROM clients_as_keys
        WHERE telegram_id = $1 AND expiration_date > EXTRACT(EPOCH FROM NOW())::bigint
        GROUP BY uuid;
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, telegram_id)
        return {
            str(row['uuid']): parse_json_str(row['records']) 
            for row in rows
        }

    async def add_server_to_creating(self, host, port, username, password, location):
        async with self._pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO servers (host, port, username, password, location)
                VALUES ($1, $2, $3, $4, $5)
            ''', host, port, username, password, location)

    async def final_add_server(self, host, public_key, private_key):
        async with self._pool.acquire() as conn:
            await conn.execute('''
                UPDATE servers 
                SET public_key = $1, 
                    private_key = $2, 
                    created = 1 
                WHERE host = $3
            ''', public_key, private_key, host)

    async def get_all_servers(self):
        async with self._pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM servers WHERE created = 1')
        
    async def server_exists(self, host: int) -> bool:
        sql = "SELECT EXISTS(SELECT 1 FROM servers WHERE host = $1)"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, host)

    async def get_servers_with_uniqe_locations(self):
        sql = """
        SELECT *
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY location ORDER BY clients_on_server ASC, id) as rn
            FROM servers WHERE created = 1
        ) t
        WHERE t.rn = 1
        """
        async with self._pool.acquire() as conn:
            return await conn.fetch(sql)
        
    async def add_clientkey(self, telegram_id, host, uuid, email, public_key, expiration_date):
        async with self._pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO clients_as_keys (telegram_id, host, uuid, email, public_key, expiration_date)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', telegram_id, host, uuid, email, public_key, expiration_date)
    
    async def get_clientkeys_by_uuid(self, uuid):
        async with self._pool.acquire() as conn:
            return await conn.fetch('SELECT * FROM clients_as_keys WHERE uuid = $1 AND expiration_date > EXTRACT(EPOCH FROM NOW())::bigint', uuid)

    async def get_all_host_keys(self, host):
        sql = '''
        SELECT 
            uuid,
            json_agg(
                json_build_object(
                    'id', id,
                    'telegram_id', telegram_id,
                    'host', host,
                    'email', email,
                    'public_key', public_key,
                    'created_at', created_at
                )
            ) AS records
        FROM clients_as_keys
        WHERE host = $1 AND expiration_date > EXTRACT(EPOCH FROM NOW())::bigint AND deleted = 0
        GROUP BY uuid;
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, host)
        return {
            str(row['uuid']): parse_json_str(row['records']) 
            for row in rows
        }
        
    async def update_online_datas(self, ips, host, uuid):
        online_count = len(ips)
        ips_string = ':'.join(ips)
        sql = """UPDATE clients_as_keys SET online_count = $1, online_ips = $2 WHERE host = $3 AND uuid = $4"""
        async with self._pool.acquire() as conn:
            await conn.execute(sql, online_count, ips_string, host, uuid)
        
    async def get_private_key_by_host(self, host):
        sql = """SELECT private_key FROM servers WHERE host = $1"""
        async with self._pool.acquire() as conn:
            return await conn.fetch(sql, host)
        
    async def get_keys_by_host_including_expired(self, host):
        sql = '''
        SELECT 
            uuid,
            json_agg(
                json_build_object(
                    'id', id,
                    'telegram_id', telegram_id,
                    'host', host,
                    'email', email,
                    'public_key', public_key,
                    'created_at', created_at
                )
            ) AS records
        FROM clients_as_keys
        WHERE host = $1 AND deleted = 0
        GROUP BY uuid;
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, host)
        return {
            str(row['uuid']): parse_json_str(row['records']) 
            for row in rows
        }
    
    async def get_key_days_left(self, uuid):
        sql = "SELECT expiration_date FROM clients_as_keys WHERE uuid = $1"
        async with self._pool.acquire() as conn:
            expiration_date = await conn.fetch(sql, uuid)
        return (datetime.fromtimestamp(expiration_date[0]['expiration_date']) - datetime.now()).days
        
    async def prodlit_expiration_date(self, uuid, days):
        sql = "UPDATE clients_as_keys SET expiration_date = expiration_date + $1 WHERE uuid = $2"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, days, uuid)
            return await conn.fetch("SELECT expiration_date FROM clients_as_keys WHERE uuid = $1", uuid)

    async def get_all_keys_with_expiration(self):
        sql = "SELECT DISTINCT uuid, telegram_id, expiration_date, notified_2_days, notified_1_day FROM clients_as_keys WHERE deleted = 0"
        async with self._pool.acquire() as conn:
            return await conn.fetch(sql)  
        
    async def mark_key_notified(self, uuid, day_notified):
        allowed_columns = {"notified_2_days", "notified_1_day"}
        if day_notified not in allowed_columns:
            raise ValueError(f"Invalid column name: {day_notified}")
        sql = f"UPDATE clients_as_keys SET {day_notified} = TRUE WHERE uuid = $1"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, uuid)

    async def unmark_key_notified(self, uuid):
        sql = f"UPDATE clients_as_keys SET notified_2_days = FALSE, notified_1_day = FALSE WHERE uuid = $1"
        async with self._pool.acquire() as conn:
            await conn.execute(sql, uuid)

    async def is_used_promocode_by_telegram_id(self, telegram_id, promocode):
        """Проверяет, использовал ли пользователь промокод"""
        try:
            query = "SELECT * FROM used_promocodes WHERE telegram_id = $1 AND promocode = $2"
            async with self._pool.acquire() as conn:
                result = await conn.fetchrow(query, telegram_id, promocode)
                return result is not None
        except Exception as e:
            logging.error(f"Error checking if promocode {promocode} was used by {telegram_id}: {str(e)}")
            return True

    async def add_promocode_used_by_telegram_id(self, telegram_id, promocode):
        """Добавляет запись об использовании промокода пользователем"""
        try:
            query = "INSERT INTO used_promocodes (telegram_id, promocode) VALUES ($1, $2) ON CONFLICT DO NOTHING"
            async with self._pool.acquire() as conn:
                await conn.execute(query, telegram_id, promocode)
            return True
        except Exception as e:
            logging.error(f"Error adding used promocode {promocode} for {telegram_id}: {str(e)}")
            return False

    async def clear_uncreated_servers(self):
        sql = "DELETE FROM servers WHERE created = 0"
        async with self._pool.acquire() as conn:
            await conn.execute(sql)

    async def is_admin(self, user_id: int) -> bool:
        sql = "SELECT EXISTS(SELECT 1 FROM admin_users WHERE user_id = $1)"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, user_id)
    
    async def create_admin_promocode(self, code: str, days: int, admin_id: int) -> bool:
        sql = """
        INSERT INTO admin_promocodes (code, days, creator_id) 
        VALUES ($1, $2, $3)
        ON CONFLICT (code) DO NOTHING
        RETURNING id
        """
        async with self._pool.acquire() as conn:
            try:
                result = await conn.fetchval(sql, code, days, admin_id)
                return bool(result)
            except Exception:
                return False
    
    async def get_admin_promocode(self, code: str):
        sql = """
        SELECT * FROM admin_promocodes 
        WHERE code = $1 AND used = FALSE
        """
        async with self._pool.acquire() as conn:
            record = await conn.fetchrow(sql, code)
            return dict(record) if record else None
    
    async def mark_admin_promocode_used(self, code: str):
        sql = """
        UPDATE admin_promocodes 
        SET used = TRUE 
        WHERE code = $1
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, code)
    
    async def is_admin_promocode_used(self, code: str) -> bool:
        sql = "SELECT used FROM admin_promocodes WHERE code = $1"
        async with self._pool.acquire() as conn:
            return await conn.fetchval(sql, code) or False
    
    async def add_admin_user(self, user_id: int) -> bool:
        sql = """
        INSERT INTO admin_users (user_id)
        VALUES ($1)
        ON CONFLICT (user_id) DO NOTHING
        RETURNING id
        """
        async with self._pool.acquire() as conn:
            try:
                result = await conn.fetchval(sql, user_id)
                return bool(result)
            except Exception:
                return False