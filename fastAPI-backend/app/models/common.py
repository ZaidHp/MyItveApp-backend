from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    id: str
    email: str
    user_type: str
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class BlockUserRequest(BaseModel):
    user_id: str
    blocked_user_id: str
    