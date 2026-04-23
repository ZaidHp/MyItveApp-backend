from fastapi import APIRouter, Depends, HTTPException, status
from api.deps import get_current_user
from core.database import get_database
from models.main_entities import AddMainDomain, AddMainCourse, AddSubCourse, AddLaunchCourse
from datetime import datetime

router = APIRouter()
db = get_database()
main_domain_collection = db["MainDomain"]
main_course_collection = db["MainCourse"]
sub_course_collection = db["SubCourse"]
launch_course_collection = db["LaunchCourse"]


# ==================== Add Main Domain Endpoint ====================
@router.post("/add_main_domain", status_code=status.HTTP_201_CREATED)
async def add_main_domain(data: AddMainDomain, current_user=Depends(get_current_user)):
    """Add a new main domain (Admin only)"""

    # Only admins can add domains
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add main domains."
        )

    # Check name uniqueness (case-insensitive)
    existing = await main_domain_collection.find_one(
        {"main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A domain with this name already exists!"
        )

    # Build domain document
    domain_document = {
        "main_domain_name": data.main_domain_name,
        "created_at": datetime.now()
    }

    try:
        result = await main_domain_collection.insert_one(domain_document)
        return {
            "message": "Main domain added successfully!",
            "domain_id": str(result.inserted_id),
            "main_domain_name": data.main_domain_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add main domain: {str(e)}"
        )


# ==================== Add Main Course Endpoint ====================
@router.post("/add_main_course", status_code=status.HTTP_201_CREATED)
async def add_main_course(data: AddMainCourse, current_user=Depends(get_current_user)):
    """Add a new main course (Admin only)"""

    # Only admins can add courses
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add main courses."
        )

    # Verify the domain exists
    domain = await main_domain_collection.find_one(
        {"main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}}
    )
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Main domain '{data.main_domain_name}' does not exist! Please add the domain first."
        )

    # Check course name uniqueness within the same domain (case-insensitive)
    existing = await main_course_collection.find_one({
        "main_course_name": {"$regex": f"^{data.main_course_name}$", "$options": "i"},
        "main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A course with this name already exists in this domain!"
        )

    # Build course document
    course_document = {
        "main_course_name": data.main_course_name,
        "main_domain_name": data.main_domain_name,
        "created_at": datetime.now()
    }

    try:
        result = await main_course_collection.insert_one(course_document)
        return {
            "message": "Main course added successfully!",
            "course_id": str(result.inserted_id),
            "main_course_name": data.main_course_name,
            "main_domain_name": data.main_domain_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add main course: {str(e)}"
        )


# ==================== Add SubCourse Endpoint ====================
@router.post("/add_subcourse", status_code=status.HTTP_201_CREATED)
async def add_subcourse(data: AddSubCourse, current_user=Depends(get_current_user)):
    """Add a new subcourse (Admin only)"""

    # Only admins can add subcourses
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add subcourses."
        )

    # Verify the domain exists
    domain = await main_domain_collection.find_one(
        {"main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}}
    )
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Main domain '{data.main_domain_name}' does not exist! Please add the domain first."
        )

    # Verify the course exists under that domain
    course = await main_course_collection.find_one({
        "main_course_name": {"$regex": f"^{data.main_course_name}$", "$options": "i"},
        "main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}
    })
    if not course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Main course '{data.main_course_name}' does not exist under domain '{data.main_domain_name}'! Please add the course first."
        )

    # Check subcourse name uniqueness within the same course & domain
    existing = await sub_course_collection.find_one({
        "subcourse_name": {"$regex": f"^{data.subcourse_name}$", "$options": "i"},
        "main_course_name": {"$regex": f"^{data.main_course_name}$", "$options": "i"},
        "main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A subcourse with this name already exists under this course and domain!"
        )

    # Build subcourse document
    subcourse_document = {
        "main_domain_name": data.main_domain_name,
        "main_course_name": data.main_course_name,
        "subcourse_name": data.subcourse_name,
        "percentage_of_main_course": data.percentage_of_main_course,
        "campus": data.campus,
        "course_level": data.course_level,
        "modules": data.modules,
        "per_week_hours": data.per_week_hours,
        "advertising_radius_km": data.advertising_radius_km,
        "introduction": data.introduction,
        "duration_weeks": data.duration_weeks,
        "total_lessons": data.total_lessons,
        "total_quiz": data.total_quiz,
        "total_tests": data.total_tests,
        "lessons": [lesson.model_dump() for lesson in data.lessons],
        "status": data.status,
        "created_at": datetime.now()
    }

    try:
        result = await sub_course_collection.insert_one(subcourse_document)
        return {
            "message": "Subcourse added successfully!",
            "subcourse_id": str(result.inserted_id),
            "subcourse_name": data.subcourse_name,
            "main_course_name": data.main_course_name,
            "main_domain_name": data.main_domain_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add subcourse: {str(e)}"
        )


# ==================== Launch Course Endpoint ====================
@router.post("/launch_course", status_code=status.HTTP_201_CREATED)
async def launch_course(data: AddLaunchCourse, current_user=Depends(get_current_user)):
    """Launch a new course batch (Admin only)"""

    # Only admins can launch courses
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can launch courses."
        )

    # Verify the domain exists
    domain = await main_domain_collection.find_one(
        {"main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}}
    )
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Main domain '{data.main_domain_name}' does not exist!"
        )

    # Verify the course exists under that domain
    course = await main_course_collection.find_one({
        "main_course_name": {"$regex": f"^{data.main_course_name}$", "$options": "i"},
        "main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}
    })
    if not course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Main course '{data.main_course_name}' does not exist under domain '{data.main_domain_name}'!"
        )

    # Verify the subcourse exists under that course & domain
    subcourse = await sub_course_collection.find_one({
        "subcourse_name": {"$regex": f"^{data.subcourse_name}$", "$options": "i"},
        "main_course_name": {"$regex": f"^{data.main_course_name}$", "$options": "i"},
        "main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}
    })
    if not subcourse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subcourse '{data.subcourse_name}' does not exist under course '{data.main_course_name}'!"
        )

    # Check batch_name uniqueness within the same subcourse
    existing = await launch_course_collection.find_one({
        "batch_name": {"$regex": f"^{data.batch_name}$", "$options": "i"},
        "subcourse_name": {"$regex": f"^{data.subcourse_name}$", "$options": "i"},
        "main_course_name": {"$regex": f"^{data.main_course_name}$", "$options": "i"},
        "main_domain_name": {"$regex": f"^{data.main_domain_name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A batch with this name already exists for this subcourse!"
        )

    # Build launch course document
    launch_document = {
        "main_domain_name": data.main_domain_name,
        "main_course_name": data.main_course_name,
        "subcourse_name": data.subcourse_name,
        "batch_name": data.batch_name,
        "start_date": data.start_date.isoformat(),
        "end_date": data.end_date.isoformat(),
        "enrollment_deadline": data.enrollment_deadline.isoformat(),
        "campus": data.campus,
        "max_students": data.max_students,
        "fee": data.fee,
        "schedule": data.schedule,
        "status": data.status,
        "enrolled_students": 0,
        "created_at": datetime.now()
    }

    try:
        result = await launch_course_collection.insert_one(launch_document)
        return {
            "message": "Course launched successfully!",
            "launch_id": str(result.inserted_id),
            "batch_name": data.batch_name,
            "subcourse_name": data.subcourse_name,
            "main_course_name": data.main_course_name,
            "main_domain_name": data.main_domain_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch course: {str(e)}"
        )
