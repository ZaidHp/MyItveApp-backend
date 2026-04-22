from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

def format_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M".replace(".0M", "M")
    if num >= 1_000:
        return f"{num / 1_000:.1f}K".replace(".0K", "K")
    return str(num)

def format_date_custom(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y").replace("/0", "/")

def format_time_custom(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lower()

class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)