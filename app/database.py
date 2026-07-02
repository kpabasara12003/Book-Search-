from collections.abc import AsyncGenerator
import asyncpg
from app.config import settings

class DatabaseManager:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60.0
            )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

db_manager = DatabaseManager()

async def get_raw_db() -> AsyncGenerator[asyncpg.Connection, None]:
    if not db_manager.pool:
        raise RuntimeError("Database pool is not initialized.")
    async with db_manager.pool.acquire() as connection:
        yield connection
