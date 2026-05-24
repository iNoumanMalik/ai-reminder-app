import logging
from typing import Any, Dict, Optional

from firebase_admin import auth as firebase_auth

from services.firebase import init_firebase

logger = logging.getLogger(__name__)


class GoogleAuthError(Exception):
    def __init__(self, message: str, *, status_code: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def verify_google_id_token(id_token: str) -> Dict[str, Any]:
    """Verify a Firebase ID token from Google Sign-In and return decoded claims."""
    token = (id_token or "").strip()
    if not token:
        raise GoogleAuthError("Missing ID token", status_code=400)

    if not init_firebase():
        raise GoogleAuthError(
            "Google sign-in is not configured on the server",
            status_code=503,
        )

    try:
        decoded = firebase_auth.verify_id_token(token)
    except firebase_auth.InvalidIdTokenError as exc:
        logger.warning("event=google_auth_invalid_token error=%s", exc)
        raise GoogleAuthError("Invalid or expired Google token") from exc
    except firebase_auth.ExpiredIdTokenError as exc:
        logger.warning("event=google_auth_expired_token error=%s", exc)
        raise GoogleAuthError("Invalid or expired Google token") from exc
    except Exception as exc:
        logger.exception("event=google_auth_verify_failed error=%s", exc)
        raise GoogleAuthError("Could not verify Google token") from exc

    sign_in_provider = (
        decoded.get("firebase", {}).get("sign_in_provider")
        if isinstance(decoded.get("firebase"), dict)
        else None
    )
    if sign_in_provider and sign_in_provider != "google.com":
        logger.warning(
            "event=google_auth_wrong_provider provider=%s", sign_in_provider
        )
        raise GoogleAuthError("Token was not issued by Google sign-in")

    email = (decoded.get("email") or "").strip().lower()
    if not email:
        raise GoogleAuthError(
            "Google account has no email address",
            status_code=400,
        )
    if decoded.get("email_verified") is False:
        raise GoogleAuthError("Google email is not verified", status_code=400)

    uid = decoded.get("uid") or decoded.get("sub")
    if not uid:
        raise GoogleAuthError("Invalid Google token payload", status_code=400)

    logger.info(
        "event=google_auth_verified firebase_uid=%s email=%s",
        uid,
        email,
    )
    return {
        "firebase_uid": str(uid),
        "email": email,
        "name": decoded.get("name"),
    }
