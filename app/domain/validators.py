"""Pure domain validation rules for IoT data points.

These functions contain ONLY business logic -- no database, no framework.
They raise ``app.core.exceptions.ValidationError`` on failure.
"""

from __future__ import annotations

import time

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger("domain.validators")

METRIC_1_MIN, METRIC_1_MAX = 0.0, 100.0
METRIC_2_MIN, METRIC_2_MAX = 0.0, 200.0

MAX_CLOCK_DRIFT_SECONDS = 5.0


def validate_metric_1(value: float) -> None:
    if not (METRIC_1_MIN <= value <= METRIC_1_MAX):
        raise ValidationError(
            f"metric_1 must be between {METRIC_1_MIN} and {METRIC_1_MAX}, got {value}"
        )


def validate_metric_2(value: float) -> None:
    if not (METRIC_2_MIN <= value <= METRIC_2_MAX):
        raise ValidationError(
            f"metric_2 must be between {METRIC_2_MIN} and {METRIC_2_MAX}, got {value}"
        )


def validate_timestamp_not_future(ts: float) -> None:
    now = time.time()
    if ts > now + MAX_CLOCK_DRIFT_SECONDS:
        raise ValidationError(
            f"Timestamp {ts} is in the future (server time: {now:.0f})"
        )


def validate_iot_data_point(
    metric_1: float,
    metric_2: float,
    timestamp: float,
) -> None:
    """Run all domain-level checks for a single IoT data point.

    Collects every violation so the caller receives a complete error
    report in a single round trip rather than one-at-a-time.
    """
    errors: list[str] = []

    try:
        validate_metric_1(metric_1)
    except ValidationError as exc:
        errors.append(exc.message)

    try:
        validate_metric_2(metric_2)
    except ValidationError as exc:
        errors.append(exc.message)

    try:
        validate_timestamp_not_future(timestamp)
    except ValidationError as exc:
        errors.append(exc.message)

    if errors:
        logger.warning("Validation failed (%d issue(s)): %s", len(errors), errors)
        raise ValidationError("IoT data validation failed", details=errors)
