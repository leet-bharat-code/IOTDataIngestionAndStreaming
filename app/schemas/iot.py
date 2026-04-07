from __future__ import annotations

from pydantic import BaseModel, Field


class IoTDataPoint(BaseModel):
    """Structural schema only -- business-rule validation (ranges, future
    timestamp) lives in ``domain.validators`` so that all violations are
    reported in a single pass with our standardized error format."""

    user_id: str = Field(..., min_length=1, examples=["U1001"])
    metric_1: float
    metric_2: float
    metric_3: float
    timestamp: float = Field(..., description="Unix epoch seconds")


class IoTDataResponse(BaseModel):
    user_id: str
    metric_1: float
    metric_2: float
    metric_3: float
    timestamp: float
    ingested_at: str | None = None


class IoTIngestResult(BaseModel):
    status: str = "accepted"
    user_id: str
    timestamp: float
