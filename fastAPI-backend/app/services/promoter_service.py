from bson import ObjectId
from bson.errors import InvalidId
from app.core.database import get_database
from fastapi import HTTPException, UploadFile
import os
from app.core.config import settings
from uuid import uuid4 
import aiofiles 
from datetime import datetime
from app.models.promoter import UpdatePromoter
import random
import time 
from app.services.whatsapp_service import send_whatsapp_otp
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = get_database()
COLLECTION_NAME = "Promoters"
ROLE_FIELD = "user_type"


# 🔹 Create Promoter
async def create_promoter(data: dict):
    data[ROLE_FIELD] = "promoter"
    data["campaigns"] = []
    data["skills"] = []
    data["social_links"] = []

    result = await db[COLLECTION_NAME].insert_one(data)
    promoter = await db[COLLECTION_NAME].find_one({"_id": result.inserted_id})
    return {
        "id": str(promoter["_id"]),
        "name": promoter.get("name"),
        "email": promoter.get("email"),
        "phone": promoter.get("phone"),
        "bio": promoter.get("bio"),
        "location": promoter.get("location"),
        "profile_image": promoter.get("profile_image"),
        "company": promoter.get("company"),
        "campaigns": promoter.get("campaigns", []),
        "work": promoter.get("work"),
        "skills": promoter.get("skills", []),
        "social_links": promoter.get("social_links", [])
    }


# 🔹 Get Promoter by ID
async def get_promoter_by_id(promoter_id: str):
    try:
        promoter = await db[COLLECTION_NAME].find_one({
            "_id": ObjectId(promoter_id),
            ROLE_FIELD: "promoter"
        })
    except InvalidId:
        return None

    if not promoter:
        return None

    return {
        "id": str(promoter["_id"]),
        "name": promoter.get("name"),
        "email": promoter.get("email"),
        "phone": promoter.get("phone"),
        "bio": promoter.get("bio"),
        "location": promoter.get("location"),
        "profile_image": promoter.get("profile_image"),
        "company": promoter.get("company"),
        "campaigns": promoter.get("campaigns", []),
        "work": promoter.get("work"),
        "skills": promoter.get("skills", []),
        "social_links": promoter.get("social_links", [])
    }


# 🔹 Get All Promoters
async def get_all_promoters():
    promoters = []

    async for promoter in db[COLLECTION_NAME].find({ROLE_FIELD: "promoter"}):
        promoters.append({
            "id": str(promoter["_id"]),
            "name": promoter.get("name"),
            "email": promoter.get("email"),
            "phone": promoter.get("phone"),
            "bio": promoter.get("bio"),
            "location": promoter.get("location"),
            "profile_image": promoter.get("profile_image"),
            "company": promoter.get("company"),
            "campaigns": promoter.get("campaigns", []),
            "work": promoter.get("work"),
            "skills": promoter.get("skills", []),
            "social_links": promoter.get("social_links", [])
        })

    return promoters

# 🔹 Update Promoter
otp_store = {}

async def update_promoter(promoter_id: str, update_data: UpdatePromoter):

    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    update_dict = update_data.model_dump(exclude_none=True)

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    # ✅ Handle password change
    if "new_password" in update_dict:

        # 1. old_password must be provided
        old_password = update_dict.pop("old_password", None)
        if not old_password:
            raise HTTPException(status_code=400, detail="old_password is required")

        # 2. Verify old password matches DB
        if not pwd_context.verify(old_password, promoter.get("password")):
            raise HTTPException(status_code=400, detail="Old password is incorrect")

        # 3. Hash new password and store it
        update_dict["password"] = pwd_context.hash(update_dict.pop("new_password"))

        # 4. Remove confirm_new_password — never save to DB
        update_dict.pop("confirm_new_password", None)
        update_dict.pop("old_password", None)

    # ✅ Handle OTP for email or phone change
    if "email" in update_dict or "phone" in update_dict:

        otp = str(random.randint(100000, 999999))

        otp_store[promoter_id] = {
            "otp": otp,
            "data": update_dict,
            "expires_at": time.time() + 300
        }

        phone_number = promoter.get("phone")
        await send_whatsapp_otp(phone_number, otp)

        return {"message": "OTP sent to WhatsApp. Please verify to complete update."}

    # ✅ Normal update — no sensitive fields
    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )

    return await get_promoter_by_id(promoter_id)
# 🔹 Verify OTP → apply pending update
async def verify_update_otp(promoter_id: str, otp: str):
    stored = otp_store.get(promoter_id)

    # 1. Does OTP exist?
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP found. Request a new one.")

    # 2. Has it expired?
    if time.time() > stored["expires_at"]:
        del otp_store[promoter_id]
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")

    # 3. Does it match?
    if stored["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # 4. ✅ Apply the update
    update_data = stored["data"]
    result = await db[COLLECTION_NAME].update_one(
        {"_id": ObjectId(promoter_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promoter not found")

    # 5. Delete OTP so it can't be reused
    del otp_store[promoter_id]

    return {"message": "Promoter updated successfully"}

# 🔹 Update Promoter Status
async def update_promoter_status(promoter_id: str, status: str, reason: str = None):
    update_data = {"status": status}
    if reason:
        update_data["reason"] = reason

    try:
        result = await db[COLLECTION_NAME].update_one(
            {"_id": ObjectId(promoter_id)},
            {"$set": update_data}
        )
    except InvalidId:
        return False

    return result.modified_count > 0


# 🔹 Upload Profile Image
async def upload_promoter_profile_image(file: UploadFile, promoter_id: str) -> str:
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID format.")

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    old_image = promoter.get("profile_image")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                print(f"Deleted old profile image: {old_image}")
            except Exception as e:
                print(f"Failed to delete old image {old_image}: {str(e)}")

    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": {"profile_image": unique_name, "updated_at": datetime.now()}}
    )

    return unique_name

# 🔹 Deactivate Promoter (Soft delete)
async def deactivate_promoter(promoter_id: str, reason: str = None):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    update_data = {"status": "inactive", "updated_at": datetime.now()}
    if reason:
        update_data["reason"] = reason

    result = await db[COLLECTION_NAME].update_one(
        {"_id": obj_id, ROLE_FIELD: "promoter"},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Promoter not found or already inactive")

    return await get_promoter_by_id(promoter_id)


# 🔹 Delete Promoter (Soft delete)
async def delete_promoter(promoter_id: str, reason: str = None):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    update_data = {"status": "deleted", "updated_at": datetime.now()}
    if reason:
        update_data["reason"] = reason

    result = await db[COLLECTION_NAME].update_one(
        {"_id": obj_id, ROLE_FIELD: "promoter"},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Promoter not found or already deleted")

    return {"message": "Promoter deleted successfully", "id": promoter_id}


# 🔹 Optional: Hard delete (permanent removal)
async def hard_delete_promoter(promoter_id: str):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    result = await db[COLLECTION_NAME].delete_one(
        {"_id": obj_id, ROLE_FIELD: "promoter"}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Promoter not found")

    return {"message": "Promoter permanently deleted", "id": promoter_id}