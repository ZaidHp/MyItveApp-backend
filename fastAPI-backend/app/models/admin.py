import re
from pydantic import BaseModel, EmailStr, Field, field_validator

class AdminSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: str = Field(..., pattern=r'^\+92 \d{10}$')
    name: str = Field(..., min_length=2, max_length=100)
    admin_code: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890 (space ke baad 10 digits)')
        return v