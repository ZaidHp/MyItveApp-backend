from fastapi import APIRouter, HTTPException, status
from app.models.student import StudentLogin
from app.models.common import UserResponse
from app.core.database import get_database
from app.core.security import verify_password, create_access_token, create_refresh_token

router = APIRouter()
db = get_database()
students_col = db['Students']

@router.post("/student/login", response_model=UserResponse)
async def login_student(data: StudentLogin):
    user = await students_col.find_one({
        "$or": [{"email": data.username_or_email}, {"username": data.username_or_email}]
    })
    
    if not user or not verify_password(data.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account inactive")

    subject = {"sub": str(user["_id"]), "user_type": "Student"}
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        user_type="Student",
        message="Login successful",
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject)
    )