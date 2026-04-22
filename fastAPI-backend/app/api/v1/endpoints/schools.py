from fastapi import APIRouter, HTTPException, status, Form, File, UploadFile, Depends
from pydantic import ValidationError
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from fastapi.encoders import jsonable_encoder

from app.models.school import SchoolSignup, SchoolProfileResponse, SchoolProfileUpdate
from app.core.database import get_database
from app.core.security import hash_password
from app.api.deps import get_current_user
from app.utils.file_handlers import save_profile_image

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_school(school: SchoolSignup):
    db = get_database()
    schools_collection = db['Schools']
    students_collection = db['Students']
    promoters_collection = db['Promoters']
    admins_collection = db['Admins']

    # 1. Check for Duplicate Email or Username in Schools
    existing_school = await schools_collection.find_one({
        "$or": [{"email": school.email}, {"username": school.username}]
    })
    if existing_school:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Validation Error: School with this email or username already exists."
        )

    # 2. Check Email across ALL other user collections
    email_exists = (
        await students_collection.find_one({"email": school.email}) or
        await promoters_collection.find_one({"email": school.email}) or
        await admins_collection.find_one({"email": school.email})
    )
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in the system!"
        )

    # 3. Convert Pydantic Model to Dictionary & Remove confirmPassword
    school_dict = school.model_dump(exclude={"confirmPassword"})
    school_dict["password"] = hash_password(school_dict["password"])

    # 4. Inject Default Backend Values
    school_dict.update({
        "user_type": "school/college",
        "bio": "",
        "profilePicture": "",
        "badge": False,
        "stats": {"followers": 0, "students": 0, "followings": 0},
        "details": {
            "rank": 0,
            "principal": school.name,
            "totalStudentsEnrolled": 0,
            "alumni": 0
        },
        "facilities": [],
        "labs": [],
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    })

    # 5. Save to Database
    result = await schools_collection.insert_one(school_dict)

    return {
        "id": str(result.inserted_id),
        "email": school.email,
        "user_type": "school/college",
        "message": "School registered successfully"
    }

@router.get("/{schoolId}", response_model=SchoolProfileResponse)
async def get_school_profile(schoolId: str):
    db = get_database()
    try:
        obj_id = ObjectId(schoolId)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid School ID format")

    school_data = await db['Schools'].find_one({"_id": obj_id})
    if not school_data:
        raise HTTPException(status_code=404, detail="School not found")

    return SchoolProfileResponse(
        schoolId=str(school_data["_id"]),
        username=school_data.get("username", ""),
        instituteName=school_data.get("instituteName", ""),
        name=school_data.get("name", ""),
        email=school_data.get("email", ""),
        phone=school_data.get("phone", ""),
        cnic=school_data.get("cnic", ""),
        gender=school_data.get("gender", ""),
        bio=school_data.get("bio", ""),
        profilePicture=school_data.get("profilePicture", ""),
        badge=school_data.get("badge", False),
        stats=school_data.get("stats", {}),
        details=school_data.get("details", {}),
        facilities=school_data.get("facilities", []),
        labs=school_data.get("labs", []),
        location=school_data.get("locationName", "") 
    )

@router.put("/{schoolId}/profile", status_code=status.HTTP_200_OK)
async def update_school_profile(
    schoolId: str,
    name: str = Form(...),
    instituteName: str = Form(...),
    bio: str = Form(""),
    gender: str = Form(...),
    dateOfBirth: str = Form(...),
    username: str = Form(...),
    locationName: str = Form(...),
    profileImage: UploadFile = File(None),
    current_user=Depends(get_current_user)
):
    current_user_id = current_user.get("sub")
    if current_user_id != schoolId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You can only edit your own school profile."
        )

    db = get_database()
    try:
        obj_id = ObjectId(schoolId)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid School ID format.")

    try:
        validated_data = SchoolProfileUpdate(
            name=name, instituteName=instituteName, bio=bio,
            gender=gender, dateOfBirth=dateOfBirth, username=username,
            locationName=locationName
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=jsonable_encoder(e.errors()))

    existing_user = await db['Schools'].find_one({
        "_id": {"$ne": obj_id},
        "username": validated_data.username
    })
    
    if existing_user:
        raise HTTPException(status_code=409, detail="Username is already taken.")

    update_dict = validated_data.model_dump()
    update_dict["updatedAt"] = datetime.now(timezone.utc)

    if profileImage:
        image_url = await save_profile_image(profileImage)
        update_dict["profilePicture"] = image_url

    result = await db['Schools'].find_one_and_update(
        {"_id": obj_id},
        {"$set": update_dict},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="School not found.")

    return {
        "success": True,
        "message": "School profile updated successfully.",
        "data": {
            "schoolId": str(result["_id"]),
            "name": result.get("name"),
            "instituteName": result.get("instituteName"),
            "username": result.get("username"),
            "profilePicture": result.get("profilePicture", "")
        }
    }