"""FastAPI entrypoint for compliance monitoring backend."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.routes import router
from core.config import ALLOWED_ORIGINS, LOG_FORMAT, LOG_LEVEL
from services.registry import ServiceRegistry

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    registry = ServiceRegistry.get_instance()
    task = asyncio.create_task(registry.monitor.run_forever())
    logger.info("Compliance monitoring background loop started")

    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        logger.info("Compliance monitoring background loop stopped")


app = FastAPI(title="Compliance Monitoring API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok", "service": "compliance-monitoring"}
