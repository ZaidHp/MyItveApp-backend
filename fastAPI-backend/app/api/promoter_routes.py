from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional
from app.services.whatsapp_service import send_whatsapp_otp
from app.services.promoter_service import (
    get_promoter_by_id,
    get_all_promoters,
    create_promoter,
    update_promoter,
    verify_update_otp,
    upload_promoter_profile_image,
    deactivate_promoter,
    delete_promoter,
    hard_delete_promoter
)

from app.models.promoter import (
    PromoterSignup,
    PromoterProfileResponse,
    UpdatePromoter
)

router = APIRouter(prefix="/promoters", tags=["Promoters"])


# 🔹 GET all promoters
@router.get("/", response_model=List[PromoterProfileResponse])
async def read_all_promoters():
    promoters = await get_all_promoters()
    return promoters


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

    promoter_dict = promoter.model_dump()  # ✅ Pydantic v2

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


# 🔹 Deactivate promoter (soft deactivate)
@router.patch("/{promoter_id}/deactivate", response_model=PromoterProfileResponse)
async def deactivate(
    promoter_id: str,
    reason: Optional[str] = Query(None)
):

    promoter = await deactivate_promoter(promoter_id, reason)

    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")

    return promoter


# 🔹 Soft delete promoter
@router.patch("/{promoter_id}/delete", response_model=dict)
async def soft_delete(
    promoter_id: str,
    reason: Optional[str] = Query(None)
):

    return await delete_promoter(promoter_id, reason)


# 🔹 Hard delete promoter (permanent)
@router.delete("/{promoter_id}/hard-delete", response_model=dict)
async def permanent_delete(promoter_id: str):

    return await hard_delete_promoter(promoter_id)


@router.post("/{promoter_id}/verify-otp")
async def verify_otp(promoter_id: str, otp: str):
    return await verify_update_otp(promoter_id, otp)