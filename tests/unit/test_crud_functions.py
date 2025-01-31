import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app import crud, models, schemas, utils

# Настройка тестовой БД SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Фикстура для создания тестовой БД
@pytest.fixture(scope="function")
def db() -> Session:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# Тест: получение пользователя по токену
def test_get_user_by_token(db: Session):
    # Создаем пользователя с токеном
    user = models.User(email="token_user@example.com", hashed_password="hashed")
    # Предположим, что у модели User есть поле token
    user.token = "testtoken"
    db.add(user)
    db.commit()
    db.refresh(user)

    retrieved_user = crud.get_user_by_token(db, "testtoken")
    assert retrieved_user is not None
    assert retrieved_user.email == "token_user@example.com"

# Тест: получение пользователя по email
def test_get_user_by_email(db: Session):
    user = models.User(email="email_user@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    retrieved_user = crud.get_user_by_email(db, "email_user@example.com")
    assert retrieved_user is not None
    assert retrieved_user.email == "email_user@example.com"

# Тест: создание пользователя
def test_create_user(db: Session):
    user_in = schemas.UserCreate(email="new_user@example.com", password="secret")
    created_user = crud.create_user(db, user_in)
    assert created_user is not None
    assert created_user.email == "new_user@example.com"
    # Проверяем, что пароль был захеширован (не совпадает с исходным)
    assert created_user.hashed_password != "secret"
    # Можно дополнительно проверить работу функции хеширования, если нужно:
    assert utils.verify_password("secret", created_user.hashed_password)

# Тест: получение пользователя по id
def test_get_user(db: Session):
    user = models.User(email="get_user@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    retrieved_user = crud.get_user(db, user.id)
    assert retrieved_user is not None
    assert retrieved_user.email == "get_user@example.com"

# Тест: получение контактов для пользователя
def test_get_contacts(db: Session):
    # Создаем пользователя
    user = models.User(email="contacts_user@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Создаем несколько контактов, принадлежащих пользователю
    # Добавляем требуемое поле email в данные контакта
    contact_data = [
        {"name": "Contact 1", "phone": "111-111-1111", "email": "contact1@example.com"},
        {"name": "Contact 2", "phone": "222-222-2222", "email": "contact2@example.com"},
        {"name": "Contact 3", "phone": "333-333-3333", "email": "contact3@example.com"},
    ]
    for data in contact_data:
        contact_in = schemas.ContactCreate(**data)
        crud.create_contact(db, contact_in, user.id)

    contacts = crud.get_contacts(db, user.id)
    assert len(contacts) == len(contact_data)
    names = [contact.name for contact in contacts]
    for data in contact_data:
        assert data["name"] in names

# Тест: создание контакта
def test_create_contact(db: Session):
    # Создаем пользователя
    user = models.User(email="create_contact@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Добавляем требуемое поле email в данные контакта
    contact_data = {"name": "New Contact", "phone": "444-444-4444", "email": "newcontact@example.com"}
    contact_in = schemas.ContactCreate(**contact_data)
    created_contact = crud.create_contact(db, contact_in, user.id)
    assert created_contact is not None
    assert created_contact.name == "New Contact"
    # Проверяем, что владелец контакта соответствует id пользователя
    assert created_contact.owner_id == user.id

# Тест: получение конкретного контакта
def test_get_contact(db: Session):
    # Создаем пользователя и контакт
    user = models.User(email="get_contact@example.com", hashed_password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    # Добавляем требуемое поле email в данные контакта
    contact_data = {"name": "Specific Contact", "phone": "555-555-5555", "email": "specific@example.com"}
    contact_in = schemas.ContactCreate(**contact_data)
    created_contact = crud.create_contact(db, contact_in, user.id)

    retrieved_contact = crud.get_contact(db, created_contact.id, user.id)
    assert retrieved_contact is not None
    assert retrieved_contact.name == "Specific Contact"

# Тест: обновление аватара пользователя
def test_update_avatar(db: Session):
    user = models.User(email="avatar_user@example.com", hashed_password="hashed", avatar_url=None)
    db.add(user)
    db.commit()
    db.refresh(user)

    new_avatar_url = "https://example.com/avatar.png"
    updated_user = crud.update_avatar(db, user, new_avatar_url)
    assert updated_user is not None
    assert updated_user.avatar_url == new_avatar_url
