import re
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class SchoolCollegeSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: str = Field(..., pattern=r'^\+92 \d{10}$')
    institute_name: str = Field(..., min_length=2, max_length=200)
    address: str = Field(..., min_length=5)
    head_of_institute: Optional[str] = None
    institution_type: Literal["school", "college"] = Field(..., description="Type: school or college")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890 (space ke baad 10 digits)')
        return v