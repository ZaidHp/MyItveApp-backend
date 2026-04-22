from fastapi import APIRouter, HTTPException, status, Form, File, UploadFile, Depends
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional             
from app.core.database import get_database
from app.api.deps import get_current_user
from app.utils.file_handlers import save_profile_image
from app.models.post import format_number, format_date_custom, format_time_custom, CommentCreate

router = APIRouter()
db = get_database()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_post(
    content: str = Form(""),
    image: UploadFile = File(None),
    current_user=Depends(get_current_user)
):
    current_user_id = current_user.get("sub")
    
    # Check if the author is a school or student
    author = await db["Schools"].find_one({"_id": ObjectId(current_user_id)}) or await db["Students"].find_one({"_id": ObjectId(current_user_id)})
    if not author:
        raise HTTPException(status_code=404, detail="Author profile not found.")

    image_url = await save_profile_image(image) if image else ""
    now = datetime.now(timezone.utc)
    
    post_document = {
        "authorId": current_user_id,
        "authorName": author.get("name") or author.get("instituteName", "Unknown"),
        "authorUsername": author.get("username", "unknown"),
        "authorProfilePic": author.get("profilePicture", author.get("profile_image", "")),
        "content": content,
        "imageUrl": image_url,
        "likesCount": 0, "commentsCount": 0, "sharesCount": 0, "viewsCount": 0,
        "isEdited": False, "createdAt": now, "updatedAt": now
    }

    result = await db["Posts"].insert_one(post_document)
    return {"success": True, "message": "Post created.", "postId": str(result.inserted_id)}

@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_posts(page: int = 1, limit: int = 10, current_user=Depends(get_current_user)):
    skip = (page - 1) * limit
    cursor = db["Posts"].find().sort("createdAt", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(length=limit)
    total_posts = await db["Posts"].count_documents({})

    formatted_posts = []
    for post in posts:
        formatted_posts.append({
            "postId": str(post["_id"]),
            "authorName": post.get("authorName", ""),
            "content": post.get("content", ""),
            "imageUrl": post.get("imageUrl", ""),
            "likesCount": post.get("likesCount", 0),
            "commentsCount": post.get("commentsCount", 0),
            "formattedViews": format_number(post.get("viewsCount", 0)),
            "createdAtDate": format_date_custom(post["createdAt"]),
            "createdAtTime": format_time_custom(post["createdAt"])
        })

    return {"success": True, "data": formatted_posts, "pagination": {"total": total_posts}}

@router.post("/{postId}/like", status_code=status.HTTP_200_OK)
async def toggle_like(postId: str, current_user=Depends(get_current_user)):
    current_user_id = current_user.get("sub")
    obj_id = ObjectId(postId)
    
    existing_like = await db["Post_Likes"].find_one({"postId": postId, "userId": current_user_id})

    if existing_like:
        await db["Post_Likes"].delete_one({"_id": existing_like["_id"]})
        await db["Posts"].update_one({"_id": obj_id}, {"$inc": {"likesCount": -1}})
        return {"success": True, "message": "Post unliked."}
    else:
        await db["Post_Likes"].insert_one({"postId": postId, "userId": current_user_id, "createdAt": datetime.now(timezone.utc)})
        await db["Posts"].update_one({"_id": obj_id}, {"$inc": {"likesCount": 1}})
        return {"success": True, "message": "Post liked."}

@router.post("/{postId}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(postId: str, comment: CommentCreate, current_user=Depends(get_current_user)):
    current_user_id = current_user.get("sub")
    now = datetime.now(timezone.utc)
    
    comment_doc = {
        "postId": postId,
        "userId": current_user_id,
        "text": comment.text,
        "createdAt": now
    }
    
    await db["Post_Comments"].insert_one(comment_doc)
    await db["Posts"].update_one({"_id": ObjectId(postId)}, {"$inc": {"commentsCount": 1}})

    return {"success": True, "message": "Comment added."}