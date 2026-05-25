"""Tests for repeat rule parsing and next occurrence."""

from datetime import datetime, timezone

from services.repeat_schedule import (
    next_occurrence_after,
    normalize_repeat,
    repeat_label,
)


def test_normalize_aliases():
    assert normalize_repeat("Every Day") == "daily"
    assert normalize_repeat("Mon-Fri") == "weekdays"
    assert normalize_repeat("bogus") is None


def test_daily_next():
    base = datetime(2026, 5, 25, 8, 0, tzinfo=timezone.utc)
    after = datetime(2026, 5, 25, 9, 0, tzinfo=timezone.utc)
    nxt = next_occurrence_after("daily", base, after=after)
    assert nxt == datetime(2026, 5, 26, 8, 0, tzinfo=timezone.utc)


def test_weekdays_skips_weekend():
    # Saturday 2026-05-23
    base = datetime(2026, 5, 23, 9, 0, tzinfo=timezone.utc)
    nxt = next_occurrence_after("weekdays", base, after=base)
    assert nxt.weekday() == 0  # Monday
    assert nxt.day == 25


def test_repeat_label():
    assert repeat_label("daily") == "Repeats daily"
    assert repeat_label(None) is None
