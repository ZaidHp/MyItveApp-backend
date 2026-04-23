from fastapi import APIRouter, Depends, HTTPException, status
from api.deps import get_current_user
from core.database import get_database

from models.teacher import GenerateTeacherAccount
from core.security import hash_password
from bson import ObjectId
from datetime import datetime

router = APIRouter()
db = get_database()
teachers_collection = db["Teachers"]
workers_collection = db["Workers"]

# ==================== Generate Teacher Account Endpoint ====================
@router.post("/generate_teacher_account", status_code=status.HTTP_201_CREATED)
async def generate_teacher_account(data: GenerateTeacherAccount, current_user=Depends(get_current_user)):
    """Generate a teacher account (Admin or Courses-Worker only)"""

    user_type = current_user.get("user_type")

    if user_type == "admin":
        pass  # Admins are allowed
    elif user_type == "worker":
        # Verify this worker has job_type == "courses"
        worker_id = current_user.get("sub")
        try:
            worker = await workers_collection.find_one({"_id": ObjectId(worker_id)})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid worker ID format."
            )

        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found!"
            )

        if worker.get("job_type") != "courses":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workers with job type 'courses' can generate teacher accounts."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and courses-workers can generate teacher accounts."
        )

    # Check username uniqueness in Teachers collection
    existing_username = await teachers_collection.find_one({"username": data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken by another teacher!"
        )

    # Build teacher document
    teacher_document = {
        "course": data.course,
        "username": data.username,
        "password": hash_password(data.password),
        "user_type": "teacher",
        "is_active": True,
        "created_at": datetime.now()
    }

    try:
        result = await teachers_collection.insert_one(teacher_document)
        return {
            "message": "Teacher account created successfully!",
            "teacher_id": str(result.inserted_id),
            "username": data.username,
            "course": data.course
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create teacher account: {str(e)}"
        )
