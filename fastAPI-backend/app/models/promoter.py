import re
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class ExperienceModel(BaseModel):
    name: str
    role: str
    img: Optional[str] = None


# 🔹 Signup Model (POST)
class PromoterSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: str
    name: str = Field(..., min_length=2, max_length=100)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least 1 alphabet')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v


# 🔹 Response Model (GET)
class PromoterProfileResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: str

    bio: Optional[str] = None
    location: Optional[str] = None
    profile_image: Optional[str] = None

    company: Optional[str] = None
    campaigns: List[str] = Field(default_factory=list)

    work: Optional[ExperienceModel] = None

    skills: List[str] = Field(default_factory=list)
    social_links: List[str] = Field(default_factory=list)


# 🔹 Update Model (PUT/PATCH)
class PromoterProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

    company: Optional[str] = None
    work: Optional[ExperienceModel] = None

    skills: Optional[List[str]] = None
    social_links: Optional[List[str]] = None


# 🔹 Status Update (Admin)
class PromoterStatusUpdate(BaseModel):
    status: Literal["active", "inactive", "blocked"]
    reason: Optional[str] = None