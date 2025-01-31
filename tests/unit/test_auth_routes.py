import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app import schemas, crud, utils, models

client = TestClient(app)

# ✅ Mock email sending
@pytest.fixture
def mock_send_email():
    with patch("app.routers.auth.send_verification_email_internal") as mock:
        yield mock

# ✅ Test successful user registration
def test_register_user(db, mock_send_email):
    with patch("app.crud.get_user_by_email", return_value=None):
        new_user = models.User(
            id=1, email="test@example.com", hashed_password="hashed", is_active=True, is_verified=False
        )
        with patch("app.crud.create_user", return_value=new_user):
            response = client.post(
                "/auth/register",
                json={"email": "test@example.com", "password": "securepassword"}
            )

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    mock_send_email.assert_called_once_with("test@example.com")


# ✅ Test registering with an existing email
def test_register_existing_user(db):
    with patch("app.crud.get_user_by_email", return_value=models.User(
        id=1, email="test@example.com", hashed_password="hashed", is_active=True, is_verified=False
    )):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "securepassword"}
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


# ✅ Test successful login
def test_login_success(db):
    hashed_password = utils.get_password_hash("securepassword")
    mock_user = models.User(
        id=1, email="test@example.com", hashed_password=hashed_password, is_active=True, is_verified=True
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "securepassword"}
        )

    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"


# ✅ Test sending verification email
def test_send_verification_email(db, mock_send_email):
    mock_user = models.User(
        id=1, email="test@example.com", hashed_password="hashed", is_active=True, is_verified=False
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.post(
            "/auth/send-verification-email",
            json={"email": "test@example.com"},
            headers={"Content-Type": "application/json"}
        )

    print(response.json())  # ✅ Debug response body if needed
    assert response.status_code == 200




# ✅ Fix: HTTP 422 → 400 when user is already verified
def test_send_verification_email_already_verified(db):
    mock_user = models.User(
        id=1, email="test@example.com", hashed_password="hashed", is_active=True, is_verified=True
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.post(
            "/auth/send-verification-email",
            json={"email": "test@example.com"},
            headers={"Content-Type": "application/json"}
        )

    print(response.json())  # ✅ Debug response body if needed
    assert response.status_code == 400




# ✅ Test confirming email successfully
def test_confirm_email(db):
    mock_user = models.User(
        id=1, email="test@example.com", hashed_password="hashed", is_active=True, is_verified=False
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        db.add(mock_user)  # ✅ Attach user to session
        db.commit()  # ✅ Commit before refresh

        response = client.get("/auth/confirm-email?email=test@example.com")

    assert response.status_code == 200




# ✅ Fix: Confirming already verified email
def test_confirm_already_verified_email(db):
    mock_user = models.User(
        id=1, email="test@example.com", hashed_password="hashed", is_active=True, is_verified=True
    )

    with patch("app.crud.get_user_by_email", return_value=mock_user):
        response = client.get("/auth/confirm-email?email=test@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already verified"


# ✅ Fix: Confirming a non-existent email
def test_confirm_non_existent_email(db):
    with patch("app.crud.get_user_by_email", return_value=None):
        response = client.get("/auth/confirm-email?email=nonexistent@example.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
