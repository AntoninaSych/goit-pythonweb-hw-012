# app/main.py
from fastapi import FastAPI, Depends
from .routers import auth, users, contacts
from .database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from .config import settings
from fastapi_limiter.depends import RateLimiter

# Створення таблиць (не обов'язково, якщо ви використовуєте лише міграції Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts API")

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення до Redis для rate limiting
@app.on_event("startup")
async def startup():
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)

# Підключаємо маршрути
app.include_router(auth.router)
# Обмежуємо /users/me до 5 запитів на хвилину
app.include_router(
    users.router,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
app.include_router(contacts.router)
