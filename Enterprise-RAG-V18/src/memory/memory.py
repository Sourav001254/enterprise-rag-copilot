# src/memory/memory.py
import logging
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from configs.settings import settings
import asyncpg

logger = logging.getLogger(__name__)

class CheckpointManager:
    def __init__(self):
        self.checkpointer = None
        self._pool = None

    async def initialize(self):
        logger.info("Initializing AsyncPostgresSaver for LangGraph memory...")
        conn_string = settings.POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        self._pool = await asyncpg.create_pool(
            dsn=conn_string,
            min_size=1,
            max_size=5
        )
        self.checkpointer = AsyncPostgresSaver(self._pool)
        
        # Setup tables if they don't exist
        logger.info("Setting up checkpointer tables...")
        await self.checkpointer.setup()
        logger.info("Checkpointer initialized.")

    async def close(self):
        if self._pool:
            logger.info("Closing checkpointer pool...")
            await self._pool.close()

    def get_checkpointer(self):
        if not self.checkpointer:
            raise RuntimeError("Checkpointer not initialized. Call initialize() first.")
        return self.checkpointer

checkpoint_manager = CheckpointManager()
