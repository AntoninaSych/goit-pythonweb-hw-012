import pytest
from app.utils import get_password_hash, verify_password

# Тестуємо функцію get_password_hash
def test_get_password_hash():
    password = "mypassword"
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert isinstance(hashed_password, str)

# Тестуємо функцію verify_password
def test_verify_password():
    password = "mypassword"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False
