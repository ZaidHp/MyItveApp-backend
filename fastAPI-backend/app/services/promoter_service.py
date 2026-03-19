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
from passlib.context import CryptContext
from app.services.otp_service import generate_and_store_otp, verify_otp
from app.core.email_utils import send_otp_email

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
    data["settings"] = {
        "seminar_invites": True,
        "mentions_and_comments": True,
        }

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


# 🔹 Update Promoter Status
async def update_promoter(promoter_id: str, update_data: UpdatePromoter):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    update_dict = update_data.model_dump(exclude_none=True)

    # ✅ Strip all password fields — password changes go through /change-password only
    for field in ("old_password", "new_password", "confirm_new_password", "password"):
        update_dict.pop(field, None)

    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": update_dict}
    )

    return await get_promoter_by_id(promoter_id)
# ── CHANGE PASSWORD ──────────────────────────────────────────────────────────
async def change_promoter_password(promoter_id: str, old_password: str, new_password: str, confirm_new_password: str):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id, ROLE_FIELD: "promoter"})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    if not pwd_context.verify(old_password, promoter.get("password")):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    if new_password != confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    if old_password == new_password:
        raise HTTPException(status_code=400, detail="New password must differ from old password")

    hashed = pwd_context.hash(new_password)

    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": {"password": hashed, "updated_at": datetime.now()}}
    )

    return {"message": "Password changed successfully"}

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


# ── CHANGE EMAIL — Step 1 ────────────────────────────────────────────────────
async def request_email_change_otp(promoter_id: str, new_email: str):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id, ROLE_FIELD: "promoter"})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    if promoter.get("email") == new_email:
        raise HTTPException(status_code=400, detail="New email is the same as the current email")

    existing = await db[COLLECTION_NAME].find_one({"email": new_email})
    if existing:
        raise HTTPException(status_code=409, detail="This email is already in use")

    otp = await generate_and_store_otp(user_id=promoter_id, purpose="change_email", new_value=new_email)
    await send_otp_email(to_email=new_email, otp=otp, purpose="change_email", new_value=new_email)

    return {"message": f"OTP sent to {new_email}. It expires in 10 minutes."}


# ── CHANGE EMAIL — Step 2 ────────────────────────────────────────────────────
async def verify_email_change_otp(promoter_id: str, otp_input: str):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    result = await verify_otp(user_id=promoter_id, purpose="change_email", otp_input=otp_input)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["reason"])

    new_email = result["new_value"]

    # Race condition guard
    existing = await db[COLLECTION_NAME].find_one({"email": new_email, "_id": {"$ne": obj_id}})
    if existing:
        raise HTTPException(status_code=409, detail="This email was taken by another account")

    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": {"email": new_email, "updated_at": datetime.now()}}
    )
    return {"message": "Email updated successfully", "email": new_email}


# ── CHANGE PHONE — Step 1 ────────────────────────────────────────────────────
async def request_phone_change_otp(promoter_id: str, new_phone: str):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id, ROLE_FIELD: "promoter"})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    if promoter.get("phone") == new_phone:
        raise HTTPException(status_code=400, detail="New phone is the same as the current phone")

    current_email = promoter.get("email")
    if not current_email:
        raise HTTPException(status_code=400, detail="No email on file to send OTP to")

    otp = await generate_and_store_otp(user_id=promoter_id, purpose="change_phone", new_value=new_phone)
    await send_otp_email(to_email=current_email, otp=otp, purpose="change_phone", new_value=new_phone)

    return {"message": "OTP sent to your registered email. It expires in 10 minutes."}


# ── CHANGE PHONE — Step 2 ────────────────────────────────────────────────────
async def verify_phone_change_otp(promoter_id: str, otp_input: str):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    result = await verify_otp(user_id=promoter_id, purpose="change_phone", otp_input=otp_input)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["reason"])

    new_phone = result["new_value"]

    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": {"phone": new_phone, "updated_at": datetime.now()}}
    )
    return {"message": "Phone number updated successfully", "phone": new_phone}

async def update_promoter_notification_settings(
    promoter_id: str,
    seminar_invites: bool | None,
    mentions_and_comments: bool | None
):
    try:
        obj_id = ObjectId(promoter_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid promoter ID")

    promoter = await db[COLLECTION_NAME].find_one({"_id": obj_id, ROLE_FIELD: "promoter"})
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    update_fields = {}

    if seminar_invites is not None:
        update_fields["settings.seminar_invites"] = seminar_invites
    if mentions_and_comments is not None:
        update_fields["settings.mentions_and_comments"] = mentions_and_comments

    if not update_fields:
        raise HTTPException(status_code=400, detail="No settings provided to update")

    update_fields["updated_at"] = datetime.now()

    await db[COLLECTION_NAME].update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    updated = await db[COLLECTION_NAME].find_one({"_id": obj_id})
    settings_data = updated.get("settings", {})

    return {
        "message": "Settings updated successfully",
        "settings": {
            "seminar_invites": settings_data.get("seminar_invites", True),
            "mentions_and_comments": settings_data.get("mentions_and_comments", True),
        }
    }