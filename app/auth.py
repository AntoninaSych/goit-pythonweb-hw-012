import json
from datetime import datetime, timedelta

import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import crud, models, schemas, utils
from .config import settings
from .database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
from datetime import datetime, timedelta
from jose import JWTError, jwt

from .config import settings

# Секретний ключ та алгоритм для підпису токенів
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Ініціалізація Redis клієнта через URL з settings (наприклад, "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Створює JWT токен доступу.

    :param data: Дані, які потрібно зашифрувати у токені (наприклад, email користувача).
    :param expires_delta: Термін дії токена (за замовчуванням 30 хвилин).
    :return: Строка з JWT токеном.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # Додаємо час дії токена
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # Додаємо термін дії в дані токена
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Шифруємо дані в JWT
    return encoded_jwt

def decode_access_token(token: str):
    """
    Декодує JWT-токен, повертає розкодувані дані або None, якщо токен недійсний.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = utils.decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception
    email: str = payload.get("sub")

    # Спроба отримати користувача з кешу Redis
    cache_key = f"user:{email}"
    cached_user = redis_client.get(cache_key)
    if cached_user:
        user_data = json.loads(cached_user)
        return models.User(**user_data)

    # Якщо в кеші немає, звертаємось до бази даних
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    # Формуємо словник для кешування (без чутливих даних)
    user_dict = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "avatar_url": user.avatar_url
    }
    # Зберігаємо в Redis на 5 хвилин (300 секунд)
    redis_client.setex(cache_key, 300, json.dumps(user_dict))
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return current_user
