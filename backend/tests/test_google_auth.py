"""Tests for Google sign-in endpoint."""

from unittest.mock import patch
from uuid import uuid4

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models
from app import app
from auth_security import hash_password
from database import Base, get_db
from services.google_auth import GoogleAuthError


def _google_claims(email: str = "user@gmail.com", uid: str | None = None) -> dict:
    return {
        "firebase_uid": uid or f"firebase-{uuid4()}",
        "email": email,
        "name": "Test User",
    }


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


@patch("routers.auth.verify_google_id_token")
def test_google_auth_creates_user(mock_verify, client, db_session):
    claims = _google_claims()
    mock_verify.return_value = claims

    response = client.post(
        "/auth/google",
        json={"id_token": "fake-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]

    user = db_session.query(models.User).filter(models.User.email == claims["email"]).first()
    assert user is not None
    assert user.firebase_uid == claims["firebase_uid"]
    assert user.password is None


@patch("routers.auth.verify_google_id_token")
def test_google_auth_links_existing_email_user(mock_verify, client, db_session):
    email = "existing@gmail.com"
    user = models.User(
        email=email,
        password=hash_password("password123"),
    )
    db_session.add(user)
    db_session.commit()

    claims = _google_claims(email=email)
    mock_verify.return_value = claims

    response = client.post(
        "/auth/google",
        json={"id_token": "fake-token"},
    )

    assert response.status_code == 200
    db_session.refresh(user)
    assert user.firebase_uid == claims["firebase_uid"]
    assert user.password is not None


@patch("services.google_auth.init_firebase", return_value=False)
def test_google_auth_requires_firebase(_mock_init):
    from services.google_auth import verify_google_id_token

    with pytest.raises(GoogleAuthError) as exc_info:
        verify_google_id_token("token")
    assert exc_info.value.status_code == 503


def test_password_login_rejects_google_only_user(client, db_session):
    user = models.User(
        email="googleonly@gmail.com",
        password=None,
        firebase_uid="uid-123",
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": "anything"},
    )
    assert response.status_code == 401
    assert "Google" in response.json()["detail"]
