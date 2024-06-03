import aiosqlite
import os


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._connection = None

    # Эта хуйня заменяет async with aiosqlite.connect(БАЗА_ДАННЫХ) // Вызывается в самом начале всех функций класса
    async def __aenter__(self):
        await self.connect()
        return self

    # Эта хуйня типо clean-up, закрывает коннекшены с БД, вызывается в конце каждой функции
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def connect(self):
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
        return self._connection

    async def close(self):
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def db_start(self):
        db = await self.connect()
        try:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS accounts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    locale TEXT,
                    grum_balance REAL DEFAULT 0.00000000,
                    inviter_id INTEGER,
                    ref_amount INTEGER DEFAULT 0
                );
            ''')
            await db.commit()
        except Exception as e:
            print(f"An error occurred: {e}")

    async def get_or_create_user(self, user_id, inviter_id=None):
        db = await self.connect()
        try:
            if not await self.exists('user_id', user_id):
                await db.execute('INSERT INTO accounts (user_id) VALUES (?)', (user_id,))

                if inviter_id:
                    await db.execute('UPDATE accounts SET inviter_id = ? WHERE user_id = ?',
                                     (inviter_id, user_id))
                    await db.execute('UPDATE accounts SET ref_amount = ref_amount + 1 WHERE user_id = ?',
                                     (inviter_id, ))
                    await db.execute('UPDATE accounts SET grum_balance = grum_balance + 50.00000000 WHERE user_id = ?',
                                     (inviter_id,))

                await db.commit()
        except Exception as e:
            print(f"An error occurred: {e}")

    async def exists(self, column: str, value: any, table='accounts'):
        db = await self.connect()
        try:
            async with db.execute(f'SELECT * FROM {table} WHERE {column} == ?', (value,)) as cursor:
                result = await cursor.fetchone()
                return result is not None
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    async def update_language(self, user_id, locale):
        db = await self.connect()
        try:
            await db.execute('UPDATE accounts SET locale = ? WHERE user_id = ?', (locale, user_id))
            await db.commit()
            print(locale, user_id)
        except Exception as e:
            print(f"An error occurred: {e}")

    async def get_data(self, data: str,  value: int, column='user_id', table='accounts'):
        db = await self.connect()
        try:
            async with db.execute(f'SELECT {data} FROM {table} WHERE {column} == ?', (value,)) as cursor:
                result = await cursor.fetchone()
                return result
        except Exception as e:
            print(f"An error occurred: {e}")

    async def update_grum_balance(self, user_id):
        db = await self.connect()
        try:
            await db.execute('UPDATE accounts SET grum_balance = grum_balance + 50.00000000 WHERE user_id = ?',
                             (user_id,))
            await db.commit()
        except Exception as e:
            print(f"An error occurred: {e}")


path = os.path.abspath('database/tg.db')
db = Database(path)
