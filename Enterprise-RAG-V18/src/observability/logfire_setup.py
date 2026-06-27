# src/observability/logfire_setup.py
import logging
import logfire
from fastapi import FastAPI
from configs.settings import settings

logger = logging.getLogger(__name__)

def setup_logfire(app: FastAPI):
    if settings.LOGFIRE_TOKEN:
        logfire.configure(token=settings.LOGFIRE_TOKEN)
        logfire.instrument_fastapi(app)
        # Instrument standard logging
        logging.basicConfig(handlers=[logfire.LogfireLoggingHandler()], level=logging.INFO)
        logger.info("Logfire instrumentation enabled.")
    else:
        logger.warning("Logfire token not found. Structured logging disabled.")
