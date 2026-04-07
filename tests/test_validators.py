"""Tests for pure domain validation logic (no I/O)."""

import time

import pytest

from app.core.exceptions import ValidationError
from app.domain.validators import (
    validate_metric_1,
    validate_metric_2,
    validate_timestamp_not_future,
    validate_iot_data_point,
)


class TestMetric1:
    def test_valid_lower_bound(self):
        validate_metric_1(0.0)

    def test_valid_upper_bound(self):
        validate_metric_1(100.0)

    def test_valid_mid(self):
        validate_metric_1(55.5)

    def test_below_range(self):
        with pytest.raises(ValidationError, match="metric_1"):
            validate_metric_1(-0.1)

    def test_above_range(self):
        with pytest.raises(ValidationError, match="metric_1"):
            validate_metric_1(100.1)


class TestMetric2:
    def test_valid_lower_bound(self):
        validate_metric_2(0.0)

    def test_valid_upper_bound(self):
        validate_metric_2(200.0)

    def test_below_range(self):
        with pytest.raises(ValidationError, match="metric_2"):
            validate_metric_2(-1.0)

    def test_above_range(self):
        with pytest.raises(ValidationError, match="metric_2"):
            validate_metric_2(200.1)


class TestTimestamp:
    def test_past_timestamp(self):
        validate_timestamp_not_future(time.time() - 3600)

    def test_current_timestamp(self):
        validate_timestamp_not_future(time.time())

    def test_future_timestamp(self):
        with pytest.raises(ValidationError, match="future"):
            validate_timestamp_not_future(time.time() + 3600)

    def test_within_drift_tolerance(self):
        validate_timestamp_not_future(time.time() + 3)


class TestComposite:
    def test_all_valid(self):
        validate_iot_data_point(
            metric_1=50.0,
            metric_2=100.0,
            timestamp=time.time() - 10,
        )

    def test_multiple_failures_collected(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_iot_data_point(
                metric_1=999.0,
                metric_2=999.0,
                timestamp=time.time() + 9999,
            )
        assert len(exc_info.value.details) == 3

    def test_partial_failure_reports_only_failing_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_iot_data_point(
                metric_1=50.0,
                metric_2=999.0,
                timestamp=time.time() - 10,
            )
        assert len(exc_info.value.details) == 1
        assert "metric_2" in exc_info.value.details[0]
