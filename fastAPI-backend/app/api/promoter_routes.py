# app/api/promoter_routes.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.services.promoter_service import get_promoter_by_id, get_all_promoters
from app.models.promoter import PromoterProfileResponse

router = APIRouter(prefix="/promoters", tags=["Promoters"])

# GET all promoters
@router.get("/", response_model=List[PromoterProfileResponse])
async def read_all_promoters():
    promoters = await get_all_promoters()
    return promoters  # empty list is fine if no promoters

# GET single promoter by ID
@router.get("/{promoter_id}", response_model=PromoterProfileResponse)
async def read_promoter(promoter_id: str):
    promoter = await get_promoter_by_id(promoter_id)
    if not promoter:
        raise HTTPException(status_code=404, detail="Promoter not found")
    return promoter