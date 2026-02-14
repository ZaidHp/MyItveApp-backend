from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from app.models.student import StudentSignup, StudentStatusUpdate, UpdateStudent
from app.models.common import UserResponse
from app.core.database import get_database
from app.core.security import hash_password
from app.api.deps import get_current_user
from app.services import student_service
from datetime import datetime
from bson import ObjectId

router = APIRouter()
db = get_database()
collection = db['Students']

@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(user: StudentSignup):
    if await collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email exists")
    if await collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username exists")

    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user.password)
    user_dict['is_active'] = True
    user_dict['user_type'] = 'Student'
    user_dict['created_at'] = datetime.now()
    
    result = await collection.insert_one(user_dict)
    
    return UserResponse(
        id=str(result.inserted_id),
        email=user.email,
        user_type='Student',
        message="Student registered successfully"
    )

@router.post("/upload_profile")
async def upload_profile(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    filename = await student_service.handle_profile_upload(file, current_user['sub'])
    return {"message": "Image uploaded", "filename": filename}

@router.put("/update")
async def update_profile(data: UpdateStudent, current_user=Depends(get_current_user)):
    updated_fields = await student_service.update_student_profile(current_user['sub'], data)
    if not updated_fields:
        return {"message": "No changes made"}
    return {"message": "Updated successfully", "fields": updated_fields}