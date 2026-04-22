from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timezone
from app.models.hope import HopeCreate, HopeResponse
from app.core.database import get_database

router = APIRouter()

@router.post("/", response_model=HopeResponse, status_code=201)
async def create_hope(hope: HopeCreate):
    db = get_database()
    hope_dict = hope.model_dump(by_alias=True)
    hope_dict["created_at"] = datetime.now(timezone.utc)
    result = await db["Hopes"].insert_one(hope_dict)

    return HopeResponse(id=str(result.inserted_id), **hope_dict)

@router.get("/", response_model=List[HopeResponse])
async def get_all_hopes():
    db = get_database()
    hopes_list = []
    async for hope in db["Hopes"].find({}):
        hopes_list.append(HopeResponse(id=str(hope["_id"]), **hope))
    return hopes_list