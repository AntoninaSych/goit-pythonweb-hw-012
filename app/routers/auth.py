# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText

from ..database import get_db
from ..config import settings
from .. import schemas, crud, utils

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    new_user = crud.create_user(db, user)
    send_verification_email(new_user.email)  # Відправляємо лист із посиланням
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify", response_model=schemas.UserResponse)
def verify_email(email: str = Query(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user

def send_verification_email(to_email: str):
    subject = "Email Verification"
    link = f"http://localhost:8000/auth/verify?email={to_email}"
    text = f"Please verify your email by clicking the link: {link}"
    msg = MIMEText(text)
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = to_email
    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_USERNAME, to_email, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
