from fastapi import APIRouter, status, Depends, UploadFile, File, HTTPException
from app.models.student import (
    StudentSignup, UpdateStudent, StudentStatusUpdate,
    StudentProfileResponse, StudentProfileUpdate,
    ScholarshipCreate, ScholarshipApplication,
       )    
from app.models.common import UserResponse
from app.api.deps import get_current_user
from app.services import student_service
from pydantic import BaseModel, EmailStr, field_validator
import re
from app.models.promoter import ChangePasswordRequest
from app.models.student import PrivacySettingsRequest
from app.services.student_service import update_student_privacy_settings
from app.models.student import NotificationSettingsRequest
from app.services.student_service import update_student_notification_settings


router = APIRouter()


# ── Request Models 

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr


class ChangePhoneRequest(BaseModel):
    new_phone: str

    @field_validator("new_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v)
        if not re.match(r"^\+92\s?\d{10}$", cleaned):
            raise ValueError("Phone format: +92 1234567890")
        return cleaned


class VerifyOtpRequest(BaseModel):
    otp: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError("OTP must be exactly 6 digits")
        return v


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
        "url": f"/uploads/{filename}"
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
    return await student_service.get_student_profile(student_id)


# ==================== UPDATE PROFILE DATA ====================
@router.put("/profile", status_code=status.HTTP_200_OK)
async def update_profile(profile_data: StudentProfileUpdate, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.update_student_profile(student_id, profile_data)


# ==================== UPLOAD EXPERIENCE IMAGE ====================
@router.post("/upload_experience_image/{exp_type}", status_code=status.HTTP_200_OK)
async def upload_experience_image(
    exp_type: str,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    student_id = current_user.get("sub")
    filename = await student_service.upload_experience_image(file, student_id, exp_type)
    return {"message": f"{exp_type} image uploaded successfully", "filename": filename}


# ==================== REMOVE PROFILE IMAGE ====================
@router.delete("/remove_profile_image", status_code=status.HTTP_200_OK)
async def remove_profile_image(current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.remove_profile_image(student_id)


# ==================== SCHOLARSHIPS ====================

@router.get("/scholarships")
async def list_scholarships():
    return await student_service.get_all_scholarships()


@router.get("/scholarships/{scholarship_id}")
async def scholarship_detail(scholarship_id: str):
    scholarship = await student_service.get_scholarship_by_id(scholarship_id)
    if not scholarship:
        raise HTTPException(status_code=404, detail="Scholarship not found")
    return scholarship


@router.post("/scholarships/apply")
async def apply(data: ScholarshipApplication, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    student = {"id": student_id, "username": current_user.get("username")}
    result = await student_service.apply_for_scholarship(student, data.dict())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Application submitted successfully", "application": result}


@router.get("/scholarships/my-applications")
async def my_applications(current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    apps = await student_service.get_my_applications(student_id)
    if not apps:
        return {"message": "No applications found", "applications": []}
    return {"applications": apps}


@router.post("/scholarships/create")
async def create_scholarship(data: ScholarshipCreate):
    result = await student_service.create_scholarship(data.dict())
    return {"message": "Scholarship created successfully", "scholarship": result}


# ==================== CHANGE EMAIL ====================

@router.post("/change-email/request-otp")
async def request_email_otp(body: ChangeEmailRequest, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.request_student_email_change_otp(student_id, str(body.new_email))


@router.post("/change-email/verify-otp")
async def verify_email_otp(body: VerifyOtpRequest, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.verify_student_email_change_otp(student_id, body.otp)


# ==================== CHANGE PHONE ====================

@router.post("/change-phone/request-otp")
async def request_phone_otp(body: ChangePhoneRequest, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.request_student_phone_change_otp(student_id, body.new_phone)


@router.post("/change-phone/verify-otp")
async def verify_phone_otp(body: VerifyOtpRequest, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.verify_student_phone_change_otp(student_id, body.otp)


# ==================== CHANGE PASSWORD ====================

@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, current_user=Depends(get_current_user)):
    student_id = current_user.get("sub")
    return await student_service.change_student_password(
        student_id=student_id,
        old_password=body.old_password,
        new_password=body.new_password,
        confirm_new_password=body.confirm_new_password,
    )

# add endpoint
@router.patch("/settings/notifications")
async def update_notification_settings(
    body: NotificationSettingsRequest,
    current_user=Depends(get_current_user)
):
    student_id = current_user.get("sub")
    return await update_student_notification_settings(
        student_id=student_id,
        mentions_and_comments=body.mentions_and_comments,
        class_updates=body.class_updates,
        study_reminders=body.study_reminders,
        seminar_invites=body.seminar_invites,
    )


@router.patch("/settings/privacy")
async def update_privacy_settings(
    body: PrivacySettingsRequest,
    current_user=Depends(get_current_user)
):
    student_id = current_user.get("sub")
    return await update_student_privacy_settings(
        student_id=student_id,
        content_visibility=body.content_visibility,
        message_permission=body.message_permission,
    )