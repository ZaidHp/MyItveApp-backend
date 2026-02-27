from bson import ObjectId
from app.core.database import get_database


db = get_database()


# 🔹 Create Promoter
async def create_promoter(data: dict):
    data["role"] = "promoter"
    data["campaigns"] = []
    data["skills"] = []
    data["social_links"] = []

    result = await db.users.insert_one(data)
    return str(result.inserted_id)


# 🔹 Get Promoter by ID
async def get_promoter_by_id(id: str):
    promoter = await db.users.find_one({
        "_id": ObjectId(id),
        "role": "promoter"
    })

    if not promoter:
        return None

    return {
        "id": str(promoter["_id"]),
        "name": promoter.get("name"),
        "email": promoter.get("email"),
        "phone": promoter.get("phone"),
        "bio": promoter.get("bio"),
        "location": promoter.get("location"),
        "profile_image": promoter.get("profile_image"),
        "company": promoter.get("company"),
        "campaigns": promoter.get("campaigns", []),
        "work": promoter.get("work"),
        "skills": promoter.get("skills", []),
        "social_links": promoter.get("social_links", [])
    }


# 🔹 Get All Promoters
async def get_all_promoters():
    promoters = []

    async for promoter in db.users.find({"role": "promoter"}):
        promoters.append({
            "id": str(promoter["_id"]),
            "name": promoter.get("name"),
            "email": promoter.get("email"),
            "phone": promoter.get("phone"),
            "company": promoter.get("company"),
        })

    return promoters


# 🔹 Update Promoter
async def update_promoter(id: str, update_data: dict):
    await db.users.update_one(
        {"_id": ObjectId(id), "role": "promoter"},
        {"$set": update_data}
    )
    return True


# 🔹 Update Status
async def update_promoter_status(id: str, status: str, reason: str = None):
    update_data = {"status": status}

    if reason:
        update_data["reason"] = reason

    await db.users.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )

    return True