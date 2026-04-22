import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class Achievement(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    icon_url: str = Field(default="", max_length=500)
    date_earned: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DonorSignup(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: str
    name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.]+$")
    profile_image_url: Optional[str] = Field(default="", max_length=500)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        normalized = re.sub(r"[\s-]", "", v)
        if not re.fullmatch(r"^\+92\d{10}$", normalized):
            raise ValueError("Phone format must be +92XXXXXXXXXX (10 digits after +92).")
        return normalized

class DonorProfileResponse(BaseModel):
    id: str
    username: str
    name: str
    about: Optional[str] = ""
    followers_count: int = 0
    following_count: int = 0
    beneficiaries_count: int = 0
    total_amount_donated: float = 0.0
    donor_class: str = ""
    donor_rank: int = 0
    achievements: List[Achievement] = []
    profile_image_url: Optional[str] = ""

class DonorUpdateProfile(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    about: Optional[str] = Field(None, max_length=500)
    profile_image_url: Optional[str] = Field(None, max_length=500)

class AchievementPatch(BaseModel):
    achievements: List[Achievement] = Field(default_factory=list)

class DeactivateAccountRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000)