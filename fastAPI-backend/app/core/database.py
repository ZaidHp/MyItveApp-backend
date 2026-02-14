from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()

def get_db_client():
    if db.client is None:
        try:
            db.client = AsyncIOMotorClient(settings.MONGO_URL)
            # Check connection
            db.client.admin.command('ping')
            print("[SUCCESS] MongoDB connected successfully!")
        except ConnectionFailure as e:
            print(f"[ERROR] MongoDB connection failed: {e}")
            raise e
    return db.client

def get_database():
    client = get_db_client()
    return client[settings.DB_NAME]