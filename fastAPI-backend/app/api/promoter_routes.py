from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional
import re
from app.models.promoter import ChangePasswordRequest

from app.models.promoter import NotificationSettingsRequest
from app.services.promoter_service import update_promoter_notification_settings

from app.services.promoter_service import (
    get_promoter_by_id,
    get_all_promoters,
    create_promoter,
    update_promoter,
    upload_promoter_profile_image,
    deactivate_promoter,
    delete_promoter,
    hard_delete_promoter,
    request_email_change_otp,
    verify_email_change_otp,
    request_phone_change_otp,
    verify_phone_change_otp,
    change_promoter_password,
    
)

from app.models.promoter import (
    PromoterSignup,
    PromoterProfileResponse,
    UpdatePromoter
)

router = APIRouter(prefix="/promoters", tags=["Promoters"])


# ── Request Models ────────────────────────────────────────────────────────────

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr


class ChangePhoneRequest(BaseModel):
    new_phone: str

    @field_validator("new_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v)
        if not re.match(r"^\+?[0-9]{7,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


class VerifyOtpRequest(BaseModel):
    otp: str

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError("OTP must be exactly 6 digits")
        return v


# ── Existing Endpoints ────────────────────────────────────────────────────────

# 🔹 GET all promoters
@router.get("/", response_model=List[PromoterProfileResponse])
async def read_all_promoters():
    return await get_all_promoters()


# 🔹 GET single promoter
@router.get("/{promoter_id}", response_model=PromoterProfileResponse)
async def read_promoter(promoter_id: str):
    promoter = await get_promoter_by_id(promoter_id)
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")
    return promoter


# 🔹 POST create promoter
@router.post("/", response_model=PromoterProfileResponse)
async def create_new_promoter(promoter: PromoterSignup):
    promoter_dict = promoter.model_dump()
    promoter_id = await create_promoter(promoter_dict)
    return await get_promoter_by_id(promoter_id)


# 🔹 PATCH update promoter
@router.patch("/{promoter_id}", response_model=PromoterProfileResponse)
async def patch_promoter(promoter_id: str, promoter_update: UpdatePromoter):
    updated_promoter = await update_promoter(promoter_id, promoter_update)
    if not updated_promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")
    return updated_promoter


# 🔹 Upload profile image
@router.post("/{promoter_id}/upload-profile", response_model=dict)
async def upload_profile(promoter_id: str, file: UploadFile = File(...)):
    filename = await upload_promoter_profile_image(file, promoter_id)
    return {
        "profile_image": filename,
        "message": "Profile image uploaded successfully"
    }


# 🔹 Deactivate promoter
@router.patch("/{promoter_id}/deactivate", response_model=PromoterProfileResponse)
async def deactivate(promoter_id: str, reason: Optional[str] = Query(None)):
    promoter = await deactivate_promoter(promoter_id, reason)
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")
    return promoter


# 🔹 Soft delete promoter
@router.patch("/{promoter_id}/delete", response_model=dict)
async def soft_delete(promoter_id: str, reason: Optional[str] = Query(None)):
    return await delete_promoter(promoter_id, reason)


# 🔹 Hard delete promoter
@router.delete("/{promoter_id}/hard-delete", response_model=dict)
async def permanent_delete(promoter_id: str):
    return await hard_delete_promoter(promoter_id)

@router.post("/{promoter_id}/change-email/request-otp")
async def request_email_otp(promoter_id: str, body: ChangeEmailRequest):
    return await request_email_change_otp(promoter_id, str(body.new_email))


@router.post("/{promoter_id}/change-email/verify-otp")
async def verify_email_otp(promoter_id: str, body: VerifyOtpRequest):
    return await verify_email_change_otp(promoter_id, body.otp)


# ── Change Phone Endpoints 

@router.post("/{promoter_id}/change-phone/request-otp")
async def request_phone_otp(promoter_id: str, body: ChangePhoneRequest):
    return await request_phone_change_otp(promoter_id, body.new_phone)


@router.post("/{promoter_id}/change-phone/verify-otp")
async def verify_phone_otp(promoter_id: str, body: VerifyOtpRequest):
    return await verify_phone_change_otp(promoter_id, body.otp)


@router.post("/{promoter_id}/change-password")
async def change_password(promoter_id: str, body: ChangePasswordRequest):
    return await change_promoter_password(
        promoter_id=promoter_id,
        old_password=body.old_password,
        new_password=body.new_password,
        confirm_new_password=body.confirm_new_password,
    )
@router.patch("/{promoter_id}/settings/notifications")
async def update_notification_settings(promoter_id: str, body: NotificationSettingsRequest):
    return await update_promoter_notification_settings(
        promoter_id=promoter_id,
        seminar_invites=body.seminar_invites,
        mentions_and_comments=body.mentions_and_comments,
    )