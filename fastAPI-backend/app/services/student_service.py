import os
import aiofiles
from datetime import datetime
from uuid import uuid4
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status, UploadFile
from pymongo.collection import Collection
from datetime import date
from app.core.database import get_database
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.student import StudentSignup, UpdateStudent, StudentStatusUpdate
from app.services.otp_service import generate_and_store_otp, verify_otp
from app.core.email_utils import send_otp_email

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
    user_dict['settings'] = {
        "mentions_and_comments": True,
        "class_updates": True,
        "study_reminders": True,
        "seminar_invites": True,
    }
    user_dict['privacy'] = {
    "content_visibility": "public",
    "message_permission": "everyone",
}

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

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    old_image = student.get("profile_image")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                print(f"Deleted old profile image: {old_image}")
            except Exception as e:
                print(f"Failed to delete old image {old_image}: {str(e)}")

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {"profile_image": unique_name, "updated_at": datetime.now()}}
    )

    return unique_name


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

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg, jpeg, png allowed")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    current_exp = student.get(exp_type)
    
    if not isinstance(current_exp, dict):
        current_exp = {"name": "", "role": ""}
        
    old_image = current_exp.get("img")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                print(f"Deleted old {exp_type} image: {old_image}")
            except Exception as e:
                print(f"Failed to delete old image {old_image}: {str(e)}")

    current_exp["img"] = unique_name

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {exp_type: current_exp, "updated_at": datetime.now()}}
    )
    return unique_name

async def remove_profile_image(student_id: str) -> dict:
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID format.")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    old_image = student.get("profile_image")
    if old_image:
        old_image_path = os.path.join(settings.UPLOAD_DIR, old_image)
        if os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                print(f"Deleted profile image: {old_image}")
            except Exception as e:
                print(f"Failed to delete image {old_image}: {str(e)}")

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {"profile_image": None, "updated_at": datetime.now()}}
    )

    return {"message": "Profile picture removed successfully"}


SCHOLARSHIP_COL = "scholarships"
APPLICATION_COL = "scholarship_applications"


def convert_ids(doc: dict) -> dict:
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


# ── Scholarships ──────────────────────────────────────────────────────────────

async def create_scholarship(data: dict):
    result = await db[SCHOLARSHIP_COL].insert_one(data)
    scholarship = await db[SCHOLARSHIP_COL].find_one({"_id": result.inserted_id})
    return convert_ids(scholarship)


async def get_all_scholarships():
    cursor = db[SCHOLARSHIP_COL].find({"status": "open"})
    scholarships = []
    async for s in cursor:
        scholarships.append(convert_ids(s))
    return scholarships


async def get_scholarship_by_id(scholarship_id: str):
    try:
        scholarship = await db[SCHOLARSHIP_COL].find_one(
            {"_id": ObjectId(scholarship_id)}
        )
    except InvalidId:
        return None
    return convert_ids(scholarship) if scholarship else None


# ── Applications 

async def apply_for_scholarship(student: dict, data: dict):
    scholarship_id = data.get("scholarship_id")

    # ✅ Validate student exists and is actually a student
    try:
        obj_id = ObjectId(student["id"])
    except InvalidId:
        return {"error": "Invalid student ID"}

    student_doc = await students_collection.find_one({"_id": obj_id})
    if not student_doc:
        return {"error": "Student not found"}
    if student_doc.get("user_type") != "Student":
        return {"error": "Only students can apply for scholarships"}
    if not student_doc.get("is_active", False):
        return {"error": "Your account is inactive"}
    if student_doc.get("is_deleted", False):
        return {"error": "Your account has been deleted"}

    # ✅ Auto-fill name and email from DB instead of trusting user input
    data["name"] = student_doc.get("name")
    data["email"] = student_doc.get("email")

    # Check scholarship exists
    scholarship = await get_scholarship_by_id(scholarship_id)
    if not scholarship:
        return {"error": "Scholarship not found"}

    # Check if open
    if scholarship["status"] != "open":
        return {"error": "This scholarship is closed"}

    # Check deadline
    deadline = date.fromisoformat(scholarship["deadline"])
    if date.today() > deadline:
        return {"error": "Scholarship deadline has passed"}

    # Check GPA requirement
    if scholarship.get("min_gpa") and data["gpa"] < scholarship["min_gpa"]:
        return {"error": f"Minimum GPA required is {scholarship['min_gpa']}"}

    # Check major requirement
    if scholarship.get("major_required"):
        if data["major"].lower() != scholarship["major_required"].lower():
            return {"error": f"This scholarship is only for {scholarship['major_required']} majors"}

    # Check duplicate application
    existing = await db[APPLICATION_COL].find_one({
        "applied_by": student["id"],
        "scholarship_id": scholarship_id
    })
    if existing:
        return {"error": "You have already applied for this scholarship"}

    # Build application
    application = {
        **data,
        "applied_by": student["id"],
        "username": student_doc.get("username"),
        "applied_at": str(date.today()),
        "application_status": "pending"
    }

    result = await db[APPLICATION_COL].insert_one(application)
    application["_id"] = str(result.inserted_id)
    return application

