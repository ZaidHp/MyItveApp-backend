from app.core.database import get_database
from bson import ObjectId
from fastapi import HTTPException
from bson.errors import InvalidId

db = get_database()

admins_collection = db["Admins"]
students_collection = db["Students"]
schools_collection = db["Schools"]
promoters_collection = db["Promoters"]

collections = {
    "admin": admins_collection,
    "student": students_collection,
    "school": schools_collection,
    "promoter": promoters_collection
}


# -----------------------------
# Helper: Validate ObjectId
# -----------------------------
def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")


# -----------------------------
# Helper: Find user in any collection
# -----------------------------
async def find_user_by_id(user_id: str):

    obj_id = validate_object_id(user_id)

    for role, collection in collections.items():

        user = await collection.find_one({"_id": obj_id})

        if user:
            user["role"] = role
            return user, collection

    return None, None


# -----------------------------
# Get user counts
# -----------------------------
async def get_user_counts():

    counts = {}

    for role, collection in collections.items():
        counts[role] = await collection.count_documents({})

    total_users = sum(counts.values())

    return {
        "total_users": total_users,
        "admins": counts["admin"],
        "students": counts["student"],
        "schools_colleges": counts["school"],
        "promoters": counts["promoter"]
    }


# -----------------------------
# Get all users
# -----------------------------
async def get_all_users_list():

    all_users = []

    for role, collection in collections.items():

        cursor = collection.find({}, {"password": 0})

        async for user in cursor:

            user["_id"] = str(user["_id"])
            user["role"] = role

            all_users.append(user)

    return {
        "total_users": len(all_users),
        "users": all_users
    }


# -----------------------------
# Block user
# -----------------------------
async def block_user(user_id: str, blocked_user_id: str):

    if user_id == blocked_user_id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    user, user_collection = await find_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    blocked_user, _ = await find_user_by_id(blocked_user_id)

    if not blocked_user:
        raise HTTPException(status_code=404, detail="Blocked user not found")

    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$addToSet": {"blocked_users": ObjectId(blocked_user_id)}}
    )

    return {"message": "User blocked successfully"}


# -----------------------------
# Unblock user
# -----------------------------
async def unblock_user(user_id: str, blocked_user_id: str):

    user, user_collection = await find_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"blocked_users": ObjectId(blocked_user_id)}}
    )

    return {"message": "User unblocked successfully"}


# -----------------------------
# Get blocked users
# -----------------------------
async def get_blocked_users(user_id: str):

    user, _ = await find_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    blocked_ids = user.get("blocked_users", [])

    blocked_users = []

    for blocked_id in blocked_ids:

        blocked_user, _ = await find_user_by_id(str(blocked_id))

        if blocked_user:
            blocked_user["_id"] = str(blocked_user["_id"])
            blocked_user.pop("password", None)

            blocked_users.append(blocked_user)

    return blocked_users


# -----------------------------
# Search users
# -----------------------------
from bson import ObjectId

def convert_objectids(doc):
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = convert_objectids(value)
        elif isinstance(value, list):
            doc[key] = [
                convert_objectids(i) if isinstance(i, dict)
                else str(i) if isinstance(i, ObjectId)
                else i
                for i in value
            ]
    return doc

async def search_users(name: str):
    users = []

    for role, collection in collections.items():
        cursor = collection.find(
            {"name": {"$regex": name, "$options": "i"}},
            {"password": 0}
        )

        async for user in cursor:
            user = convert_objectids(user)  # handles all nested ObjectIds
            user["role"] = role
            users.append(user)

    return users