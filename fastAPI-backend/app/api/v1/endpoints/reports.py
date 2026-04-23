from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
import cloudinary
import cloudinary.uploader
from api.deps import get_current_user
from core.database import get_database
from core.config import settings
from typing import List, Optional
import time
from models.report import StudentReportRespond, StudentReportResponse, StudentReportRespondResponse


db = get_database()
reports_collection = db["StudentReports"]

router = APIRouter()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

@router.post("/report_student", response_model=StudentReportResponse, status_code=status.HTTP_201_CREATED)
async def report_student(
    message: str = Form(..., min_length=5, max_length=1000),
    image: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user)
):
    if current_user.get("user_type", "").lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit reports."
        )

    url = None
    if image:
        if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Supported formats are png, jpg, jpeg."
            )
        try:
            result = cloudinary.uploader.upload(image.file)
            url = result.get('secure_url')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading image to Cloudinary: {str(e)}"
            )

    report_id = int(time.time() * 1000)

    report_doc = {
        "id": report_id,
        "message": message,
        "image_url": url,
        "status": "No Response",
        "reply": "",
        "responded_by": ""
    }

    try:
        await reports_collection.insert_one(report_doc.copy())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving report: {str(e)}"
        )

    return StudentReportResponse(**report_doc)


from bson.objectid import ObjectId

@router.post("/respond_to_report", response_model=StudentReportRespondResponse)
async def respond_to_report(
    response_data: StudentReportRespond,
    current_user=Depends(get_current_user)
):
    user_type = current_user.get("user_type", "").lower()
    user_id = current_user.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    db_done_by = ""

    if user_type == "admin":
        admin = await db["Admins"].find_one({"_id": ObjectId(user_id)})
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found in database.")
        db_done_by = str(admin.get("_id"))

    elif user_type == "worker":
        worker = await db["Workers"].find_one({"_id": ObjectId(user_id)})
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found in database.")
        if worker.get("job_type") != "reports":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only reports workers can respond to reports.")
        db_done_by = str(worker.get("_id"))

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or authorized workers can respond to reports."
        )

    report = await reports_collection.find_one({"id": response_data.id})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found."
        )

    if report.get("status") != "No Response":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report has already been responded to."
        )

    final_done_by = db_done_by

    update_fields = {
        "status": response_data.action,
        "reply": response_data.reply if response_data.reply else "",
        "responded_by": final_done_by
    }

    await reports_collection.update_one(
        {"id": response_data.id},
        {"$set": update_fields}
    )

    return StudentReportRespondResponse(
        id=response_data.id,
        action=response_data.action,
        reply=response_data.reply,
        done_by=final_done_by
    )


@router.get("/get_reports", response_model=List[StudentReportResponse])
async def get_reports(
    current_user=Depends(get_current_user)
):
    user_type = current_user.get("user_type", "").lower()
    user_id = current_user.get("sub")
    
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    if user_type == "admin":
        admin = await db["Admins"].find_one({"_id": ObjectId(user_id)})
        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found in database.")
    elif user_type == "worker":
        worker = await db["Workers"].find_one({"_id": ObjectId(user_id)})
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found in database.")
        if worker.get("job_type") != "reports":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only reports workers can view reports.")
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or authorized workers can view reports."
        )

    cursor = reports_collection.find({})
    reports = await cursor.to_list(length=None)
    
    return [StudentReportResponse(**r) for r in reports]
