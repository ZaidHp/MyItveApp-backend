import re
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# 🔹 Work / Experience Model
class ExperienceModel(BaseModel):
    name: str
    role: str
    img: Optional[str] = None


# 🔹 Signup Model (POST) - Create Promoter
class PromoterSignup(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    cnic: str = Field(..., description="CNIC in 12345-1234567-1 format")
    gender: str = Field(..., pattern="^(male|female|other)$")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str
    activation_pin: str = Field(..., min_length=4, max_length=6)

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
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

    @field_validator('cnic')
    @classmethod
    def validate_cnic(cls, v):
        if not re.match(r'^\d{5}-\d{7}-\d{1}$', v):
            raise ValueError('CNIC format: 12345-1234567-1')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @field_validator('dob')
    @classmethod
    def validate_dob(cls, v):
        from datetime import date
        try:
            dob = date.fromisoformat(v)
        except ValueError:
            raise ValueError('DOB format: YYYY-MM-DD')
        if dob >= date.today():
            raise ValueError('DOB must be in the past')
        return v

    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


# 🔹 Update Promoter Model (PATCH) - no password fields, no email/phone (those have their own OTP endpoints)
class UpdatePromoter(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, min_length=10, max_length=500)
    gender: Optional[Literal["male", "female"]] = None
    date_of_birth: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    location: Optional[str] = Field(None, min_length=2)
    username: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')


# 🔹 Change Password Request — POST /{id}/change-password
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=72)
    confirm_new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least 1 alphabet')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v

    @model_validator(mode='after')
    def passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError('New passwords do not match')
        return self


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

class NotificationSettingsRequest(BaseModel):
    seminar_invites: Optional[bool] = None
    mentions_and_comments: Optional[bool] = None

    @model_validator(mode='after')
    def at_least_one(self):
        if self.seminar_invites is None and self.mentions_and_comments is None:
            raise ValueError("At least one setting must be provided")
        return self