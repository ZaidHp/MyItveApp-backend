from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
from app.models.donor import DonorSignup, DonorProfileResponse, DonorUpdateProfile, AchievementPatch, DeactivateAccountRequest
from app.models.common import UserResponse
from app.core.database import get_database
from app.core.security import hash_password
from app.api.deps import get_current_user

router = APIRouter()
db = get_database()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup_donor(donor: DonorSignup):
    # Cross-collection validation
    collections = ['Donors', 'Students', 'Schools', 'Admins', 'Promoters']
    for coll in collections:
        if await db[coll].find_one({"email": donor.email}):
            raise HTTPException(status_code=400, detail="Email already registered in the system!")
        
    if await db['Donors'].find_one({"username": donor.username}):
        raise HTTPException(status_code=400, detail="Username already exists!")

    donor_dict = donor.model_dump()
    donor_dict["password"] = hash_password(donor.password)
    donor_dict.update({
        "user_type": "donor",
        "followers_count": 0, "following_count": 0, "beneficiaries_count": 0,
        "total_amount_donated": 0.0, "donor_class": "Starter", "donor_rank": 0,
        "achievements": [], "is_active": True, "is_deleted": False,
        "created_at": datetime.now(timezone.utc)
    })

    result = await db["Donors"].insert_one(donor_dict)

    return UserResponse(
        id=str(result.inserted_id),
        email=donor.email,
        user_type="donor",
        message="Donor account created successfully!"
    )

@router.get("/profile", response_model=DonorProfileResponse)
async def get_donor_profile(current_user=Depends(get_current_user)):
    user = await db["Donors"].find_one({"email": current_user.get("email")})
    if not user:
        raise HTTPException(status_code=404, detail="Donor not found")
        
    return DonorProfileResponse(id=str(user["_id"]), **user)

@router.patch("/profile")
async def update_donor_profile(profile_data: DonorUpdateProfile, current_user=Depends(get_current_user)):
    update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")
        
    await db["Donors"].update_one({"email": current_user.get("email")}, {"$set": update_data})
    return {"message": "Profile updated successfully"}

@router.patch("/achievements")
async def update_donor_achievements(achievements_data: AchievementPatch, current_user=Depends(get_current_user)):
    achievements_list = [ach.model_dump() for ach in achievements_data.achievements]
    await db["Donors"].update_one({"email": current_user.get("email")}, {"$set": {"achievements": achievements_list}})
    return {"message": "Achievements updated successfully"}

@router.post("/account/deactivate")
async def deactivate_donor_account(payload: DeactivateAccountRequest = None, current_user=Depends(get_current_user)):
    await db["Donors"].update_one(
        {"email": current_user.get("email")},
        {"$set": {"is_active": False, "deactivated_at": datetime.now(timezone.utc), "deactivation_reason": payload.reason if payload else None}}
    )
    return {"message": "Account deactivated successfully"}