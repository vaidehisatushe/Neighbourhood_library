from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[datetime] = None

    @validator('title')
    def trim_title(cls, v):
        v2 = v.strip() if isinstance(v, str) else v
        if not v2:
            raise ValueError('title must not be blank')
        return v2

class BookUpdate(BookCreate):
    id: int

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @validator('name')
    def trim_name(cls, v):
        v2 = v.strip() if isinstance(v, str) else v
        if not v2:
            raise ValueError('name must not be blank')
        return v2

    @validator('phone')
    def normalize_phone(cls, v):
        if v is None or v == '':
            return v
        digits = ''.join(ch for ch in v if ch.isdigit())
        if len(digits) < 7:
            raise ValueError('phone must contain at least 7 digits')
        return digits

class MemberUpdate(MemberCreate):
    id: int

class BorrowRequest(BaseModel):
    book_id: int
    member_id: int
    due_at: Optional[datetime] = None

class ReturnRequest(BaseModel):
    borrowing_id: int
