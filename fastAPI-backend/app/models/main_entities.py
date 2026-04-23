from typing import List, Optional, Literal
import re
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ==================== Add Main Domain Schema ====================
class AddMainDomain(BaseModel):
    main_domain_name: str = Field(..., min_length=2, max_length=100)

    @field_validator('main_domain_name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Domain name must be at least 2 characters long')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "main_domain_name": "Computer Science"
            }
        }
    )


# ==================== Add Main Course Schema ====================
class AddMainCourse(BaseModel):
    main_course_name: str = Field(..., min_length=2, max_length=100)
    main_domain_name: str = Field(..., min_length=2, max_length=100)

    @field_validator('main_course_name')
    @classmethod
    def validate_course_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Course name must be at least 2 characters long')
        return v

    @field_validator('main_domain_name')
    @classmethod
    def validate_domain_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Domain name must be at least 2 characters long')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "main_course_name": "Data Structures",
                "main_domain_name": "Computer Science"
            }
        }
    )


# ==================== Lesson Schema ====================
class Lesson(BaseModel):
    lesson_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=2, max_length=500)
    content: str = Field(..., min_length=2)

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Lesson description must be at least 2 characters long')
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Lesson content must be at least 2 characters long')
        return v


# ==================== Add SubCourse Schema ====================
class AddSubCourse(BaseModel):
    main_domain_name: str = Field(..., min_length=2, max_length=100)
    main_course_name: str = Field(..., min_length=2, max_length=100)
    subcourse_name: str = Field(..., min_length=2, max_length=200)
    percentage_of_main_course: int = Field(..., ge=0, le=100)
    campus: str = Field(..., min_length=2, max_length=200)
    course_level: Literal["Beginner", "Intermediate", "Advanced", "All Levels"]
    modules: int = Field(..., ge=1)
    per_week_hours: int = Field(..., ge=1)
    advertising_radius_km: int = Field(..., ge=1)
    introduction: str = Field(..., min_length=10)
    duration_weeks: int = Field(..., ge=1)
    total_lessons: int = Field(..., ge=1)
    total_quiz: int = Field(..., ge=0)
    total_tests: int = Field(..., ge=0)
    lessons: List[Lesson] = Field(..., min_length=1)
    status: Literal["draft", "published", "archived", "inactive"] = Field(default="draft")

    @field_validator('main_domain_name', 'main_course_name', 'subcourse_name', 'campus')
    @classmethod
    def validate_string_fields(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Field must be at least 2 characters long')
        return v

    @field_validator('introduction')
    @classmethod
    def validate_introduction(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError('Introduction must be at least 10 characters long')
        return v

    @model_validator(mode='after')
    def validate_lesson_count(self):
        # 1. Check for duplicate lesson numbers
        lesson_numbers = [lesson.lesson_number for lesson in self.lessons]
        if len(lesson_numbers) != len(set(lesson_numbers)):
            raise ValueError('Lesson numbers must be unique')

        # 2. Check lesson count matches total_lessons
        if len(self.lessons) != self.total_lessons:
            raise ValueError(
                f"Number of lessons ({len(self.lessons)}) must be equal to total_lessons ({self.total_lessons})"
            )
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "main_domain_name": "Computer Science",
                "main_course_name": "Web Development",
                "subcourse_name": "Frontend Basics",
                "percentage_of_main_course": 30,
                "campus": "Main Campus",
                "course_level": "Beginner",
                "modules": 5,
                "per_week_hours": 10,
                "advertising_radius_km": 50,
                "introduction": "This subcourse covers the fundamentals of frontend web development.",
                "duration_weeks": 8,
                "total_lessons": 2,
                "total_quiz": 3,
                "total_tests": 1,
                "lessons": [
                    {
                        "lesson_number": 1,
                        "description": "Introduction to Webdev",
                        "content": "In this lesson, we cover the basics of web development."
                    },
                    {
                        "lesson_number": 2,
                        "description": "HTML Basics",
                        "content": "This lesson covers HTML fundamentals."
                    }
                ],
                "status": "draft"
            }
        }
    )


# ==================== Add Launch Course Schema ====================
class AddLaunchCourse(BaseModel):
    main_domain_name: str = Field(..., min_length=2, max_length=100)
    main_course_name: str = Field(..., min_length=2, max_length=100)
    subcourse_name: str = Field(..., min_length=2, max_length=200)
    batch_name: str = Field(..., min_length=2, max_length=100)
    start_date: date
    end_date: date
    enrollment_deadline: date
    campus: str = Field(..., min_length=2, max_length=200)
    max_students: int = Field(..., ge=1)
    fee: int = Field(..., ge=0)
    schedule: str = Field(..., min_length=2, max_length=300)
    status: Literal["open", "closed", "completed", "cancelled"] = Field(default="open")

    @field_validator('main_domain_name', 'main_course_name', 'subcourse_name', 'batch_name', 'campus')
    @classmethod
    def validate_string_fields(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Field must be at least 2 characters long')
        return v

    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError('Schedule must be at least 2 characters long')
        # Expected format: "Day[/Day...] HH:MM-HH:MM"
        valid_days = {'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'}
        pattern = r'^([A-Za-z]{3}(?:/[A-Za-z]{3})*)\s+(\d{2}:\d{2})-(\d{2}:\d{2})$'
        match = re.match(pattern, v)
        if not match:
            raise ValueError(
                'Schedule must follow the format: "Day/Day HH:MM-HH:MM" '
                '(e.g. "Mon/Wed/Fri 10:00-12:00")'
            )
        # Validate day names
        days = match.group(1).split('/')
        for day in days:
            if day.capitalize() not in valid_days:
                raise ValueError(
                    f"Invalid day '{day}'. Valid days: Mon, Tue, Wed, Thu, Fri, Sat, Sun"
                )
        # Validate time range
        start_time = match.group(2)
        end_time = match.group(3)
        sh, sm = map(int, start_time.split(':'))
        eh, em = map(int, end_time.split(':'))
        if not (0 <= sh <= 23 and 0 <= sm <= 59):
            raise ValueError(f"Invalid start time '{start_time}'")
        if not (0 <= eh <= 23 and 0 <= em <= 59):
            raise ValueError(f"Invalid end time '{end_time}'")
        if (eh, em) <= (sh, sm):
            raise ValueError('End time must be after start time')
        return v

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError('end_date must be after start_date')
        if self.enrollment_deadline > self.start_date:
            raise ValueError('enrollment_deadline must be on or before start_date')
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "main_domain_name": "Computer Science",
                "main_course_name": "Web Development",
                "subcourse_name": "Frontend Basics",
                "batch_name": "Batch 2026-A",
                "start_date": "2026-04-01",
                "end_date": "2026-06-30",
                "enrollment_deadline": "2026-03-25",
                "campus": "Main Campus",
                "max_students": 30,
                "fee": 5000,
                "schedule": "Mon/Wed/Fri 10:00-12:00",
                "status": "open"
            }
        }
    )
