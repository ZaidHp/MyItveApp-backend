import os

class Settings:
    PROJECT_NAME: str = "User Registration API"
    VERSION: str = "1.0.0"
    
    # Database
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    DB_NAME: str = "ITVE_Database"

    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-super-secret-key")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    
    # Business Logic
    ADMIN_SECRET_CODE: str = os.getenv("ADMIN_SECRET_CODE", "ADMIN2024SECRET")
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png"}

settings = Settings()