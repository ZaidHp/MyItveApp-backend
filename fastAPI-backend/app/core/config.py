import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "User Registration API"
    VERSION: str = "1.0.0"
    
    # Database
    MONGO_URL: str = os.getenv("MONGO_URL")
    DB_NAME: str = "ITVE_Database"

    # Security
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS") or 7)
    
    # Business Logic
    ADMIN_SECRET_CODE: str = os.getenv("ADMIN_SECRET_CODE")
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png"}

settings = Settings()