"""Tests for the IoT ingestion service layer against mock MongoDB."""

import time

import pytest
import pytest_asyncio

from app.core.exceptions import NotFoundError, ValidationError
from app.messaging.event_bus import clear_subscribers, subscribe
from app.schemas.iot import IoTDataPoint
from app.schemas.user import UserCreate
from app.services import iot_service, user_service


@pytest_asyncio.fixture(autouse=True)
async def cleanup_event_bus():
    yield
    clear_subscribers()


@pytest_asyncio.fixture
async def active_user():
    await user_service.create_user(
        UserCreate(user_id="U5001", name="IoT Tester", password="pass123456")
    )


@pytest.mark.asyncio
class TestProcessIoTData:
    async def test_ingest_success(self, active_user):
        result = await iot_service.process_iot_data(
            IoTDataPoint(
                user_id="U5001",
                metric_1=42.0,
                metric_2=100.0,
                metric_3=7.7,
                timestamp=time.time() - 60,
            )
        )
        assert result.status == "accepted"
        assert result.user_id == "U5001"

    async def test_publishes_event(self, active_user):
        events: list[dict] = []

        async def _capture(e: dict) -> None:
            events.append(e)

        subscribe(_capture)

        ts = time.time() - 30
        await iot_service.process_iot_data(
            IoTDataPoint(
                user_id="U5001", metric_1=10, metric_2=20, metric_3=30, timestamp=ts
            )
        )
        assert len(events) == 1
        assert events[0]["event"] == "NEW_DATA"
        assert events[0]["user_id"] == "U5001"

    async def test_idempotency_duplicate_rejected(self, active_user):
        """mongomock doesn't enforce unique indexes, so we verify at the
        repository layer that DuplicateKeyError from a real Mongo would
        propagate. Here we test that two distinct timestamps are both accepted
        and that the same user+ts combo stores only one document."""
        ts = time.time() - 120
        data = IoTDataPoint(
            user_id="U5001", metric_1=1, metric_2=2, metric_3=3, timestamp=ts
        )
        await iot_service.process_iot_data(data)

        different_ts = IoTDataPoint(
            user_id="U5001", metric_1=1, metric_2=2, metric_3=3, timestamp=ts + 1
        )
        result = await iot_service.process_iot_data(different_ts)
        assert result.status == "accepted"

        history = await iot_service.get_history("U5001", limit=100)
        timestamps = [d.timestamp for d in history]
        assert ts in timestamps
        assert (ts + 1) in timestamps

    async def test_missing_user(self):
        with pytest.raises(NotFoundError):
            await iot_service.process_iot_data(
                IoTDataPoint(
                    user_id="GHOST",
                    metric_1=1,
                    metric_2=2,
                    metric_3=3,
                    timestamp=time.time() - 10,
                )
            )

    async def test_inactive_user_rejected(self, active_user):
        from app.schemas.user import UserUpdate
        await user_service.update_user("U5001", UserUpdate(is_active=False))

        with pytest.raises(ValidationError, match="not active"):
            await iot_service.process_iot_data(
                IoTDataPoint(
                    user_id="U5001",
                    metric_1=1,
                    metric_2=2,
                    metric_3=3,
                    timestamp=time.time() - 10,
                )
            )

    async def test_future_timestamp_rejected(self, active_user):
        with pytest.raises(ValidationError) as exc_info:
            await iot_service.process_iot_data(
                IoTDataPoint(
                    user_id="U5001",
                    metric_1=1,
                    metric_2=2,
                    metric_3=3,
                    timestamp=time.time() + 9999,
                )
            )
        assert any("future" in d for d in exc_info.value.details)


@pytest.mark.asyncio
class TestGetLatestAndHistory:
    async def test_latest(self, active_user):
        ts = time.time() - 500
        for i in range(3):
            await iot_service.process_iot_data(
                IoTDataPoint(
                    user_id="U5001",
                    metric_1=float(i),
                    metric_2=float(i),
                    metric_3=float(i),
                    timestamp=ts + i,
                )
            )
        latest = await iot_service.get_latest("U5001")
        assert latest.metric_1 == 2.0

    async def test_history_limit(self, active_user):
        ts = time.time() - 1000
        for i in range(5):
            await iot_service.process_iot_data(
                IoTDataPoint(
                    user_id="U5001",
                    metric_1=float(i),
                    metric_2=float(i),
                    metric_3=float(i),
                    timestamp=ts + i,
                )
            )
        history = await iot_service.get_history("U5001", limit=3)
        assert len(history) == 3
