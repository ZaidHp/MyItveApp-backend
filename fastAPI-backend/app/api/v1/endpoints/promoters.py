import os
import aiofiles
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_database
from app.core.security import hash_password, verify_password
from app.models.common import UserResponse
from app.models.promoter import (
    PromoterProfileResponse,
    PromoterProfileUpdate,
    PromoterSignup,
    PromoterStatusUpdate
)
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()
db = get_database()
promoters_collection = db['Promoters']
students_collection = db['Students']
admins_collection = db['Admins']
schools_collection = db['Schools']

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_promoter(user: PromoterSignup):
    # Check email across ALL user collections
    email_exists = (
        await promoters_collection.find_one({"email": user.email}) or
        await students_collection.find_one({"email": user.email}) or
        await admins_collection.find_one({"email": user.email}) or
        await schools_collection.find_one({"email": user.email})
    )
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in the system!"
        )
    
    # Check for existing phone
    if await promoters_collection.find_one({"phone": user.phone}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered!"
        )
        
    # Check for existing CNIC (ignoring empty strings)
    if user.cnic and str(user.cnic).strip():
        if await promoters_collection.find_one({"cnic": user.cnic}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNIC already registered!"
            )

    # Prepare user document
    user_document = {
        "email": user.email,
        "password": hash_password(user.password),
        "phone": user.phone,
        "name": user.name,
        "dob": user.dob,
        "gender": user.gender,
        "cnic": user.cnic,
        "activationPin": user.activationPin,
        "location": user.location,
        "user_type": 'promoter',
        "is_active": True,
        "created_at": datetime.now()
    }

    result = await promoters_collection.insert_one(user_document)

    return UserResponse(
        id=str(result.inserted_id),
        email=user.email,
        user_type='promoter',
        message="Promoter registered successfully!"
    )

@router.get("/profile", response_model=PromoterProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    user = await promoters_collection.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="Promoter not found!")

    edu_data = user.get("edu")

    return {
        "username": user.get("username", ""),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "bio": user.get("bio", ""),
        "location": user.get("location", ""),
        "dob": user.get("dob", ""),
        "gender": user.get("gender", ""),
        "languages": user.get("languages", []),
        "profile_image": user.get("profile_image"),
        "edu": edu_data if edu_data else None
    }

@router.put("/profile", status_code=status.HTTP_200_OK)
async def update_profile(profile_data: PromoterProfileUpdate, current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    user = await promoters_collection.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="Promoter not found!")

    update_fields = {}
    data_dict = profile_data.model_dump(exclude_unset=True)

    mapped_fields = ["name", "bio", "location", "edu", "languages", "dob", "gender", "email", "phone"]
    
    for field in mapped_fields:
        if field in data_dict:
            value = data_dict[field]
            
            if field == "edu" and value is not None:
                current_db_data = user.get("edu") or {}
                if value.get("img") is None and current_db_data.get("img"):
                    value["img"] = current_db_data.get("img")
            
            if field == "email" and value != user.get("email"):
                # Check email across ALL user collections
                email_exists = (
                    await promoters_collection.find_one({"email": value, "_id": {"$ne": obj_id}}) or
                    await students_collection.find_one({"email": value}) or
                    await admins_collection.find_one({"email": value}) or
                    await schools_collection.find_one({"email": value})
                )
                if email_exists:
                    raise HTTPException(status_code=400, detail="Email already registered in the system!")
            
            if field == "phone" and value != user.get("phone"):
                # Check phone across ALL user collections
                phone_exists = (
                    await promoters_collection.find_one({"phone": value, "_id": {"$ne": obj_id}}) or
                    await students_collection.find_one({"phone": value}) or
                    await admins_collection.find_one({"phone": value}) or
                    await schools_collection.find_one({"phone": value})
                )
                if phone_exists:
                    raise HTTPException(status_code=400, detail="Phone number already registered!")

            update_fields[field] = value

    if data_dict.get("old_password"):
        if not data_dict.get("new_password"):
            raise HTTPException(status_code=400, detail="New password is required to change password.")
        if not verify_password(data_dict["old_password"], user["password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect!")
        update_fields["password"] = hash_password(data_dict["new_password"])

    if not update_fields:
        return {"message": "No changes made"}

    update_fields["updated_at"] = datetime.now()

    await promoters_collection.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    return {"message": "Profile updated successfully!"}

@router.patch("/status", status_code=status.HTTP_200_OK)
async def update_status(data: PromoterStatusUpdate, current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    new_is_active = True if data.status == "active" else False
    is_deleted = True if data.status == "deleted" else False

    update_doc = {
        "is_active": new_is_active,
        "is_deleted": is_deleted,
        "updated_at": datetime.now()
    }
    
    if data.reason:
        update_doc["status_reason"] = data.reason

    result = await promoters_collection.update_one(
        {"_id": obj_id},
        {"$set": update_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Promoter not found")

    return {
        "message": f"Account successfully {data.status}d.",
        "status": data.status,
        "is_active": new_is_active,
        "is_deleted": is_deleted
    }

@router.post("/upload_experience_image/{exp_type}", status_code=status.HTTP_200_OK)
async def upload_experience_image(
    exp_type: str, 
    file: UploadFile = File(...), 
    current_user=Depends(get_current_user)
):
    if exp_type not in ["edu", "work"]:
        raise HTTPException(status_code=400, detail="Invalid experience type")

    user_id = current_user.get("sub")
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    user = await promoters_collection.find_one({"_id": obj_id})
    if not user:
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

    current_exp = user.get(exp_type)
    if not isinstance(current_exp, dict):
        current_exp = {"name": "", "role": ""}
        
    old_image = current_exp.get("img")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
            except Exception:
                pass

    current_exp["img"] = unique_name

    await promoters_collection.update_one(
        {"_id": obj_id},
        {"$set": {exp_type: current_exp, "updated_at": datetime.now()}}
    )
    return {
        "message": f"{exp_type} image uploaded successfully", 
        "filename": unique_name
    }

@router.post("/upload_profile", status_code=status.HTTP_200_OK)
async def upload_profile(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    user = await promoters_collection.find_one({"_id": obj_id})
    if not user:
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

    old_image = user.get("profile_image")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
            except Exception:
                pass

    await promoters_collection.update_one(
        {"_id": obj_id},
        {"$set": {"profile_image": unique_name, "updated_at": datetime.now()}}
    )

    return {
        "message": "Profile image uploaded successfully", 
        "filename": unique_name,
        "url": f"/uploads/{unique_name}"
    }

@router.delete("/remove_profile_image", status_code=status.HTTP_200_OK)
async def remove_profile_image(current_user=Depends(get_current_user)):
    user_id = current_user.get("sub")
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    user = await promoters_collection.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="Promoter not found")

    old_image = user.get("profile_image")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
            except Exception:
                pass

    await promoters_collection.update_one(
        {"_id": obj_id},
        {"$set": {"profile_image": None, "updated_at": datetime.now()}}
    )

    return {"message": "Profile picture removed successfully"}