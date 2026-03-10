from fastapi import HTTPException
from bson import ObjectId
from app.core.database import get_database
from fastapi import HTTPException

db = get_database()

otp_store = {}

async def verify_update_otp(promoter_id: str, otp: str):
    stored = otp_store.get(promoter_id)
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP request found")

    if stored["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    update_data = stored["data"]

    result = await db["users"].update_one(
        {"_id": ObjectId(promoter_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promoter not found in DB")

    del otp_store[promoter_id]

    return {"message": "Promoter updated successfully"}