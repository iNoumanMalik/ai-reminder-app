"""High-level auth emails (verification + password reset)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

import models
from services import email_service, email_tokens

logger = logging.getLogger(__name__)


def send_verification_email(db: Session, user: models.User) -> bool:
    if user.email_verified:
        return True
    if user.password is None:
        return True
    raw = email_tokens.create_token(
        db, user.id, models.AuthTokenPurpose.EMAIL_VERIFY
    )
    base = email_service.public_app_url()
    verify_url = f"{base}/auth/verify-email/confirm?token={raw}"
    app_url = f"aireminder://verify-email?token={raw}"
    subject = "Verify your AI Reminder email"
    text = (
        f"Hi,\n\n"
        f"Please verify your email for AI Reminder:\n\n"
        f"{verify_url}\n\n"
        f"Or open in the app: {app_url}\n\n"
        f"If you did not create an account, you can ignore this message.\n"
    )
    html = (
        f"<p>Please verify your email for <strong>AI Reminder</strong>:</p>"
        f'<p><a href="{verify_url}">Verify email</a></p>'
        f"<p>Link expires in 48 hours.</p>"
    )
    ok = email_service.send_email(user.email, subject, text, html)
    if ok:
        logger.info("event=verification_email_sent user_id=%s", user.id)
    return ok


def send_password_reset_email(db: Session, user: models.User) -> bool:
    if user.password is None:
        return False
    raw = email_tokens.create_token(
        db, user.id, models.AuthTokenPurpose.PASSWORD_RESET
    )
    base = email_service.public_app_url()
    reset_url = f"{base}/auth/reset-password/form?token={raw}"
    app_url = f"aireminder://reset-password?token={raw}"
    subject = "Reset your AI Reminder password"
    text = (
        f"Hi,\n\n"
        f"Reset your password using this link (expires in 2 hours):\n\n"
        f"{reset_url}\n\n"
        f"Or in the app: {app_url}\n\n"
        f"If you did not request this, ignore this email.\n"
    )
    html = (
        f"<p>Reset your <strong>AI Reminder</strong> password:</p>"
        f'<p><a href="{reset_url}">Reset password</a></p>'
        f"<p>This link expires in 2 hours.</p>"
    )
    ok = email_service.send_email(user.email, subject, text, html)
    if ok:
        logger.info("event=password_reset_email_sent user_id=%s", user.id)
    return ok
