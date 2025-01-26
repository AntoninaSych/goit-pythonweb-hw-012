# app/routers/users.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..config import settings
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(OAuth2PasswordBearer(tokenUrl="/auth/login"))],
)


@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(db: Session = Depends(get_db)):
    # Приклад функції для отримання інформації про поточного користувача
    # Реалізуйте відповідно до вашої логіки аутентифікації
    pass
