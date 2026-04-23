import cloudinary
import cloudinary.uploader
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status, UploadFile
from pymongo.collection import Collection

from core.database import get_database
from core.config import settings
from core.security import hash_password, verify_password

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)
from models.student import StudentSignup, UpdateStudent, StudentStatusUpdate

db = get_database()
students_collection: Collection = db['Students']

async def create_student(user: StudentSignup) -> dict:
    
    if await students_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken!")
    if await students_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered!")
    if await students_collection.find_one({"phone": user.phone}):
        raise HTTPException(status_code=400, detail="Phone number already registered!")

    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user.password)
    user_dict['is_active'] = True
    user_dict['user_type'] = 'Student'
    user_dict['created_at'] = datetime.now()
    user_dict['profile_image'] = None

    result = await students_collection.insert_one(user_dict)
    
    return {
        "id": str(result.inserted_id),
        "email": user.email,
        "user_type": "Student"
    }

async def upload_profile_image(file: UploadFile, student_id: str) -> str:
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if f".{ext}" not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="itve/profile_images",
            resource_type="image"
        )
        url = result.get("secure_url")
        public_id = result.get("public_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload to Cloudinary failed: {str(e)}")

    # Destroy old image from Cloudinary if exists
    old_public_id = student.get("profile_image_public_id")
    if old_public_id:
        try:
            cloudinary.uploader.destroy(old_public_id)
        except Exception:
            pass  # Non-critical: old image cleanup failure

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {
            "profile_image": url,
            "profile_image_public_id": public_id,
            "updated_at": datetime.now()
        }}
    )

    return url

async def update_student_profile(student_id: str, update_data: UpdateStudent) -> dict:

    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found!")

    update_fields = {}
    
    mapped_fields = [
        "name", "bio", "gender", "date_of_birth", "location", "school",
        "work", "edu", "interests", "skills", "programming_languages", "languages"
    ]
    
    data_dict = update_data.model_dump(exclude_unset=True)
    
    for field in mapped_fields:
        if field in data_dict:
            if field in ["work", "edu"] and data_dict[field] is not None:
                current_db_data = student.get(field) or {}
                
                if data_dict[field].get("img") is None and current_db_data.get("img"):
                    data_dict[field]["img"] = current_db_data.get("img")
                if data_dict[field].get("img_public_id") is None and current_db_data.get("img_public_id"):
                    data_dict[field]["img_public_id"] = current_db_data.get("img_public_id")
            
            update_fields[field] = data_dict[field]

    async def check_and_set_unique(field_name, value):
        if value is not None:
            existing = await students_collection.find_one({
                field_name: value, 
                "_id": {"$ne": obj_id}
            })
            if existing:
                raise HTTPException(status_code=400, detail=f"{field_name.capitalize()} already taken!")
            update_fields[field_name] = value

    if "username" in data_dict:
        await check_and_set_unique("username", data_dict["username"])
    if "email" in data_dict:
        await check_and_set_unique("email", data_dict["email"])
    if "phone" in data_dict:
        await check_and_set_unique("phone", data_dict["phone"])

    if data_dict.get("old_password"):
        if not verify_password(data_dict["old_password"], student["password"]):
            raise HTTPException(status_code=400, detail="Old password is incorrect!")
        
        update_fields["password"] = hash_password(data_dict["new_password"])

    if not update_fields:
        return {"message": "No changes made", "updated_fields": []}

    update_fields["updated_at"] = datetime.now()

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    return {
        "message": "Student profile updated successfully!",
        "updated_fields": list(update_fields.keys())
    }

async def get_student_profile(student_id: str) -> dict:

    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    student = await students_collection.find_one({"_id": obj_id})
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found!")

    work_data = student.get("work")
    edu_data = student.get("edu")

    profile_data = {
        "username": student.get("username", ""),
        "name": student.get("name", ""),
        "bio": student.get("bio"),
        "location": student.get("location"),
        "gender": student.get("gender", ""),
        "date_of_birth": student.get("date_of_birth", ""),
        "school": student.get("school", ""),               
        "profile_image": student.get("profile_image"),     
        
        "work": work_data if work_data else None,
        "edu": edu_data if edu_data else None,
        
        "interests": student.get("interests", []),
        "skills": student.get("skills", []),
        "programming_languages": student.get("programming_languages", []),
        "languages": student.get("languages", [])
    }
    
    return profile_data

async def update_student_status(student_id: str, data: StudentStatusUpdate) -> dict:
    new_is_active = True if data.status == "active" else False
    is_deleted = True if data.status == "deleted" else False

    update_doc = {
        "is_active": new_is_active,
        "is_deleted": is_deleted,
        "updated_at": datetime.now()
    }
    
    if data.reason:
        update_doc["status_reason"] = data.reason

    try:
        result = await students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": update_doc}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "status": data.status,
        "is_active": new_is_active,
        "is_deleted": is_deleted
    }
async def upload_experience_image(file: UploadFile, student_id: str, exp_type: str) -> str:

    if exp_type not in ["work", "edu"]:
        raise HTTPException(status_code=400, detail="Invalid experience type")

    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if f".{ext}" not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="itve/experience_images",
            resource_type="image"
        )
        url = result.get("secure_url")
        public_id = result.get("public_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload to Cloudinary failed: {str(e)}")

    current_exp = student.get(exp_type)
    
    if not isinstance(current_exp, dict):
        current_exp = {"name": "", "role": ""}
        
    # Destroy old image from Cloudinary if exists
    old_public_id = current_exp.get("img_public_id")
    if old_public_id:
        try:
            cloudinary.uploader.destroy(old_public_id)
        except Exception:
            pass  # Non-critical: old image cleanup failure

    current_exp["img"] = url
    current_exp["img_public_id"] = public_id

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {exp_type: current_exp, "updated_at": datetime.now()}}
    )
    return url

async def remove_profile_image(student_id: str) -> dict:
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Destroy image from Cloudinary if exists
    old_public_id = student.get("profile_image_public_id")
    if old_public_id:
        try:
            cloudinary.uploader.destroy(old_public_id)
        except Exception:
            pass  # Non-critical: old image cleanup failure

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {
            "profile_image": None,
            "profile_image_public_id": None,
            "updated_at": datetime.now()
        }}
    )

    return {"message": "Profile picture removed successfully"}