from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserId
from app.schemas.iot import IoTDataPoint, IoTDataResponse, IoTIngestResult
from app.services import iot_service

router = APIRouter(prefix="/iot", tags=["iot"])


@router.post("/data", response_model=IoTIngestResult, status_code=201)
async def ingest_data(
    body: IoTDataPoint,
    _caller: CurrentUserId = ...,
) -> IoTIngestResult:
    return await iot_service.process_iot_data(body)


users_iot_router = APIRouter(prefix="/users", tags=["iot"])


@users_iot_router.get("/{user_id}/iot/latest", response_model=IoTDataResponse)
async def get_latest(
    user_id: str,
    _caller: CurrentUserId = ...,
) -> IoTDataResponse:
    return await iot_service.get_latest(user_id)


@users_iot_router.get("/{user_id}/iot/history", response_model=list[IoTDataResponse])
async def get_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=1000),
    _caller: CurrentUserId = ...,
) -> list[IoTDataResponse]:
    return await iot_service.get_history(user_id, limit=limit)
