from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.models.common import UserResponse
from app.core.database import get_database
from app.core.security import verify_password, create_access_token, create_refresh_token

router = APIRouter()
db = get_database()

students_col = db['Students']
admins_col = db['Admins']
schools_col = db['Schools']
promoters_col = db['Promoters']
donors_col = db['Donors']

class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Enter your Email or Username")
    password: str = Field(..., min_length=8, description="Enter your password")

@router.post("/login", response_model=UserResponse)
async def login_user(data: LoginRequest):
    
    identifier = data.username_or_email
    user = None
    matched_collection = None
    
    collections_map = [
        (students_col, "Student"),
        (admins_col, "Admin"),
        (schools_col, "School/College"),
        (promoters_col, "Promoter"),
        (donors_col, "donor")
    ]

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
        email=user["email"],
        user_type=user_type,
        message="Login successful!",
        access_token=access_token,
        refresh_token=refresh_token
    )