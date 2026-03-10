from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "User Registration API"
    VERSION: str = "1.0.0"
    
    # Database
    MONGO_URL: str = Field(..., alias="MONGO_URL")
    DB_NAME: str = "ITVE_Database"

    # Security - We use Field(alias=...) to map the .env name to your Python variable name
    SECRET_KEY: str = Field(alias="JWT_SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Twilio Credentials
   
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str
    
    # Business Logic
    ADMIN_SECRET_CODE: str
    UPLOAD_DIR: str = "uploads"
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png"}

    # This tells Pydantic to automatically load from the .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()