import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import models
import schemas
from auth_security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    require_jwt_secret,
    verify_password,
)
from database import SessionLocal, get_db
from deps import get_current_user
from rate_limit import limiter
from services.auth_mailer import send_password_reset_email, send_verification_email
from services.email_tokens import verify_otp
from services.google_auth import GoogleAuthError, verify_google_id_token

router = APIRouter()
logger = logging.getLogger(__name__)

_GENERIC_RESET_MSG = (
    "If an account exists for that email, you will receive password reset instructions."
)


def _issue_tokens(user: models.User) -> schemas.TokenResponse:
    try:
        require_jwt_secret()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    return schemas.TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
        email_verified=bool(user.email_verified),
    )


def _mark_email_verified(user: models.User, db: Session) -> None:
    if user.email_verified:
        return
    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("event=email_verified user_id=%s", user.id)


def _send_verification_email_background(user_id: UUID) -> None:
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            return
        send_verification_email(db, user)
    finally:
        db.close()


def _send_password_reset_email_background(user_id: UUID) -> None:
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            return
        send_password_reset_email(db, user)
    finally:
        db.close()


@router.post("/register", response_model=schemas.TokenResponse)
@limiter.limit("20/minute")
def register(
    request: Request,
    body: schemas.UserRegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _ = request
    email = body.email.strip().lower()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        if existing.password is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email uses Google sign-in. Continue with Google.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = models.User(
        email=email,
        password=hash_password(body.password),
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    background_tasks.add_task(_send_verification_email_background, user.id)
    return _issue_tokens(user)


@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: schemas.UserLoginRequest,
    db: Session = Depends(get_db),
):
    _ = request
    user = (
        db.query(models.User)
        .filter(models.User.email == body.email.strip().lower())
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google sign-in.",
        )
    if not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return _issue_tokens(user)


@router.post("/google", response_model=schemas.TokenResponse)
@limiter.limit("20/minute")
def google_login(
    request: Request,
    body: schemas.GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    _ = request
    try:
        claims = verify_google_id_token(body.id_token)
    except GoogleAuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    firebase_uid = claims["firebase_uid"]
    email = claims["email"]

    user = (
        db.query(models.User)
        .filter(models.User.firebase_uid == firebase_uid)
        .first()
    )
    if user is None:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is not None:
            if user.firebase_uid and user.firebase_uid != firebase_uid:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is linked to another Google account",
                )
            user.firebase_uid = firebase_uid
            _mark_email_verified(user, db)
            db.commit()
            db.refresh(user)
            logger.info(
                "event=google_auth_linked user_id=%s email=%s",
                user.id,
                email,
            )
        else:
            user = models.User(
                email=email,
                password=None,
                firebase_uid=firebase_uid,
                email_verified=True,
                email_verified_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(
                "event=google_auth_registered user_id=%s email=%s",
                user.id,
                email,
            )
    else:
        if user.email != email:
            user.email = email
        _mark_email_verified(user, db)
        db.commit()
        db.refresh(user)
        logger.info("event=google_auth_login user_id=%s email=%s", user.id, email)

    return _issue_tokens(user)


@router.post("/refresh", response_model=schemas.TokenResponse)
@limiter.limit("30/minute")
def refresh_tokens(
    request: Request,
    body: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    _ = request
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    try:
        user_id = UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    try:
        require_jwt_secret()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    return _issue_tokens(user)


@router.post("/forgot-password", response_model=schemas.MessageResponse)
@limiter.limit("10/minute")
def forgot_password(
    request: Request,
    body: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _ = request
    email = body.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is not None and user.password is not None:
        background_tasks.add_task(_send_password_reset_email_background, user.id)
    return schemas.MessageResponse(message=_GENERIC_RESET_MSG)


@router.post("/reset-password", response_model=schemas.MessageResponse)
@limiter.limit("10/minute")
def reset_password(
    request: Request,
    body: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    _ = request
    email = body.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    invalid_code = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired code.",
    )
    if user is None or user.password is None:
        raise invalid_code
    if not verify_otp(db, user.id, models.AuthTokenPurpose.PASSWORD_RESET, body.code):
        raise invalid_code
    user.password = hash_password(body.password)
    db.add(user)
    db.commit()
    logger.info("event=password_reset_completed user_id=%s", user.id)
    return schemas.MessageResponse(message="Password updated. You can sign in now.")


@router.post("/verify-email", response_model=schemas.MessageResponse)
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    body: schemas.VerifyEmailRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ = request
    if current_user.email_verified:
        return schemas.MessageResponse(message="Email is already verified.")
    if not verify_otp(db, current_user.id, models.AuthTokenPurpose.EMAIL_VERIFY, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )
    _mark_email_verified(current_user, db)
    return schemas.MessageResponse(message="Email verified successfully.")


@router.post("/resend-verification", response_model=schemas.MessageResponse)
@limiter.limit("5/minute")
def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ = request
    if current_user.email_verified:
        return schemas.MessageResponse(message="Email is already verified.")
    if current_user.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google accounts are already verified via Google.",
        )
    background_tasks.add_task(_send_verification_email_background, current_user.id)
    return schemas.MessageResponse(
        message="Verification email sent. Check your inbox."
    )
