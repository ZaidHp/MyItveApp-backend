import re
from typing import Optional, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator

class PromoterSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: str = Field(..., pattern=r'^\+92 \d{10}$')
    name: str = Field(..., min_length=2, max_length=100)
    dob: Optional[str] = None
    gender: Optional[str] = None
    cnic: Optional[str] = None
    activationPin: Optional[str] = None
    location: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890 (space ke baad 10 digits)')
        return v

class PromoterEdu(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    img: Optional[str] = None

class PromoterProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    edu: Optional[PromoterEdu] = None
    languages: Optional[list[str]] = None

class PromoterProfileResponse(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[list[str]] = []
    profile_image: Optional[str] = None
    edu: Optional[PromoterEdu] = None