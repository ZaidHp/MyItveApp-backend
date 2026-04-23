from pydantic import BaseModel
from dotenv import dotenv_values
from pathlib import Path

# Resolve .env path relative to this file (app/core/config.py → app/.env)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_env = dotenv_values(_ENV_PATH)


class Settings(BaseModel):
    PROJECT_NAME: str = "User Registration API"
    VERSION: str = "1.0.0"

    # Database
    MONGO_URL: str = _env.get("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME: str = _env.get("DB_NAME", "ITVE_Database")

    # Security
    SECRET_KEY: str = _env.get("JWT_SECRET_KEY", _env.get("SECRET_KEY", "change-me-secret"))
    ALGORITHM: str = _env.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = _env.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = _env.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = _env.get("CLOUDINARY_API_SECRET", "")

    # Admin credentials
    ADMIN_EMAIL: str = _env.get("email", "")
    ADMIN_PASSWORD: str = _env.get("password", "")
    ADMIN_PHONE: str = _env.get("phone", "")
    ADMIN_USERNAME: str = _env.get("username", "")
    ADMIN_SECRET_CODE: str = _env.get("admin_code", "")
    ADMIN_ID: str = _env.get("admin_id", "65f01234567890abcdef1234")

    # Business Logic
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png"}


settings = Settings()
