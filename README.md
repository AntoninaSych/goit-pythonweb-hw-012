# Contacts API (goit-pythonweb-hw-10)

REST API для керування контактами з аутентифікацією та авторизацією користувачів. Реалізовано за допомогою FastAPI, PostgreSQL, Redis, Alembic та Cloudinary.

## Функціональність

1. **Аутентифікація та авторизація** через JWT.
2. **Доступ користувача лише до власних контактів**.
3. **Верифікація електронної пошти** при реєстрації.
4. **Обмеження кількості запитів** до маршруту `/users/me`.
5. **CORS** увімкнено для безпеки.
6. **Оновлення аватара** через Cloudinary.
7. **Docker Compose** для запуску всіх сервісів.

## Структура

```plaintext
goit-pythonweb-hw-10/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── ... (міграції)
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── config.py
│   ├── utils.py
│   ├── crud.py
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── contacts.py
│       └── users.py
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── wait-for-it.sh
├── .env
└── README.md
