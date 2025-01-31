import pytest
from app.utils import verify_password, get_password_hash
from app.auth import create_access_token, decode_access_token
from app.utils import verify_password, get_password_hash
import pytest
from datetime import timedelta, datetime
from jose import jwt, JWTError
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import auth, crud, models, utils
from app.config import settings

# Тестируем создание access token
def test_create_access_token():
    data = {"sub": "test@example.com"}
    token = auth.create_access_token(data)
    # Раскодируем токен для проверки
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert payload.get("sub") == "test@example.com"
    assert "exp" in payload
    # Проверяем, что время окончания действительно в будущем
    exp = payload.get("exp")
    assert exp > int(datetime.utcnow().timestamp())

def test_create_access_token_with_expires_delta():
    data = {"sub": "test@example.com"}
    delta = timedelta(minutes=10)
    token = auth.create_access_token(data, expires_delta=delta)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[auth.ALGORITHM])
    # Ожидаем, что время окончания примерно через 10 минут
    expected_exp = int((datetime.utcnow() + delta).timestamp())
    actual_exp = payload.get("exp")
    # Допускаем разницу в несколько секунд
    assert abs(actual_exp - expected_exp) < 5

# Тестируем декодирование токена
def test_decode_access_token_valid():
    data = {"sub": "test@example.com"}
    token = auth.create_access_token(data)
    payload = auth.decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "test@example.com"

def test_decode_access_token_invalid():
    invalid_token = "invalid.token.value"
    payload = auth.decode_access_token(invalid_token)
    assert payload is None

# Тест для функции get_db — проверяем, что генератор возвращает объект Session
def test_get_db():
    gen = auth.get_db()
    db_instance = next(gen)
    # Проверяем, что объект db_instance является экземпляром SQLAlchemy Session
    assert isinstance(db_instance, Session)
    # После первого next() генератор должен завершиться (с выбросом StopIteration)
    with pytest.raises(StopIteration):
        next(gen)

# Для тестирования get_current_user создаём фиктивный DB session,
# который реализует минимальный интерфейс для работы с crud.get_user_by_email
class DummyQuery:
    def __init__(self, user):
        self.user = user
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return self.user

class DummySession:
    def __init__(self, user):
        self.user = user
    def query(self, model):
        return DummyQuery(self.user)

def test_get_current_user_valid():
    # Фиктивный пользователь, который должен быть возвращён
    dummy_user = models.User(
        id=1,
        email="test@example.com",
        hashed_password="dummy",
        is_active=True,
        is_verified=True
    )
    dummy_db = DummySession(dummy_user)
    token = auth.create_access_token({"sub": "test@example.com"})

    # Патчим crud.get_user_by_email, чтобы он возвращал dummy_user
    def fake_get_user_by_email(db, email):
        return dummy_user if email == "test@example.com" else None

    original_get_user_by_email = crud.get_user_by_email
    crud.get_user_by_email = fake_get_user_by_email

    result = auth.get_current_user(token, dummy_db)
    assert result == dummy_user

    # Восстанавливаем оригинальную функцию
    crud.get_user_by_email = original_get_user_by_email

def test_get_current_user_invalid_token():
    dummy_db = DummySession(None)
    invalid_token = "invalid.token"
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(invalid_token, dummy_db)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail

def test_get_current_user_user_not_found():
    # Создаём фиктивную сессию, где get_user_by_email вернёт None
    dummy_db = DummySession(None)
    token = auth.create_access_token({"sub": "nonexistent@example.com"})

    def fake_get_user_by_email(db, email):
        return None

    original_get_user_by_email = crud.get_user_by_email
    crud.get_user_by_email = fake_get_user_by_email

    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(token, dummy_db)
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail

    crud.get_user_by_email = original_get_user_by_email

def test_get_current_active_user_success():
    # Активный и верифицированный пользователь
    dummy_user = models.User(
        id=1,
        email="active@example.com",
        hashed_password="dummy",
        is_active=True,
        is_verified=True
    )
    result = auth.get_current_active_user(dummy_user)
    assert result == dummy_user

def test_get_current_active_user_inactive():
    dummy_user = models.User(
        id=1,
        email="inactive@example.com",
        hashed_password="dummy",
        is_active=False,
        is_verified=True
    )
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_active_user(dummy_user)
    assert exc_info.value.status_code == 400
    assert "Inactive user" in exc_info.value.detail

def test_get_current_active_user_not_verified():
    dummy_user = models.User(
        id=1,
        email="unverified@example.com",
        hashed_password="dummy",
        is_active=True,
        is_verified=False
    )
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_active_user(dummy_user)
    assert exc_info.value.status_code == 400
    assert "Email not verified" in exc_info.value.detail

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
