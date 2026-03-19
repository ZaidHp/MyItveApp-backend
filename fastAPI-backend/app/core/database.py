from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

_client: AsyncIOMotorClient = None # type: ignore

def get_db_client():
    global _client
    if _client is None:
        try:
            _client = AsyncIOMotorClient(settings.MONGO_URL)
            _client.admin.command('ping')
            print("[SUCCESS] MongoDB connected successfully!")
        except ConnectionFailure as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            raise e
    return _client

def get_database():
    client = get_db_client()
    return client[settings.DB_NAME]