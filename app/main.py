from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.iot import router as iot_router, users_iot_router
from app.api.users import router as users_router
from app.api.websockets import router as ws_router
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.messaging.event_bus import subscribe
from app.repository.database import close_db, init_db
from app.websocket.broadcaster import handle_iot_event

logger = get_logger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await init_db()
    subscribe(handle_iot_event)
    logger.info("Application started")
    yield
    await close_db()
    logger.info("Application stopped")


app = FastAPI(
    title="IoT Data Ingestion & Streaming Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    body: dict[str, Any] = {"error": exc.code, "message": exc.message}
    if exc.details is not None:
        body["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request body validation failed",
            "details": details,
        },
    )


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(iot_router)
app.include_router(users_iot_router)
app.include_router(ws_router)


@app.get("/health", tags=["ops"])
async def health() -> dict:
    return {"status": "ok"}
