"""Authoritative server observation time helpers for event / round clocks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    """Wall clock in UTC (local operator tooling only — not for event countdown)."""
    return datetime.now(UTC)


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO-8601 / epoch timestamp into an aware UTC datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, (int, float)):
        # Heuristic: ms vs s
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=UTC)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    return None


def extract_server_observed_at(payload: dict[str, Any] | None) -> datetime | None:
    """
    Prefer explicit server observation fields from an API / snapshot payload.

    Never invent a value: returns None when no authoritative field is present.
    """
    if not payload:
        return None
    for key in (
        "server_time",
        "observed_at",
        "observation_time",
        "as_of",
        "timestamp",
        "now",
    ):
        parsed = parse_timestamp(payload.get(key))
        if parsed is not None:
            return parsed
    # Nested common containers
    for nest_key in ("clock", "time", "status", "round"):
        nested = payload.get(nest_key)
        if isinstance(nested, dict):
            found = extract_server_observed_at(nested)
            if found is not None:
                return found
    return None


def extract_deadline(payload: dict[str, Any] | None) -> datetime | None:
    """Extract a round / submission deadline timestamp if present."""
    if not payload:
        return None
    for key in (
        "deadline",
        "deadline_at",
        "closes_at",
        "close_at",
        "ends_at",
        "end_at",
        "submission_deadline",
        "round_deadline",
    ):
        parsed = parse_timestamp(payload.get(key))
        if parsed is not None:
            return parsed
    for nest_key in ("round", "current_round", "clock", "schedule"):
        nested = payload.get(nest_key)
        if isinstance(nested, dict):
            found = extract_deadline(nested)
            if found is not None:
                return found
    return None


def extract_round_open(payload: dict[str, Any] | None) -> datetime | None:
    """Extract round-open timestamp if present."""
    if not payload:
        return None
    for key in ("opens_at", "open_at", "started_at", "start_at", "round_open"):
        parsed = parse_timestamp(payload.get(key))
        if parsed is not None:
            return parsed
    for nest_key in ("round", "current_round", "clock", "schedule"):
        nested = payload.get(nest_key)
        if isinstance(nested, dict):
            found = extract_round_open(nested)
            if found is not None:
                return found
    return None


def seconds_until(
    deadline: datetime | str | None,
    *,
    observed_at: datetime | str | None,
) -> int | None:
    """
    Countdown seconds from an authoritative observation time to a deadline.

    Returns None when either timestamp is missing/unparseable (UNKNOWN, not zero).
    """
    dl = parse_timestamp(deadline) if not isinstance(deadline, datetime) else (
        deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
    )
    obs = parse_timestamp(observed_at) if not isinstance(observed_at, datetime) else (
        observed_at if observed_at.tzinfo else observed_at.replace(tzinfo=UTC)
    )
    if dl is None or obs is None:
        return None
    return int((dl - obs).total_seconds())


def countdown(
    *,
    deadline: Any = None,
    observed_at: Any = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a countdown record from server-observed time and a deadline.

    Does not fall back to the local browser/operator clock for the remaining
    seconds when authoritative fields are absent — remaining is null/UNKNOWN.
    """
    obs = parse_timestamp(observed_at) or extract_server_observed_at(payload)
    dl = parse_timestamp(deadline) or extract_deadline(payload)
    opened = extract_round_open(payload) if payload else None
    remaining = seconds_until(dl, observed_at=obs)
    return {
        "observed_at": obs.isoformat() if obs else None,
        "deadline": dl.isoformat() if dl else None,
        "opens_at": opened.isoformat() if opened else None,
        "remaining_seconds": remaining,
        "source": "server_observation" if obs is not None else "UNKNOWN",
    }
