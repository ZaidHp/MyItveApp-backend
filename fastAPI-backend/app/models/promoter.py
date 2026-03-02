import re
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

# 🔹 Work / Experience Model
class ExperienceModel(BaseModel):
    name: str
    role: str
    img: Optional[str] = None


# 🔹 Signup Model (POST) - Create Promoter
class PromoterSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: str
    name: str = Field(..., min_length=2, max_length=100)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # ✅ Accepts +92 1234567890 or +921234567890
        if not re.match(r'^\+92\s?\d{10}$', v):
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


# 🔹 Update Promoter Model (PATCH/PUT)
class UpdatePromoter(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, min_length=10, max_length=500)
    gender: Optional[Literal["male", "female"]] = None
    date_of_birth: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    location: Optional[str] = Field(None, min_length=2)
    username: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    old_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=72)
    confirm_new_password: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.match(r'^\+92\s?\d{10}$', v):
            raise ValueError('Phone format: +92 1234567890')
        return v

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v is None:
            return v
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least 1 alphabet')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v


# 🔹 Response Model (GET) - Promoter Profile
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

    class Config:
        # ✅ MongoDB ObjectId compatibility
        from_attributes = True


# 🔹 Profile Update Model (PATCH/PUT)
class PromoterProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

    company: Optional[str] = None
    work: Optional[ExperienceModel] = None

    skills: Optional[List[str]] = None
    social_links: Optional[List[str]] = None


# 🔹 Status Update (Admin Only)
class PromoterStatusUpdate(BaseModel):
    status: Literal["active", "inactive", "deleted"] = Field(
        ..., description="Set promoter status to 'active', 'inactive', or 'deleted'"
    )
    reason: Optional[str] = Field(
        None, description="Reason for deactivation or deletion"
    )