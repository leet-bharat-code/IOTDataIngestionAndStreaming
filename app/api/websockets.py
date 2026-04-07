"""WebSocket endpoints for real-time IoT data ingestion and subscription.

Both endpoints validate JWT at connection time and reject unauthorized clients.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.schemas.iot import IoTDataPoint
from app.services import iot_service
from app.websocket.manager import manager

logger = get_logger("api.ws")
router = APIRouter(tags=["websocket"])


async def _authenticate_ws(ws: WebSocket, token: str | None) -> str | None:
    """Validate JWT and return user_id, or close with 4001 on failure."""
    if not token:
        await ws.close(code=4001, reason="Missing token")
        return None
    try:
        payload = decode_access_token(token)
        return payload["sub"]
    except Exception:
        await ws.close(code=4001, reason="Invalid or expired token")
        return None


def _error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, AppError):
        resp: dict[str, Any] = {"error": exc.code, "message": exc.message}
        if exc.details is not None:
            resp["details"] = exc.details
        return resp
    return {"error": "INTERNAL_ERROR", "message": str(exc)}


@router.websocket("/ws/ingest")
async def ws_ingest(ws: WebSocket, token: str = Query(...)) -> None:
    await ws.accept()
    caller = await _authenticate_ws(ws, token)
    if caller is None:
        return

    logger.info("WS ingest opened: caller=%s", caller)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
                data = IoTDataPoint(**payload)
                result = await iot_service.process_iot_data(data)
                await ws.send_text(
                    json.dumps({"status": "accepted", "user_id": result.user_id, "timestamp": result.timestamp})
                )
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"error": "Invalid JSON"}))
            except Exception as exc:
                logger.warning("WS ingest rejected: caller=%s reason=%s", caller, exc)
                await ws.send_text(json.dumps(_error_payload(exc)))
    except WebSocketDisconnect:
        logger.info("WS ingest closed: caller=%s", caller)


@router.websocket("/ws/subscribe")
async def ws_subscribe(ws: WebSocket, user_id: str = Query(...), token: str = Query(...)) -> None:
    await ws.accept()
    caller = await _authenticate_ws(ws, token)
    if caller is None:
        return

    logger.info("WS subscribe opened: caller=%s target_user=%s", caller, user_id)
    await manager.add_subscription(user_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        logger.info("WS subscribe closed: caller=%s target_user=%s", caller, user_id)
    finally:
        await manager.remove_subscription(user_id, ws)
