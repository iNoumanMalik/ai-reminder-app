"""High-level auth emails (verification + password reset), OTP-based."""

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
    code = email_tokens.create_otp(db, user.id, models.AuthTokenPurpose.EMAIL_VERIFY)
    minutes = email_tokens.EMAIL_VERIFY_OTP_MINUTES
    subject = "Your AI Reminder verification code"
    text = (
        f"Hi,\n\n"
        f"Your verification code is: {code}\n\n"
        f"Enter this code in the app to verify your email. "
        f"It expires in {minutes} minutes.\n\n"
        f"If you did not create an account, you can ignore this message.\n"
    )
    html = (
        f"<p>Your <strong>AI Reminder</strong> verification code:</p>"
        f'<p style="font-size:28px;font-weight:700;letter-spacing:4px;">{code}</p>'
        f"<p>Enter this in the app. It expires in {minutes} minutes.</p>"
    )
    ok = email_service.send_email(user.email, subject, text, html)
    if ok:
        logger.info("event=verification_email_sent user_id=%s", user.id)
    return ok


def send_password_reset_email(db: Session, user: models.User) -> bool:
    if user.password is None:
        return False
    code = email_tokens.create_otp(db, user.id, models.AuthTokenPurpose.PASSWORD_RESET)
    minutes = email_tokens.PASSWORD_RESET_OTP_MINUTES
    subject = "Your AI Reminder password reset code"
    text = (
        f"Hi,\n\n"
        f"Your password reset code is: {code}\n\n"
        f"Enter this code in the app to reset your password. "
        f"It expires in {minutes} minutes.\n\n"
        f"If you did not request this, ignore this email.\n"
    )
    html = (
        f"<p>Your <strong>AI Reminder</strong> password reset code:</p>"
        f'<p style="font-size:28px;font-weight:700;letter-spacing:4px;">{code}</p>'
        f"<p>Enter this in the app. It expires in {minutes} minutes.</p>"
    )
    ok = email_service.send_email(user.email, subject, text, html)
    if ok:
        logger.info("event=password_reset_email_sent user_id=%s", user.id)
    return ok
