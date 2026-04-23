from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal


class StudentReportBase(BaseModel):
    message: str = Field(..., min_length=5, max_length=1000)

class StudentReportCreate(StudentReportBase):
    pass

class StudentReportRespond(BaseModel):
    id: int
    action: Literal["Resolved", "Bogused"]
    reply: Optional[str] = None

class StudentReportResponse(StudentReportBase):
    id: int
    image_url: Optional[str] = None
    status: Literal["Resolved", "Bogused", "No Response"] = "No Response"
    reply: str = ""
    responded_by: str = ""

class StudentReportRespondResponse(BaseModel):
    id: int
    action: Literal["Resolved", "Bogused"]
    reply: Optional[str] = None
    done_by: str
