from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.database import get_raw_db
from app.schemas import CategoryCreate, CategoryResponse, AuthorCreate, AuthorResponse

router = APIRouter(tags=["Catalog"])


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Create a new book category."""
    try:
        row = await db.fetchrow(
            "INSERT INTO book_categories (category_name, description) VALUES ($1, $2) RETURNING category_id, category_name, description;",
            payload.category_name, payload.description
        )
        return CategoryResponse(**dict(row))
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail=f"Category '{payload.category_name}' already exists.")


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: asyncpg.Connection = Depends(get_raw_db)):
    """List all book categories."""
    rows = await db.fetch("SELECT category_id, category_name, description FROM book_categories ORDER BY category_id;")
    return [CategoryResponse(**dict(r)) for r in rows]


@router.post("/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(payload: AuthorCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Register a new author."""
    row = await db.fetchrow(
        "INSERT INTO authors (author_name) VALUES ($1) RETURNING author_id, author_name;",
        payload.author_name
    )
    return AuthorResponse(**dict(row))


@router.get("/authors/{author_id}", response_model=AuthorResponse)
async def get_author(author_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Get an author by ID."""
    row = await db.fetchrow("SELECT author_id, author_name FROM authors WHERE author_id = $1;", author_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Author {author_id} not found.")
    return AuthorResponse(**dict(row))
