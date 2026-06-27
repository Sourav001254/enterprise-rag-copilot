# src/db/postgres.py
import asyncpg
from contextlib import asynccontextmanager
import logging
from configs.settings import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
    async def connect(self):
        try:
            logger.info("Initializing asyncpg connection pool...")
            self.pool = await asyncpg.create_pool(
                dsn=settings.POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://"),
                min_size=settings.POSTGRES_POOL_MIN,
                max_size=settings.POSTGRES_POOL_MAX,
                timeout=30.0,
            )
            
            logger.info("Database pools initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        logger.info("Closing database pools...")
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            await self.connect()
        async with self.pool.acquire() as connection:
            yield connection

db_manager = DatabaseManager()

async def execute_query(query: str, *args):
    """Helper to execute write/update queries quickly."""
    async with db_manager.get_connection() as conn:
        return await conn.execute(query, *args)

async def fetch_rows(query: str, *args):
    """Helper to fetch rows quickly."""
    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, *args)
