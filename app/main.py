from fastapi import FastAPI, Depends
from .database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from .config import settings
from fastapi_limiter.depends import RateLimiter

from .routers import auth, users, contacts


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Contacts API")

# Настройка CORS (разрешение запросов с других доменов)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Инициализация FastAPI-Limiter с Redis"""
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )
    await FastAPILimiter.init(redis_client)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(contacts.router)
