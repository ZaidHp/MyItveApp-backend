from fastapi import APIRouter, status, Depends, UploadFile, File
from app.models.student import StudentSignup, UpdateStudent, StudentStatusUpdate, StudentProfileResponse, StudentProfileUpdate
from app.models.common import UserResponse
from app.api.deps import get_current_user
from app.services import student_service

router = APIRouter()

# ==================== SIGNUP ====================
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: StudentSignup):
    result = await student_service.create_student(user)
    return UserResponse(
        id=result['id'],
        email=result['email'],
        user_type=result['user_type'],
        message="Student registered successfully!"
    )

# ==================== UPLOAD PROFILE ====================
@router.post("/upload_profile")
async def upload_profile(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    
    filename = await student_service.upload_profile_image(file, student_id)
    
    return {
        "message": "Image uploaded successfully", 
        "filename": filename,
        "url": f"/uploads/{filename}" # Optional: if you serve static files
    }

# ==================== UPDATE PROFILE ====================
@router.put("/update", status_code=status.HTTP_200_OK)
async def update_student(update_data: UpdateStudent, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    
    result = await student_service.update_student_profile(student_id, update_data)
    
    return {
        "message": result.get("message"),
        "student_id": student_id,
        "updated_fields": result.get("updated_fields")
    }

# ==================== UPDATE STATUS ====================
@router.patch("/status", status_code=status.HTTP_200_OK)
async def update_student_status(data: StudentStatusUpdate, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    
    result = await student_service.update_student_status(student_id, data)
    
    return {
        "message": f"Student status updated to {result['status']} successfully!",
        "student_id": student_id,
        "is_active": result['is_active']
    }

# ==================== GET PROFILE ====================
@router.get("/profile", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    
    profile_data = await student_service.get_student_profile(student_id)
    
    return profile_data

# ==================== UPDATE PROFILE DATA ====================
@router.put("/profile", status_code=status.HTTP_200_OK)
async def update_profile(profile_data: StudentProfileUpdate, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    
    result = await student_service.update_student_profile(student_id, profile_data)
    
    return result

@router.post("/upload_experience_image/{exp_type}", status_code=status.HTTP_200_OK)
async def upload_experience_image(
    exp_type: str, 
    file: UploadFile = File(...), 
    current_user=Depends(get_current_user)
):
    student_id = current_user.get("sub")
    
    filename = await student_service.upload_experience_image(file, student_id, exp_type)
    
    return {
        "message": f"{exp_type} image uploaded successfully", 
        "filename": filename
    }

@router.delete("/remove_profile_image", status_code=status.HTTP_200_OK)
async def remove_profile_image(current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    result = await student_service.remove_profile_image(student_id)
    return result