# src/observability/langsmith_setup.py
import os
import logging
from configs.settings import settings

logger = logging.getLogger(__name__)

def setup_langsmith():
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        logger.info(f"LangSmith tracing enabled for project: {settings.LANGSMITH_PROJECT}")
    else:
        logger.warning("LangSmith API key not found. Tracing disabled.")
