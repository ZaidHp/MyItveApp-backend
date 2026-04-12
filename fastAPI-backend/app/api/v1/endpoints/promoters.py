import os
import aiofiles
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from app.models.promoter import PromoterSignup, PromoterProfileUpdate, PromoterProfileResponse
from app.models.common import UserResponse
from app.core.database import get_database
from app.core.security import hash_password
from app.core.config import settings
from app.api.deps import get_current_user
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()
db = get_database()
promoters_collection = db['Promoters']

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_promoter(user: PromoterSignup):
    # Check for existing email
    if await promoters_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered!"
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

    mapped_fields = ["name", "bio", "location", "edu", "languages"]
    
    for field in mapped_fields:
        if field in data_dict:
            if field == "edu" and data_dict[field] is not None:
                current_db_data = user.get("edu") or {}
                if data_dict["edu"].get("img") is None and current_db_data.get("img"):
                    data_dict["edu"]["img"] = current_db_data.get("img")
            update_fields[field] = data_dict[field]

    if not update_fields:
        return {"message": "No changes made"}

    update_fields["updated_at"] = datetime.now()

    await promoters_collection.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    return {"message": "Profile updated successfully!"}

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