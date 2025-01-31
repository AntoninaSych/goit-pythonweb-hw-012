import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app import crud, models

# Налаштовуємо тестову базу даних SQLite (або іншу тестову БД)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Фікстура для створення тестової БД
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)  # Створення схем у тестовій БД
    session = TestingSessionLocal()
    try:
        yield session  # Повертає тестову сесію БД для тестів
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)  # Видалення таблиць після тесту

# Тест отримання користувача за email
def test_get_user_by_email(db: Session):
    # Створюємо тестового користувача
    user = models.User(email="test@example.com", hashed_password="hashedpassword")
    db.add(user)
    db.commit()

    # Отримуємо користувача за email
    retrieved_user = crud.get_user_by_email(db, "test@example.com")

    # Перевіряємо, чи користувач існує і має правильний email
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
