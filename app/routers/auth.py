from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
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
    # Automatically send verification email upon registration:
    send_verification_email_internal(new_user.email)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/send-verification-email")
def send_verification_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    1) This route can be used if user wants to re-send a verification email.
    2) Expects an 'email' in the body (form-data/json).
    """
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    send_verification_email_internal(user.email)
    return {"message": "Verification email has been sent."}


@router.get("/confirm-email", response_model=schemas.UserResponse)
def confirm_email(
    email: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Best Practice: Usually you'd expect a secure token rather than a plain email.
    For demonstration, we simply check the user by email and mark as verified.
    """
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user


def send_verification_email_internal(to_email: str):
    """
    Internal function that actually handles the SMTP sending of the email.
    We build a link to the confirm_email route with the user's email as a query param.
    In real apps, use a one-time token or JWT instead of direct email param.
    """
    subject = "Email Verification"
    link = f"http://localhost:8000/auth/confirm-email?email={to_email}"
    text = f"Please verify your email by clicking the following link: {link}"
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
