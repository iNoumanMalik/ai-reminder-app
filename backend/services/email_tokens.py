"""One-time 6-digit OTP codes for email verification and password reset."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_PATTERN = re.compile(r"^\d{6}$")
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
EMAIL_VERIFY_OTP_MINUTES = int(os.getenv("EMAIL_VERIFY_OTP_MINUTES", "10"))
PASSWORD_RESET_OTP_MINUTES = int(os.getenv("PASSWORD_RESET_OTP_MINUTES", "10"))


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


def _generate_otp() -> str:
    return f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"


def create_otp(db: Session, user_id: UUID, purpose: str) -> str:
    """Generate, store (hashed), and return a plaintext 6-digit OTP.

    Invalidates any prior unused/unexpired code for the same user+purpose,
    so requesting a new code (including "resend") naturally supersedes the
    old one.
    """
    minutes = (
        EMAIL_VERIFY_OTP_MINUTES
        if purpose == models.AuthTokenPurpose.EMAIL_VERIFY
        else PASSWORD_RESET_OTP_MINUTES
    )
    _invalidate_existing(db, user_id, purpose)
    code = _generate_otp()
    row = models.AuthToken(
        user_id=user_id,
        token_hash=_hash_token(code),
        purpose=purpose,
        attempts=0,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes),
    )
    db.add(row)
    db.commit()
    logger.info(
        "event=otp_created user_id=%s purpose=%s expires_minutes=%s",
        user_id,
        purpose,
        minutes,
    )
    return code


def verify_otp(db: Session, user_id: UUID, purpose: str, code: str) -> bool:
    """Verify a 6-digit code scoped to a known user.

    Codes are only 1,000,000 combinations, so lookup MUST be scoped by
    user_id (unlike the old opaque-token lookup) to avoid one user's code
    matching another user's row on hash collision. Increments the attempts
    counter on mismatch and locks the code out after OTP_MAX_ATTEMPTS
    failures. Returns True and marks the row used_at on success.
    """
    cleaned = (code or "").strip()
    if not OTP_PATTERN.match(cleaned):
        return False
    now = datetime.now(timezone.utc)
    row = (
        db.query(models.AuthToken)
        .filter(
            models.AuthToken.user_id == user_id,
            models.AuthToken.purpose == purpose,
            models.AuthToken.used_at.is_(None),
            models.AuthToken.expires_at > now,
        )
        .order_by(models.AuthToken.created_at.desc())
        .first()
    )
    if row is None:
        return False
    if row.attempts >= OTP_MAX_ATTEMPTS:
        row.used_at = now
        db.add(row)
        db.commit()
        return False
    if row.token_hash != _hash_token(cleaned):
        row.attempts += 1
        if row.attempts >= OTP_MAX_ATTEMPTS:
            row.used_at = now
            logger.info("event=otp_locked user_id=%s purpose=%s", user_id, purpose)
        db.add(row)
        db.commit()
        return False
    row.used_at = now
    db.add(row)
    db.commit()
    logger.info("event=otp_verified user_id=%s purpose=%s", user_id, purpose)
    return True
