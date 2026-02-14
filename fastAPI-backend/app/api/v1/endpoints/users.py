from fastapi import APIRouter, HTTPException, status
from app.services import user_service

router = APIRouter()

@router.get("/count")
async def get_users_count():
    try:
        return await user_service.get_user_counts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all")
async def get_all_users():
    try:
        return await user_service.get_all_users_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))