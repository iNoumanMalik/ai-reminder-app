"""Tests for email verification and password reset."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from app import app
from auth_security import hash_password, verify_password
from database import Base, get_db
from services.email_tokens import create_token


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-32chars-minimum!!")


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@patch("routers.auth.send_verification_email", return_value=True)
def test_register_sets_unverified_and_sends_email(mock_send, client, db_session):
    response = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email_verified"] is False
    mock_send.assert_called_once()
    user = db_session.query(models.User).filter(models.User.email == "new@example.com").first()
    assert user is not None
    assert user.email_verified is False


@patch("routers.auth.send_password_reset_email", return_value=True)
def test_forgot_password_sends_for_password_user(mock_send, client, db_session):
    user = models.User(
        email="reset@example.com",
        password=hash_password("oldpassword1"),
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/forgot-password",
        json={"email": user.email},
    )
    assert response.status_code == 200
    mock_send.assert_called_once()


def test_forgot_password_generic_for_unknown_email(client):
    response = client.post(
        "/auth/forgot-password",
        json={"email": "missing@example.com"},
    )
    assert response.status_code == 200
    assert "account exists" in response.json()["message"].lower()


def test_reset_password_updates_hash(client, db_session):
    user = models.User(
        email="reset2@example.com",
        password=hash_password("oldpassword1"),
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    raw = create_token(db_session, user.id, models.AuthTokenPurpose.PASSWORD_RESET)

    response = client.post(
        "/auth/reset-password",
        json={"token": raw, "password": "newpassword99"},
    )
    assert response.status_code == 200
    db_session.refresh(user)
    assert verify_password("newpassword99", user.password)


def test_verify_email_marks_user_verified(client, db_session):
    user = models.User(
        email="verify@example.com",
        password=hash_password("password123"),
        email_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    raw = create_token(db_session, user.id, models.AuthTokenPurpose.EMAIL_VERIFY)

    response = client.post(
        "/auth/verify-email",
        json={"token": raw},
    )
    assert response.status_code == 200
    db_session.refresh(user)
    assert user.email_verified is True
    assert user.email_verified_at is not None


def test_verify_email_confirm_get(client, db_session):
    user = models.User(
        email="verify2@example.com",
        password=hash_password("password123"),
        email_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    raw = create_token(db_session, user.id, models.AuthTokenPurpose.EMAIL_VERIFY)

    response = client.get(f"/auth/verify-email/confirm?token={raw}")
    assert response.status_code == 200
    assert "verified" in response.text.lower()
    db_session.refresh(user)
    assert user.email_verified is True
