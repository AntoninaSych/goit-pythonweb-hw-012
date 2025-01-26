from sqlalchemy.orm import Session
from typing import Optional, List
from . import models, schemas, utils

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = utils.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_contacts(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Contact]:
    return db.query(models.Contact).filter(models.Contact.owner_id == user_id).offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate, user_id: int) -> models.Contact:
    db_contact = models.Contact(**contact.dict(), owner_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact(db: Session, contact_id: int, user_id: int) -> Optional[models.Contact]:
    return db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.owner_id == user_id).first()

def update_avatar(db: Session, user: models.User, avatar_url: str) -> models.User:
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user
