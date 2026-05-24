import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import models
import schemas
from rate_limit import limiter
from auth_security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    require_jwt_secret,
    verify_password,
)
from database import get_db
from services.google_auth import GoogleAuthError, verify_google_id_token

router = APIRouter()
logger = logging.getLogger(__name__)


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
    )


@router.post("/register", response_model=schemas.TokenResponse)
@limiter.limit("20/minute")
def register(
    request: Request,
    body: schemas.UserRegisterRequest,
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
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user)


@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: schemas.UserLoginRequest,
    db: Session = Depends(get_db),
):
    _ = request  # used by SlowAPI rate limiter
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
    return schemas.TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
    )
