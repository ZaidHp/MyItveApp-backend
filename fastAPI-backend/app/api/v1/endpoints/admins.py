from fastapi import APIRouter, HTTPException, status
from app.models.admin import AdminSignup
from app.models.common import UserResponse
from app.core.database import get_database
from app.core.security import hash_password
from app.core.config import settings
from datetime import datetime

router = APIRouter()
db = get_database()
admins_collection = db['Admins']

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(user: AdminSignup):
    # Verify Admin Code from Settings
    if user.admin_code != settings.ADMIN_SECRET_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin code. Access denied!"
        )

    # Check for existing email
    if await admins_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered!"
        )
    
    # Check for existing phone
    if await admins_collection.find_one({"phone": user.phone}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered!"
        )

    # Prepare user document
    user_document = {
        "email": user.email,
        "password": hash_password(user.password),
        "phone": user.phone,
        "name": user.name,
        "user_type": 'admin',
        "is_active": True,
        "created_at": datetime.now()
    }

    result = await admins_collection.insert_one(user_document)

    return UserResponse(
        id=str(result.inserted_id),
        email=user.email,
        user_type='admin',
        message="Admin registered successfully!"
    )