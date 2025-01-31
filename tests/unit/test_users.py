import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import pytest

from app.main import app
from app import models, schemas
from app.database import get_db

client = TestClient(app)

# Создаём фиктивного пользователя для тестов
dummy_user = models.User(
    id=1,
    email="test@example.com",
    hashed_password="hashed",
    is_active=True,
    is_verified=True,
    avatar_url=None,
)

# Фикстура для подмены зависимости get_db (если потребуется работать с сессией)
def override_get_db():
    # Можно вернуть мок-объект сессии
    db = MagicMock(spec=Session)
    return db

app.dependency_overrides[get_db] = override_get_db

# Тест для эндпоинта /users/me с валидным токеном
def test_read_users_me_valid_token():
    # Патчим функцию, которая ищет пользователя по токену, чтобы вернуть dummy_user
    with patch("app.crud.get_user_by_token", return_value=dummy_user):
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer valid-token"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dummy_user.id
    assert data["email"] == dummy_user.email

# Тест для эндпоинта /users/me с невалидным токеном
def test_read_users_me_invalid_token():
    # Если пользователь не найден, функция get_user_by_token возвращает None
    with patch("app.crud.get_user_by_token", return_value=None):
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid authentication credentials"

# Тест для эндпоинта /users/me/avatar при успешной загрузке изображения
def test_update_avatar_success():
    # Задаем фиктивный URL для аватара, который будет возвращен после загрузки в Cloudinary
    dummy_avatar_url = "https://example.com/avatar.png"
    # Обновленный пользователь с заполненным avatar_url
    updated_user = dummy_user
    updated_user.avatar_url = dummy_avatar_url

    # Создаем фиктивный image-файл
    image_content = b"fake image data"
    file = io.BytesIO(image_content)
    file.name = "avatar.png"

    with patch("app.crud.get_user_by_token", return_value=dummy_user):
        # Патчим функцию обновления аватара, чтобы возвращалась обновленная модель пользователя
        with patch("app.crud.update_avatar", return_value=updated_user) as mock_update_avatar:
            # Патчим функцию загрузки в Cloudinary; патчим напрямую cloudinary.uploader.upload
            with patch("cloudinary.uploader.upload", return_value={"secure_url": dummy_avatar_url}) as mock_upload:
                response = client.post(
                    "/users/me/avatar",
                    headers={"Authorization": "Bearer valid-token"},
                    files={"file": ("avatar.png", file, "image/png")}
                )
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"] == dummy_avatar_url
    mock_upload.assert_called_once()
    mock_update_avatar.assert_called_once()

# Тест для эндпоинта /users/me/avatar с некорректным типом файла (не изображение)
def test_update_avatar_invalid_file_type():
    # Создаем фиктивный текстовый файл
    file_content = b"not an image"
    file = io.BytesIO(file_content)
    file.name = "file.txt"

    with patch("app.crud.get_user_by_token", return_value=dummy_user):
        response = client.post(
            "/users/me/avatar",
            headers={"Authorization": "Bearer valid-token"},
            files={"file": ("file.txt", file, "text/plain")}
        )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Invalid image type"
