from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    EMAIL_HOST: str
    EMAIL_PORT: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    ALLOWED_ORIGINS: List[str]
    REDIS_URL: str
    TEST_DATABASE_URL:str

    class Config:
        env_file = ".env"

settings = Settings()
