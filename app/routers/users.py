from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import cloudinary
import cloudinary.uploader

from ..database import get_db
from .. import crud, models, schemas
from ..config import settings

router = APIRouter(prefix="/users", tags=["users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    user = crud.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.post("/me/avatar", response_model=schemas.UserResponse)
def update_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image type")
    upload_result = cloudinary.uploader.upload(file.file)
    avatar_url = upload_result.get("secure_url")
    if not avatar_url:
        raise HTTPException(status_code=500, detail="Failed to upload image")
    updated_user = crud.update_avatar(db, current_user, avatar_url)
    return updated_user
