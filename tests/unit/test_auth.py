import pytest
from datetime import timedelta
from app.utils import verify_password, get_password_hash
from app.auth import create_access_token, decode_access_token
from app.utils import verify_password, get_password_hash

# Тест функції хешування пароля
def test_get_password_hash():
    """
    Перевіряє, що функція коректно хешує пароль.
    """
    password = "securepassword"
    hashed_password = get_password_hash(password)

    assert hashed_password != password  # Хешований пароль не повинен бути таким самим
    assert isinstance(hashed_password, str)  # Хеш має бути строкою

# Тест функції перевірки пароля
def test_verify_password():
    """
    Перевіряє, що введений пароль відповідає хешу.
    """
    password = "securepassword"
    hashed_password = get_password_hash(password)

    assert verify_password(password, hashed_password)  # Паролі повинні збігатися
    assert not verify_password("wrongpassword", hashed_password)  # Невірний пароль має повертати False

# Тест створення токена доступу
def test_create_access_token():
    """
    Перевіряє, що функція створює валідний JWT токен.
    """
    data = {"sub": "test@example.com"}  # Дані, які кодуємо у токен
    token = create_access_token(data, expires_delta=timedelta(minutes=15))

    assert isinstance(token, str)  # Токен має бути строкою
    assert "." in token  # JWT токен має містити крапки (роздільники секцій)

# Тест розшифровки токена
def test_decode_access_token():
    """
    Перевіряє, що створений токен можна коректно розшифрувати.
    """
    data = {"sub": "test@example.com"}  # Дані для кодування
    token = create_access_token(data, expires_delta=timedelta(minutes=15))

    decoded_data = decode_access_token(token)
    assert decoded_data is not None  # Переконуємось, що розшифровка успішна
    assert decoded_data["sub"] == "test@example.com"  # Перевіряємо, що email збережено


# Тест функції хешування пароля
def test_get_password_hash():
    """
    Перевіряє, що функція коректно хешує пароль.
    """
    password = "securepassword"
    hashed_password = get_password_hash(password)

    assert hashed_password != password  # Хешований пароль не повинен бути таким самим
    assert isinstance(hashed_password, str)  # Хеш має бути строкою

# Тест функції перевірки пароля
def test_verify_password():
    """
    Перевіряє, що введений пароль відповідає хешу.
    """
    password = "securepassword"
    hashed_password = get_password_hash(password)

    assert verify_password(password, hashed_password)  # Паролі повинні збігатися
    assert not verify_password("wrongpassword", hashed_password)  # Невірний пароль має повертати False

# Тест створення токена доступу
def test_create_access_token():
    """
    Перевіряє, що функція створює валідний JWT токен.
    """
    data = {"sub": "test@example.com"}  # Дані, які кодуємо у токен
    token = create_access_token(data, expires_delta=timedelta(minutes=15))

    assert isinstance(token, str)  # Токен має бути строкою
    assert "." in token  # JWT токен має містити крапки (роздільники секцій)
