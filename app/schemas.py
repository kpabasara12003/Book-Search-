from pydantic import BaseModel, Field, field_validator
from typing import Optional

class BookCreate(BaseModel):
    title: str = Field(..., max_length=200, description="Main book title string")
    subtitle: Optional[str] = Field(None, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    publisher: Optional[str] = Field(None, max_length=150)
    edition: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=50)
    publication_year: Optional[int] = Field(None, ge=0, le=2100)
    pages: Optional[int] = Field(None, gt=0)
    summary: Optional[str] = Field(None, max_length=300, description="Short descriptive text for search")
    category_id: int = Field(..., gt=0)
    author_ids: list[int] = Field(..., min_length=1, description="List of associated author primary keys")

    @field_validator('title', 'summary')
    @classmethod
    def prevent_empty_strings(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Field cannot be empty or solely whitespace characters.")
        return value

class BookResponse(BaseModel):
    book_id: int
    title: str
    subtitle: Optional[str]
    isbn: Optional[str]
    publisher: Optional[str]
    edition: Optional[str]
    language: Optional[str]
    publication_year: Optional[int]
    pages: Optional[int]
    summary: Optional[str]
    category_id: int
    category_name: str
    authors: list[str]


class CategoryCreate(BaseModel):
    category_name: str = Field(..., max_length=150, description="Unique category name classification")
    description: Optional[str] = Field(None, description="Optional text description of the category")

    @field_validator('category_name')
    @classmethod
    def validate_category_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Category name cannot be empty or only whitespace.")
        return value.strip()

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str
    description: Optional[str]

class AuthorCreate(BaseModel):
    author_name: str = Field(..., max_length=150, description="Full name of the author")

    @field_validator('author_name')
    @classmethod
    def validate_author_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Author name cannot be empty or only whitespace.")
        return value.strip()

class AuthorResponse(BaseModel):
    author_id: int
    author_name: str

class AddAuthorsToBookRequest(BaseModel):
    author_ids: list[int] = Field(..., min_length=1, description="List of author primary keys to link to the book")

