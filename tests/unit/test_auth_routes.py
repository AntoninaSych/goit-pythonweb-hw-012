import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app import schemas, crud, utils

client = TestClient(app)


# ✅ Mock database fixture
@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    yield db


# ✅ Mock email sending
@pytest.fixture
def mock_send_email():
    with patch("app.auth.send_verification_email_internal") as mock:
        yield mock


# ✅ Test successful user registration
def test_register_user(mock_db, mock_send_email):
    mock_db.query.return_value.filter_by.return_value.first.return_value = None  # No existing user

    mock_user = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=False
    )
    with patch("app.crud.create_user", return_value=mock_user):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "securepassword"}
        )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    mock_send_email.assert_called_once_with("test@example.com")  # ✅ Ensures email is sent


# ✅ Test registering with an existing email
def test_register_existing_user(mock_db):
    mock_db.query.return_value.filter_by.return_value.first.return_value = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=False
    )

    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


# ✅ Test successful login
def test_login_success(mock_db):
    hashed_password = utils.get_password_hash("securepassword")
    mock_user = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=True
    )
    mock_user.hashed_password = hashed_password

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "securepassword"}
        )

    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"


# ✅ Test login with invalid credentials
def test_login_invalid_credentials(mock_db):
    with patch("app.crud.get_user_by_email", return_value=None):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# ✅ Test sending verification email
def test_send_verification_email(mock_db, mock_send_email):
    mock_user = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=False
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.post("/auth/send-verification-email", json={"email": "test@example.com"})

    assert response.status_code == 200
    assert response.json()["message"] == "Verification email has been sent."
    mock_send_email.assert_called_once_with("test@example.com")


# ✅ Test sending verification email for already verified user
def test_send_verification_email_already_verified(mock_db):
    mock_user = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=True
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.post("/auth/send-verification-email", json={"email": "test@example.com"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already verified"


# ✅ Test confirming email successfully
def test_confirm_email(mock_db):
    mock_user = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=False
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.get("/auth/confirm-email?email=test@example.com")

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


# ✅ Test confirming an already verified email
def test_confirm_already_verified_email(mock_db):
    mock_user = schemas.UserResponse(
        id=1, email="test@example.com", is_active=True, is_verified=True
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.get("/auth/confirm-email?email=test@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already verified"


# ✅ Test confirming a non-existent email
def test_confirm_non_existent_email(mock_db):
    with patch("app.crud.get_user_by_email", return_value=None):
        response = client.get("/auth/confirm-email?email=nonexistent@example.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
