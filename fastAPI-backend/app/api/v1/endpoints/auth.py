from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from models.common import UserResponse
from core.database import get_database
from core.config import settings
from core.security import verify_password, create_access_token, create_refresh_token

router = APIRouter()
db = get_database()

students_col = db['Students']
admins_col = db['Admins']
schools_col = db['Schools']
promoters_col = db['Promoters']
workers_col = db['Workers']
teachers_col = db['Teachers']

class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Enter your Email or Username")
    password: str = Field(..., min_length=8, description="Enter your password")

@router.post("/login", response_model=UserResponse, summary="Login for all user types")
async def login_user(data: LoginRequest):
    
    identifier = data.username_or_email
    user = None
    matched_collection = None
    
    collections_map = [
        (students_col, "Student"),
        (admins_col, "Admin"),
        (schools_col, "School/College"),
        (promoters_col, "Promoter"),
        (workers_col, "worker"),
        (teachers_col, "teacher")
    ]

    if data.username_or_email in (settings.ADMIN_USERNAME, settings.ADMIN_EMAIL) and data.password == settings.ADMIN_PASSWORD:
        user_type = "admin"
        return UserResponse(
            id=settings.ADMIN_ID,
            email=settings.ADMIN_EMAIL,
            user_type=user_type,
            message="Admin login successful!",
            access_token=create_access_token({"sub": settings.ADMIN_ID, "user_type": user_type, "email": settings.ADMIN_EMAIL}),
            refresh_token=create_refresh_token({"sub": settings.ADMIN_ID, "user_type": user_type, "email": settings.ADMIN_EMAIL})
        )

    for collection, role_name in collections_map:
        user_found = await collection.find_one({
            "$or": [
                {"email": identifier},
                {"username": identifier}
            ]
        })
        
        if user_found:
            user = user_found
            user_type = user.get("user_type", role_name)
            matched_collection = collection
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please check your username or email."
        )

    if not verify_password(data.password, user.get('password', '')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password!"
        )

    if user.get("is_deleted", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been permanently deleted."
        )

    if not user.get("is_active", True):
        await matched_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "is_active": True, 
                "status_reason": None,
                "updated_at": datetime.now()
            }}
        )
        print(f"Account {user.get('username', identifier)} was auto-reactivated upon login.")

    subject = {
        "sub": str(user["_id"]),
        "user_type": user_type,
        "email": user.get("email")
    }
    
    if "username" in user:
        subject["username"] = user["username"]

    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)

    return UserResponse(
        id=str(user["_id"]),
        email=user.get("email", ""),
        user_type=user_type,
        message="Login successful!",
        access_token=access_token,
        refresh_token=refresh_token
    )