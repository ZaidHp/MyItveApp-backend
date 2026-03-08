from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PromoCodeBase(BaseModel):
    code: str
    institution_id: Optional[str] = None  # null for general_public and donor
    promo_type: Literal["school", "college", "general_public", "donor"]
    class_level: Optional[str] = None  # KG, 1-10 for school OR PreMed, PreEng, etc. for college
    batch_year: Optional[str] = None  
    is_active: bool = True
    usage_count: int = 0


class PromoCodeCreate(BaseModel):
    promo_type: Literal["school", "college", "general_public", "donor"]
    class_level: Optional[str] = None


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    promo_type: str
    class_level: Optional[str] = None
    batch_year: Optional[str] = None
    is_active: bool
    message: str


class GenerateInstitutionCodesResponse(BaseModel):
    success: bool
    message: str
    institution_type: str
    initials: str
    batch_year: str
    total_generated: int
    already_existed: int
    generated_codes: list
    existing_codes: list
