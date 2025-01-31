from datetime import datetime, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import crud, models, utils
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# Термін дії токена для скидання пароля – 15 хвилин
PASSWORD_RESET_EXPIRE_MINUTES = 15

class PasswordResetRequest(BaseModel):
    email: str

class PasswordReset(BaseModel):
    new_password: str

def create_password_reset_token(email: str) -> str:
    """
    Генерує токен для скидання пароля з даними користувача.
    """
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    # Використовуємо секретний ключ та алгоритм із налаштувань
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=getattr(settings, "ALGORITHM", "HS256"))
    return token

@router.post("/request-password-reset", status_code=200)
def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Ендпоінт для запиту скидання пароля.
    Якщо користувача з вказаним email не існує, повертаємо успішну відповідь для захисту даних.
    У разі успіху генеруємо токен та відправляємо посилання для скидання (тут просто виводимо в консоль).
    """
    user = crud.get_user_by_email(db, email=request_data.email)
    # Для безпеки завжди повертаємо позитивну відповідь, навіть якщо користувача не знайдено
    if not user:
        return {"message": "Якщо акаунт з таким email існує, на нього відправлено лист для скидання пароля."}

    token = create_password_reset_token(user.email)
    # Формуємо посилання для скидання пароля. FRONTEND_URL має бути визначено в settings (наприклад, "https://your-app.com")
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    # Тут має бути виклик email-сервісу. Для прикладу виведемо посилання в консоль.
    print(f"Посилання для скидання пароля для {user.email}: {reset_link}")

    return {"message": "Якщо акаунт з таким email існує, на нього відправлено лист для скидання пароля."}

@router.post("/reset-password", status_code=200)
def reset_password(
    token: str = Query(..., description="Токен для скидання пароля"),
    reset_data: PasswordReset = Depends(),
    db: Session = Depends(get_db)
):
    """
    Ендпоінт для скидання пароля.
    Приймає токен (як query-параметр) та новий пароль (в тілі запиту).
    Якщо токен дійсний, оновлює пароль користувача.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[getattr(settings, "ALGORITHM", "HS256")])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недійсний токен")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недійсний токен")

    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Користувача не знайдено")

    # Хешуємо новий пароль та оновлюємо користувача
    hashed_password = utils.get_password_hash(reset_data.new_password)
    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)
    return {"message": "Пароль успішно скинуто."}
