from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas, crud
from ..config import settings
from jose import JWTError, jwt

router = APIRouter(prefix="/contacts", tags=["contacts"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(status_code=401, detail="Invalid credentials")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/", response_model=schemas.ContactResponse, status_code=201)
def create_contact(
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_contact(db, contact, current_user.id)

@router.get("/", response_model=List[schemas.ContactResponse])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_contacts(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{contact_id}", response_model=schemas.ContactResponse)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    contact = crud.get_contact(db, contact_id, current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Not found")
    return contact
