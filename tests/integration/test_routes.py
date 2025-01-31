import sys
import os
import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.main import app
from app.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    """Фикстура для создания тестовой БД"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(test_db):
    """Фикстура для создания тестового клиента API"""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_read_users_me(client):
    """Тест ендпоинта /users/me"""
    response = client.get("/users/me", headers={"Authorization": "Bearer testtoken"})
    assert response.status_code == 401  # Потому что токен тестовый

def test_upload_avatar(client):
    """Тест загрузки аватара"""
    with open("tests/integration/test_avatar.jpg", "rb") as img:
        files = {"file": ("test_avatar.jpg", img, "image/jpeg")}
        response = client.post("/users/me/avatar", files=files, headers={"Authorization": "Bearer testtoken"})

    assert response.status_code in [401, 200]
