# src/observability/prometheus_setup.py
import logging
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

logger = logging.getLogger(__name__)

def setup_prometheus(app: FastAPI):
    logger.info("Setting up Prometheus instrumentation...")
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        inprogress_name="inprogress_requests",
        inprogress_labels=True,
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics exposed at /metrics")
