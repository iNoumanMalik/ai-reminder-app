"""SMTP email delivery (logs links in development when SMTP is not configured)."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    host = os.getenv("SMTP_HOST", "").strip()
    from_addr = os.getenv("SMTP_FROM", "").strip()
    return bool(host and from_addr)


def public_app_url() -> str:
    """Base URL for links in emails (API or marketing site)."""
    return (
        os.getenv("APP_PUBLIC_URL", "").strip()
        or os.getenv("PUBLIC_APP_URL", "").strip()
        or "http://127.0.0.1:8000"
    ).rstrip("/")


def mobile_deep_link_base() -> str:
    return os.getenv("MOBILE_DEEP_LINK_BASE", "aireminder://").rstrip("/")


def send_email(
    to_address: str,
    subject: str,
    text_body: str,
    html_body: Optional[str] = None,
) -> bool:
    to_address = to_address.strip().lower()
    if not to_address:
        return False

    if not _smtp_configured():
        logger.info(
            "event=email_dev to=%s subject=%s\n%s",
            to_address,
            subject,
            text_body,
        )
        return True

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    from_addr = os.getenv("SMTP_FROM", "").strip()
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() != "false"

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_address
    message.attach(MIMEText(text_body, "plain", "utf-8"))
    if html_body:
        message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            if use_tls:
                server.starttls()
            if user:
                server.login(user, password)
            server.sendmail(from_addr, [to_address], message.as_string())
        logger.info("event=email_sent to=%s subject=%s", to_address, subject)
        return True
    except Exception as exc:
        logger.error("event=email_send_failed to=%s error=%s", to_address, exc)
        return False
