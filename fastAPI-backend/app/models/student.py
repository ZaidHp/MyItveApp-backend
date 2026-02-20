import re
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

class ExperienceModel(BaseModel):
    name: str
    role: str
    img: Optional[str] = None


class StudentSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    gender: Literal["male", "female"] = Field(...)
    date_of_birth: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Date format: YYYY-MM-DD")
    
    username: str = Field(..., min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')
    phone: str = Field(..., pattern=r'^\+92 \d{10}$')
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    promo_code: Optional[str] = None

    bio: Optional[str] = None
    school: Optional[str] = None
    location: Optional[str] = None
    edu: Optional[ExperienceModel] = None
    work: Optional[ExperienceModel] = None
    
    interests: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890 (space ke baad 10 digits)')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least 1 alphabet')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v):
        try:
            dob = datetime.strptime(v, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 10:
                raise ValueError('Student must be at least 10 years old')
            if age > 100:
                raise ValueError('Invalid date of birth')
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date format must be YYYY-MM-DD')
            raise e
        return v


class StudentLogin(BaseModel):
    username_or_email: str = Field(..., description="Username or email for login")
    password: str = Field(..., min_length=8)


class UpdateStudent(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, min_length=10, max_length=500)
    gender: Optional[Literal["male", "female"]] = None
    date_of_birth: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    location: Optional[str] = Field(None, min_length=2)
    username: Optional[str] = Field(None, min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')
    school: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+92 \d{10}$')

    old_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=72)
    confirm_new_password: Optional[str] = None

    @model_validator(mode='after')
    def validate_password_change(self):
        pwd_fields = [self.old_password, self.new_password, self.confirm_new_password]
        provided = [f for f in pwd_fields if f is not None]

        if len(provided) > 0 and len(provided) < 3:
            raise ValueError(
                'To change password, all three fields are required: old_password, new_password, confirm_new_password'
            )

        if len(provided) == 3:
            if self.new_password != self.confirm_new_password:
                raise ValueError('new_password and confirm_new_password do not match')
        return self

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least 1 alphabet')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least 1 number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least 1 special character')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.match(r'^\+92 \d{10}$', v):
            raise ValueError('Phone format: +92 1234567890 (space ke baad 10 digits)')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is None:
            return v
        try:
            dob = datetime.strptime(v, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 10:
                raise ValueError('Student must be at least 10 years old')
            if age > 100:
                raise ValueError('Invalid date of birth')
        except ValueError as e:
            if 'does not match format' in str(e):
                raise ValueError('Date format must be YYYY-MM-DD')
            raise e
        return v


class StudentProfileResponse(BaseModel):
    username: str
    name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None        
    date_of_birth: Optional[str] = None 
    school: Optional[str] = None       
    profile_image: Optional[str] = None
    
    work: Optional[ExperienceModel] = None
    edu: Optional[ExperienceModel] = None
    
    interests: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    
    work: Optional[ExperienceModel] = None
    edu: Optional[ExperienceModel] = None
    
    interests: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    programming_languages: Optional[List[str]] = None
    languages: Optional[List[str]] = None


class StudentStatusUpdate(BaseModel):
    status: Literal["active", "inactive"] = Field(..., description="Set student status to 'active' or 'inactive'")