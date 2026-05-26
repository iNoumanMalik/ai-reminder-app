"""One-time tokens for email verification and password reset."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)

EMAIL_VERIFY_HOURS = int(__import__("os").getenv("EMAIL_VERIFY_TOKEN_HOURS", "48"))
PASSWORD_RESET_HOURS = int(__import__("os").getenv("PASSWORD_RESET_TOKEN_HOURS", "2"))


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _invalidate_existing(db: Session, user_id: UUID, purpose: str) -> None:
    now = datetime.now(timezone.utc)
    rows = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.user_id == user_id,
            models.AuthToken.purpose == purpose,
            models.AuthToken.used_at.is_(None),
            models.AuthToken.expires_at > now,
        )
        .all()
    )
    for row in rows:
        row.used_at = now
        db.add(row)


def create_token(db: Session, user_id: UUID, purpose: str) -> str:
    hours = (
        EMAIL_VERIFY_HOURS
        if purpose == models.AuthTokenPurpose.EMAIL_VERIFY
        else PASSWORD_RESET_HOURS
    )
    _invalidate_existing(db, user_id, purpose)
    raw = secrets.token_urlsafe(32)
    row = models.AuthToken(
        user_id=user_id,
        token_hash=_hash_token(raw),
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
    )
    db.add(row)
    db.commit()
    logger.info(
        "event=auth_token_created user_id=%s purpose=%s expires_hours=%s",
        user_id,
        purpose,
        hours,
    )
    return raw


def consume_token(db: Session, raw_token: str, purpose: str) -> Optional[models.User]:
    cleaned = (raw_token or "").strip()
    if not cleaned:
        return None
    now = datetime.now(timezone.utc)
    row = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.token_hash == _hash_token(cleaned),
            models.AuthToken.purpose == purpose,
            models.AuthToken.used_at.is_(None),
            models.AuthToken.expires_at > now,
        )
        .first()
    )
    if row is None:
        return None
    row.used_at = now
    db.add(row)
    user = db.query(models.User).filter(models.User.id == row.user_id).first()
    if user is None:
        db.commit()
        return None
    db.commit()
    db.refresh(user)
    logger.info("event=auth_token_consumed user_id=%s purpose=%s", user.id, purpose)
    return user
