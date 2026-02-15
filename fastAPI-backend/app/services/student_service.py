import os
from datetime import datetime
from uuid import uuid4
from bson import ObjectId
from fastapi import HTTPException, status, UploadFile
from pymongo.collection import Collection

from app.core.database import get_database
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.student import StudentSignup, UpdateStudent, StudentStatusUpdate

# Initialize Database
db = get_database()
students_collection: Collection = db['Students']

async def create_student(user: StudentSignup) -> dict:
    """
    Handles Student Registration: Checks uniqueness -> Hashes Password -> Saves to DB
    """
    # 1. Check if user already exists
    if await students_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already taken!")
    if await students_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered!")
    if await students_collection.find_one({"phone": user.phone}):
        raise HTTPException(status_code=400, detail="Phone number already registered!")

    # 2. Prepare Data
    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user.password)
    user_dict['is_active'] = True
    user_dict['user_type'] = 'Student'
    user_dict['created_at'] = datetime.now()
    user_dict['profile_image'] = None

    # 3. Insert into DB
    result = await students_collection.insert_one(user_dict)
    
    return {
        "id": str(result.inserted_id),
        "email": user.email,
        "user_type": "Student"
    }

async def upload_profile_image(file: UploadFile, student_id: str) -> str:
    """
    Validates file extension, saves to disk, updates DB.
    """
    # 1. Validate Extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    # 2. Create Upload Directory if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 3. Generate Unique Filename
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    # 4. Save File
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # 5. Update Database
    try:
        await students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"profile_image": unique_name}}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    return unique_name

async def update_student_profile(student_id: str, update_data: UpdateStudent) -> dict:
    """
    Handles Profile Update: Checks existence -> Validates Uniqueness -> Handles Password -> Updates DB
    """
    if not student_id:
        raise HTTPException(status_code=400, detail="Student ID invalid.")

    # 1. Fetch Current Student
    try:
        student = await students_collection.find_one({"_id": ObjectId(student_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    if not student:
        raise HTTPException(status_code=404, detail="Student not found!")

    # 2. Prepare Update Fields
    update_fields = {}
    
    # List of simple fields to map directly
    simple_fields = ["name", "bio", "gender", "date_of_birth", "location"]
    data_dict = update_data.model_dump()
    
    for field in simple_fields:
        if data_dict.get(field) is not None:
            update_fields[field] = data_dict[field]

    # 3. Uniqueness Checks (Username, Email, Phone)
    async def check_and_set_unique(field_name, value):
        if value is not None:
            # Check if value exists in ANY OTHER document
            existing = await students_collection.find_one({
                field_name: value, 
                "_id": {"$ne": ObjectId(student_id)}
            })
            if existing:
                raise HTTPException(status_code=400, detail=f"{field_name.capitalize()} already taken!")
            update_fields[field_name] = value

    await check_and_set_unique("username", update_data.username)
    await check_and_set_unique("email", update_data.email)
    await check_and_set_unique("phone", update_data.phone)

    # 4. Password Update Logic
    if update_data.old_password:
        # Verify old password
        if not verify_password(update_data.old_password, student["password"]):
            raise HTTPException(status_code=400, detail="Old password is incorrect!")
        
        # Confirm match (Double check, though Pydantic also checks this)
        if update_data.new_password != update_data.confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match!")
        
        # Hash new password
        update_fields["password"] = hash_password(update_data.new_password)

    # 5. Perform Update
    if not update_fields:
        return {"message": "No changes made", "updated_fields": []}

    update_fields["updated_at"] = datetime.now()

    await students_collection.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": update_fields}
    )

    return {
        "message": "Student profile updated successfully!",
        "updated_fields": list(update_fields.keys())
    }

async def update_student_status(student_id: str, data: StudentStatusUpdate) -> dict:
    """
    Toggles student Active/Inactive status
    """
    new_is_active = True if data.status == "active" else False

    try:
        result = await students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"is_active": new_is_active, "updated_at": datetime.now()}}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "status": data.status,
        "is_active": new_is_active
    }