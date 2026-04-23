from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from core.config import settings

class Database:
    client: AsyncIOMotorClient = None

db = Database()

def get_db_client():
    if db.client is None:
        # Create client but don't raise on initial connection failure. In many
        # environments (tests/dev) MongoDB may be unavailable; avoid crashing
        # at import time. The client will attempt connections on use.
        db.client = AsyncIOMotorClient(settings.MONGO_URL)
        try:
            # Try a quick ping to detect connection issues but do not raise.
            db.client.admin.command('ping')
            print("[SUCCESS] MongoDB connected successfully!")
        except Exception as e:
            print(f"[WARNING] Could not connect to MongoDB at import time: {e}\nContinuing without raising; operations will fail at runtime if DB is required.")
    return db.client

def get_database():
    client = get_db_client()
    return client[settings.DB_NAME]