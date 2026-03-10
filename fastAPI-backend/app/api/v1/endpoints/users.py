from fastapi import APIRouter, HTTPException, Query

from app.services import user_service
from app.models.common import BlockUserRequest

router = APIRouter(prefix="/users", tags=["Users"])


# 🔹 Get total users count
@router.get("/count")
async def get_users_count():
    try:
        return await user_service.get_user_counts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Get all users
@router.get("/all")
async def get_all_users():
    try:
        return await user_service.get_all_users_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Search user by name
@router.get("/search")
async def search_user(
    name: str = Query(..., description="Search user by name")
):
    try:
        return await user_service.search_users(name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Block user
@router.post("/block")
async def block_user_api(data: BlockUserRequest):
    try:
        return await user_service.block_user(
            data.user_id,
            data.blocked_user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Unblock user
@router.post("/unblock")
async def unblock_user_api(data: BlockUserRequest):
    try:
        return await user_service.unblock_user(
            data.user_id,
            data.blocked_user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Get blocked users list
@router.get("/{user_id}/blocked-users")
async def blocked_list(user_id: str):
    try:
        return await user_service.get_blocked_users(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))