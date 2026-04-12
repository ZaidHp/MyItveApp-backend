import re
from typing import Optional, Dict
from datetime import datetime
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

    @field_validator('dob')
    @classmethod
    def validate_dob(cls, v):
        if not v:
            return v
        try:
            # Expected format from frontend: DD/MM/YYYY
            dob = datetime.strptime(v, '%d/%m/%Y')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 13:
                raise ValueError('Promoter must be at least 13 years old')
            if age > 100:
                raise ValueError('Invalid date of birth')
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date format must be DD/MM/YYYY')
            raise e
        return v

class PromoterEdu(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    img: Optional[str] = None

class PromoterProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    edu: Optional[PromoterEdu] = None
    languages: Optional[list[str]] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=72)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890 (space ke baad 10 digits)')
        return v

    @field_validator('dob')
    @classmethod
    def validate_dob(cls, v):
        if not v:
            return v
        try:
            # Expected format: DD/MM/YYYY
            dob = datetime.strptime(v, '%d/%m/%Y')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 13:
                raise ValueError('Promoter must be at least 13 years old')
            if age > 100:
                raise ValueError('Invalid date of birth')
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date format must be DD/MM/YYYY')
            raise e
        return v

class PromoterStatusUpdate(BaseModel):
    status: str = Field(..., pattern='^(active|inactive|deleted)$')
    reason: Optional[str] = None

class PromoterProfileResponse(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[list[str]] = []
    profile_image: Optional[str] = None
    edu: Optional[PromoterEdu] = None