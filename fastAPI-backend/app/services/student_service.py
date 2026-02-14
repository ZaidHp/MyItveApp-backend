from bson import ObjectId
from fastapi import HTTPException, UploadFile
import os
from uuid import uuid4
from datetime import datetime

from app.core.database import get_database
from app.core.config import settings
from app.models.student import UpdateStudent
from app.core.security import verify_password, hash_password

db = get_database()
collection = db['Students']

async def handle_profile_upload(file: UploadFile, student_id: str):
    # Validate
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    # Save File
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update DB
    await collection.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"profile_image": unique_name}}
    )
    return unique_name

async def update_student_profile(student_id: str, data: UpdateStudent):
    student = await collection.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_fields = data.model_dump(exclude_unset=True, exclude={'old_password', 'new_password', 'confirm_new_password'})

    # Password Logic
    if data.old_password:
        if not verify_password(data.old_password, student["password"]):
            raise HTTPException(status_code=400, detail="Incorrect old password")
        update_fields["password"] = hash_password(data.new_password)

    if not update_fields:
        return None

    update_fields["updated_at"] = datetime.now()
    
    await collection.update_one({"_id": ObjectId(student_id)}, {"$set": update_fields})
    return list(update_fields.keys())