from fastapi import APIRouter, status, Depends, UploadFile, File
from app.models.student import StudentSignup, UpdateStudent, StudentStatusUpdate
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
    # Extract ID from the JWT token
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