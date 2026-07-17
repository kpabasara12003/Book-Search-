from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum


# Enums

class CopyStatus(str, Enum):
    available = "available"
    borrowed  = "borrowed"
    lost      = "lost"
    damaged   = "damaged"

class FineStatus(str, Enum):
    pending = "pending"
    paid    = "paid"
    waived  = "waived"

# Category

class CategoryCreate(BaseModel):
    category_name: str = Field(..., max_length=150)
    description: Optional[str] = None

    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category name cannot be empty.")
        return v.strip()

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str
    description: Optional[str]

# Author

class AuthorCreate(BaseModel):
    author_name: str = Field(..., max_length=150)

    @field_validator('author_name')
    @classmethod
    def validate_author_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Author name cannot be empty.")
        return v.strip()

class AuthorResponse(BaseModel):
    author_id: int
    author_name: str


# Book

class BookCreate(BaseModel):
    title:            str           = Field(..., max_length=200)
    subtitle:         Optional[str] = Field(None, max_length=255)
    isbn:             Optional[str] = Field(None, max_length=20)
    publisher:        Optional[str] = Field(None, max_length=150)
    edition:          Optional[str] = Field(None, max_length=50)
    language:         Optional[str] = Field(None, max_length=50)
    publication_year: Optional[int] = Field(None, ge=0, le=2100)
    pages:            Optional[int] = Field(None, gt=0)
    summary:          Optional[str] = Field(None, description="Short descriptive text for semantic search")
    category_id:      int           = Field(..., gt=0)
    author_ids:       list[int]     = Field(..., min_length=1)

    @field_validator('title', 'summary')
    @classmethod
    def prevent_empty_strings(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v

class BookUpdate(BaseModel):
    title:            Optional[str] = Field(None, max_length=200)
    subtitle:         Optional[str] = Field(None, max_length=255)
    isbn:             Optional[str] = Field(None, max_length=20)
    publisher:        Optional[str] = Field(None, max_length=150)
    edition:          Optional[str] = Field(None, max_length=50)
    language:         Optional[str] = Field(None, max_length=50)
    publication_year: Optional[int] = Field(None, ge=0, le=2100)
    pages:            Optional[int] = Field(None, gt=0)
    summary:          Optional[str] = None
    category_id:      Optional[int] = Field(None, gt=0)

class BookResponse(BaseModel):
    book_id:          int
    title:            str
    subtitle:         Optional[str]
    isbn:             Optional[str]
    publisher:        Optional[str]
    edition:          Optional[str]
    language:         Optional[str]
    publication_year: Optional[int]
    pages:            Optional[int]
    summary:          Optional[str]
    category_id:      int
    category_name:    str
    total_copies:     int
    authors:          list[str]

class AddAuthorsToBookRequest(BaseModel):
    author_ids: list[int] = Field(..., min_length=1)


# Location Hierarchy

class FloorCreate(BaseModel):
    floor_name:  str           = Field(..., max_length=50)
    description: Optional[str] = None

class FloorResponse(BaseModel):
    floor_id:    int
    floor_name:  str
    description: Optional[str]

class SectionCreate(BaseModel):
    floor_id:     int = Field(..., gt=0)
    section_code: str = Field(..., max_length=10)
    section_name: Optional[str] = Field(None, max_length=100)

class SectionResponse(BaseModel):
    section_id:   int
    floor_id:     int
    section_code: str
    section_name: Optional[str]

class ShelfCreate(BaseModel):
    section_id: int = Field(..., gt=0)
    shelf_code: str = Field(..., max_length=10)

class ShelfResponse(BaseModel):
    shelf_id:   int
    section_id: int
    shelf_code: str

class ShelfRowCreate(BaseModel):
    shelf_id:     int = Field(..., gt=0)
    row_position: str = Field(..., max_length=20)
    category_id:  int = Field(..., gt=0)

class ShelfRowResponse(BaseModel):
    row_id:       int
    shelf_id:     int
    row_position: str
    category_id:  int


# Book Copies (Physical NFC items)

class CopyCreate(BaseModel):
    book_id: int = Field(..., gt=0)
    row_id:  int = Field(..., gt=0)
    nfc_id:  str = Field(..., max_length=100, description="Unique NFC/RFID tag ID on the physical book")

class CopyStatusUpdate(BaseModel):
    status: CopyStatus

class CopyLocationInfo(BaseModel):
    """Embedded location detail returned alongside a copy."""
    floor_name:   str
    section_code: str
    section_name: Optional[str]
    shelf_code:   str
    row_position: str

class CopyResponse(BaseModel):
    copy_id:  int
    book_id:  int
    nfc_id:   str
    status:   CopyStatus
    location: CopyLocationInfo


# Students

class StudentCreate(BaseModel):
    full_name:      str           = Field(..., max_length=150)
    email:          Optional[str] = Field(None, max_length=150)
    phone:          Optional[str] = Field(None, max_length=20)
    student_number: str           = Field(..., max_length=50)
    nfc_uid:        str           = Field(..., max_length=100)

class StudentResponse(BaseModel):
    student_id:     int
    full_name:      str
    email:          Optional[str]
    phone:          Optional[str]
    student_number: str
    active_borrows: int
    is_blocked:     bool
    created_at:     datetime

class StudentIdentifyRequest(BaseModel):
    nfc_uid: str = Field(..., description="NFC UID scanned from student ID card")


# Borrows

class BorrowRequest(BaseModel):
    student_nfc_uid: str = Field(..., description="Student card NFC scan")
    copy_nfc_id:     str = Field(..., description="Book NFC tag scan")

class ReturnRequest(BaseModel):
    copy_nfc_id: str = Field(..., description="NFC tag scan of the book being returned")

class BorrowResponse(BaseModel):
    borrow_id:   int
    copy_id:     int
    student_id:  int
    borrowed_at: datetime
    due_date:    date
    returned_at: Optional[datetime]
    fine_issued: bool


# Fines

class FineResponse(BaseModel):
    fine_id:    int
    borrow_id:  int
    student_id: int
    amount:     float
    status:     FineStatus
    created_at: datetime
