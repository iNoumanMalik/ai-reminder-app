"""Parse repeat rules and compute the next scheduled fire time."""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional

# Canonical values stored in DB and sent by the app.
SUPPORTED_REPEAT_RULES = frozenset({"daily", "weekly", "weekdays", "monthly"})

_REPEAT_ALIASES: dict[str, str] = {
    "daily": "daily",
    "every day": "daily",
    "everyday": "daily",
    "each day": "daily",
    "weekly": "weekly",
    "every week": "weekly",
    "each week": "weekly",
    "weekdays": "weekdays",
    "weekday": "weekdays",
    "every weekday": "weekdays",
    "monday to friday": "weekdays",
    "mon-fri": "weekdays",
    "monthly": "monthly",
    "every month": "monthly",
    "each month": "monthly",
}


def normalize_repeat(value: Optional[str]) -> Optional[str]:
    """Return a supported repeat rule or None."""
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if cleaned in SUPPORTED_REPEAT_RULES:
        return cleaned
    if cleaned in _REPEAT_ALIASES:
        return _REPEAT_ALIASES[cleaned]
    return None


def repeat_label(value: Optional[str]) -> Optional[str]:
    """Human-readable label for UI."""
    rule = normalize_repeat(value)
    if rule is None:
        return None
    return {
        "daily": "Repeats daily",
        "weekly": "Repeats weekly",
        "weekdays": "Repeats on weekdays",
        "monthly": "Repeats monthly",
    }.get(rule)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def next_occurrence_after(
    rule: Optional[str],
    current_scheduled: datetime,
    *,
    after: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Next fire time strictly after `after` (default: current_scheduled),
    preserving hour/minute from current_scheduled.
    """
    canonical = normalize_repeat(rule)
    if canonical is None:
        return None

    base = _as_utc(current_scheduled)
    pivot = _as_utc(after or current_scheduled)

    hour, minute = base.hour, base.minute
    second, micro = base.second, base.microsecond

    def at(day: datetime) -> datetime:
        return day.replace(
            hour=hour,
            minute=minute,
            second=second,
            microsecond=micro,
            tzinfo=timezone.utc,
        )

    cursor = at(pivot)

    if canonical == "daily":
        while cursor <= pivot:
            cursor = at(cursor + timedelta(days=1))
        return cursor

    if canonical == "weekdays":
        while cursor <= pivot or cursor.weekday() >= 5:
            cursor = at(cursor + timedelta(days=1))
        return cursor

    if canonical == "weekly":
        while cursor <= pivot:
            cursor = at(cursor + timedelta(days=7))
        return cursor

    if canonical == "monthly":
        year, month = base.year, base.month
        for _ in range(36):
            last_day = calendar.monthrange(year, month)[1]
            day = min(base.day, last_day)
            candidate = datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
                micro,
                tzinfo=timezone.utc,
            )
            if candidate > pivot:
                return candidate
            month += 1
            if month > 12:
                month = 1
                year += 1
        return None

    return None


def validate_repeat_field(value: Optional[str]) -> Optional[str]:
    """For API: normalize or raise ValueError with helpful message."""
    if value is None:
        return None
    if not str(value).strip():
        return None
    normalized = normalize_repeat(value)
    if normalized is None:
        raise ValueError(
            "Repeat must be one of: daily, weekly, weekdays, monthly "
            "(or leave empty for a one-time reminder)"
        )
    return normalized
