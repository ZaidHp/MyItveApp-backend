import random
import time
from app.core.database import get_database

db = get_database()
OTP_COLLECTION = "otp_store"


async def generate_and_store_otp(user_id: str, purpose: str, new_value: str) -> str:
    otp = str(random.randint(100000, 999999))
    expires_at = time.time() + 600  # 10 minutes

    await db[OTP_COLLECTION].update_one(
        {"user_id": user_id, "purpose": purpose},
        {
            "$set": {
                "otp": otp,
                "new_value": new_value,
                "expires_at": expires_at,
                "verified": False,
            }
        },
        upsert=True,
    )
    return otp


async def verify_otp(user_id: str, purpose: str, otp_input: str) -> dict:
    record = await db[OTP_COLLECTION].find_one(
        {"user_id": user_id, "purpose": purpose}
    )

    if not record:
        return {"valid": False, "reason": "No OTP found. Please request a new one."}

    if record.get("verified"):
        return {"valid": False, "reason": "OTP already used. Please request a new one."}

    if time.time() > record.get("expires_at", 0):
        await db[OTP_COLLECTION].delete_one({"user_id": user_id, "purpose": purpose})
        return {"valid": False, "reason": "OTP has expired. Please request a new one."}

    if record.get("otp") != otp_input:
        return {"valid": False, "reason": "Incorrect OTP. Please try again."}

    # Mark used immediately to prevent replay attacks
    await db[OTP_COLLECTION].update_one(
        {"user_id": user_id, "purpose": purpose},
        {"$set": {"verified": True}}
    )

    return {"valid": True, "new_value": record.get("new_value")}


async def cleanup_expired_otps():
    await db[OTP_COLLECTION].delete_many({"expires_at": {"$lt": time.time()}})