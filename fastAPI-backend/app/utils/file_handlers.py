import os
import uuid
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "uploads/profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  

async def save_profile_image(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image format. Only JPG, PNG, and WEBP are allowed.")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size too large. Maximum allowed size is 5MB.")

    ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    normalized_path = file_path.replace("\\", "/")
    return f"/{normalized_path}"