# ── CHANGE EMAIL ───────────
async def request_student_email_change_otp(student_id: str, new_email: str):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.get("email") == new_email:
        raise HTTPException(status_code=400, detail="New email is the same as the current email")

    existing = await students_collection.find_one({"email": new_email})
    if existing:
        raise HTTPException(status_code=409, detail="This email is already in use")

    otp = await generate_and_store_otp(promoter_id=student_id, purpose="change_email", new_value=new_email)
    await send_otp_email(to_email=new_email, otp=otp, purpose="change_email", new_value=new_email)

    return {"message": f"OTP sent to {new_email}. It expires in 10 minutes."}


# ── CHANGE EMAIL — Step 2 ────────────────────────────────────────────────────
async def verify_student_email_change_otp(student_id: str, otp_input: str):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    result = await verify_otp(promoter_id=student_id, purpose="change_email", otp_input=otp_input)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["reason"])

    new_email = result["new_value"]

    existing = await students_collection.find_one({"email": new_email, "_id": {"$ne": obj_id}})
    if existing:
        raise HTTPException(status_code=409, detail="This email was taken by another account")

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {"email": new_email, "updated_at": datetime.now()}}
    )
    return {"message": "Email updated successfully", "email": new_email}


# ── CHANGE PHONE — Step 1 ────────────────────────────────────────────────────
async def request_student_phone_change_otp(student_id: str, new_phone: str):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.get("phone") == new_phone:
        raise HTTPException(status_code=400, detail="New phone is the same as the current phone")

    current_email = student.get("email")
    if not current_email:
        raise HTTPException(status_code=400, detail="No email on file to send OTP to")

    otp = await generate_and_store_otp(promoter_id=student_id, purpose="change_phone", new_value=new_phone)
    await send_otp_email(to_email=current_email, otp=otp, purpose="change_phone", new_value=new_phone)

    return {"message": "OTP sent to your registered email. It expires in 10 minutes."}


# ── CHANGE PHONE — Step 2 ────────────────────────────────────────────────────
async def verify_student_phone_change_otp(student_id: str, otp_input: str):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    result = await verify_otp(promoter_id=student_id, purpose="change_phone", otp_input=otp_input)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["reason"])

    new_phone = result["new_value"]

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {"phone": new_phone, "updated_at": datetime.now()}}
    )
    return {"message": "Phone number updated successfully", "phone": new_phone}


# ── CHANGE PASSWORD ───────────────────────────────────────────────────────────
async def change_student_password(student_id: str, old_password: str, new_password: str, confirm_new_password: str):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not verify_password(old_password, student.get("password")):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    if new_password != confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    if old_password == new_password:
        raise HTTPException(status_code=400, detail="New password must differ from old password")

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": {"password": hash_password(new_password), "updated_at": datetime.now()}}
    )
    return {"message": "Password changed successfully"}
async def update_student_notification_settings(
    student_id: str,
    mentions_and_comments: bool | None,
    class_updates: bool | None,
    study_reminders: bool | None,
    seminar_invites: bool | None
):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_fields = {}

    if mentions_and_comments is not None:
        update_fields["settings.mentions_and_comments"] = mentions_and_comments
    if class_updates is not None:
        update_fields["settings.class_updates"] = class_updates
    if study_reminders is not None:
        update_fields["settings.study_reminders"] = study_reminders
    if seminar_invites is not None:
        update_fields["settings.seminar_invites"] = seminar_invites

    if not update_fields:
        raise HTTPException(status_code=400, detail="No settings provided to update")

    update_fields["updated_at"] = datetime.now()

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    updated = await students_collection.find_one({"_id": obj_id})
    settings_data = updated.get("settings", {})

    return {
        "message": "Settings updated successfully",
        "settings": {
            "mentions_and_comments": settings_data.get("mentions_and_comments", True),
            "class_updates": settings_data.get("class_updates", True),
            "study_reminders": settings_data.get("study_reminders", True),
            "seminar_invites": settings_data.get("seminar_invites", True),
        }
    }
async def update_student_privacy_settings(
    student_id: str,
    content_visibility: str | None,
    message_permission: str | None
):
    try:
        obj_id = ObjectId(student_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = await students_collection.find_one({"_id": obj_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_fields = {}

    if content_visibility is not None:
        if content_visibility not in ["public", "private"]:
            raise HTTPException(status_code=400, detail="content_visibility must be 'public' or 'private'")
        update_fields["privacy.content_visibility"] = content_visibility

    if message_permission is not None:
        if message_permission not in ["everyone", "friends_only"]:
            raise HTTPException(status_code=400, detail="message_permission must be 'everyone' or 'friends_only'")
        update_fields["privacy.message_permission"] = message_permission

    if not update_fields:
        raise HTTPException(status_code=400, detail="No privacy settings provided to update")

    update_fields["updated_at"] = datetime.now()

    await students_collection.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    updated = await students_collection.find_one({"_id": obj_id})
    privacy_data = updated.get("privacy", {})

    return {
        "message": "Privacy settings updated successfully",
        "privacy": {
            "content_visibility": privacy_data.get("content_visibility", "public"),
            "message_permission": privacy_data.get("message_permission", "everyone"),
        }
    }
