from fastapi import APIRouter, Depends, HTTPException, status
from api.deps import get_current_user
from core.database import get_database
from core.security import hash_password
from models.worker import AddWorker
from datetime import datetime

router = APIRouter()
db = get_database()
workers_collection = db["Workers"]

# ==================== Add Worker Endpoint ====================
@router.post("/add_worker", status_code=status.HTTP_201_CREATED)
async def add_worker(data: AddWorker, current_user=Depends(get_current_user)):
    """Add a new worker (Admin only)"""

    # Only admins can add workers
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add workers."
        )

    # Check username uniqueness in Workers collection
    existing_username = await workers_collection.find_one({"username": data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken by another worker!"
        )

    # Check CNIC uniqueness in Workers collection
    existing_cnic = await workers_collection.find_one({"cnic": data.cnic})
    if existing_cnic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNIC already registered by another worker!"
        )

    # Build worker document
    worker_document = {
        "name": data.name,
        "cnic": data.cnic,
        "job_type": data.job_type,
        "username": data.username,
        "password": hash_password(data.password),
        "user_type": "worker",
        "is_active": True,
        "created_at": datetime.now()
    }

    try:
        result = await workers_collection.insert_one(worker_document)
        return {
            "message": "Worker added successfully!",
            "worker_id": str(result.inserted_id),
            "username": data.username,
            "job_type": data.job_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add worker: {str(e)}"
        )
