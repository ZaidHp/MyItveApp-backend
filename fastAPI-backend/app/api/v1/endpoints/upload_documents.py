from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
import cloudinary
import cloudinary.uploader
from api.deps import get_current_user
from core.database import get_database
from core.config import settings

db = get_database()
workers_collection = db["Workers"]

router = APIRouter()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

ALLOWED_IMAGE_TYPES = {"cnic": "cnic_image", "profile": "profile_image"}

@router.post("/upload_image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    worker_username: str = Form(...),
    image_type: str = Form(..., description="Type of image: 'cnic' or 'profile'"),
    image: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    # Only admins can upload worker images
    if current_user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload images of workers."
        )

    # Validate image_type
    image_type = image_type.strip().lower()
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image_type '{image_type}'. Must be one of: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"
        )

    field_name = ALLOWED_IMAGE_TYPES[image_type]

    # Upload the file to Cloudinary
    result = cloudinary.uploader.upload(image.file)
    url = result.get('secure_url')

    # Update the corresponding field in Workers collection
    db_result = await workers_collection.update_one(
        {"username": worker_username},
        {"$set": {field_name: url}}
    )

    if db_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Worker not found.")

    return {
        "message": f"{image_type.capitalize()} image uploaded successfully",
        "worker_username": worker_username,
        "image_type": image_type,
        "field_name": field_name,
        "image_url": url
    }
