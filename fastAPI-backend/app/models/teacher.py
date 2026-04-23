import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Literal

# ==================== Generate Teacher Account Schema ====================
class GenerateTeacherAccount(BaseModel):
    course: Literal["english", "urdu", "maths"]
    username: str = Field(..., min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Password must have at least 1 special char, 1 uppercase, and 1 lowercase letter"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least 1 uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least 1 lowercase letter')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "course": "english",
                "username": "teacher_user",
                "password": "TeachPass@1"
            }
        }
    )
