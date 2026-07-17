from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.database import get_raw_db
from app.schemas import FloorCreate, FloorResponse, SectionCreate, SectionResponse, ShelfCreate, ShelfResponse, ShelfRowCreate, ShelfRowResponse

router = APIRouter(tags=["Library Location"])



@router.post("/floors", response_model=FloorResponse, status_code=status.HTTP_201_CREATED)
async def create_floor(payload: FloorCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: add a new library floor."""
    row = await db.fetchrow(
        "INSERT INTO library_floors (floor_name, description) VALUES ($1, $2) RETURNING floor_id, floor_name, description;",
        payload.floor_name, payload.description
    )
    return FloorResponse(**dict(row))


@router.get("/floors", response_model=list[FloorResponse])
async def list_floors(db: asyncpg.Connection = Depends(get_raw_db)):
    """List all library floors."""
    rows = await db.fetch("SELECT floor_id, floor_name, description FROM library_floors ORDER BY floor_id;")
    return [FloorResponse(**dict(r)) for r in rows]


@router.get("/floors/{floor_id}/sections", response_model=list[SectionResponse])
async def list_sections_on_floor(floor_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """List all sections on a given floor."""
    rows = await db.fetch(
        "SELECT section_id, floor_id, section_code, section_name FROM sections WHERE floor_id = $1 ORDER BY section_code;",
        floor_id
    )
    return [SectionResponse(**dict(r)) for r in rows]


@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(payload: SectionCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: add a section to a floor."""
    floor_exists = await db.fetchval("SELECT floor_id FROM library_floors WHERE floor_id = $1", payload.floor_id)
    if not floor_exists:
        raise HTTPException(status_code=400, detail=f"Floor {payload.floor_id} does not exist.")
    try:
        row = await db.fetchrow(
            "INSERT INTO sections (floor_id, section_code, section_name) VALUES ($1, $2, $3) RETURNING section_id, floor_id, section_code, section_name;",
            payload.floor_id, payload.section_code.upper(), payload.section_name
        )
        return SectionResponse(**dict(row))
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail=f"Section code '{payload.section_code}' already exists on floor {payload.floor_id}.")


@router.post("/shelves", response_model=ShelfResponse, status_code=status.HTTP_201_CREATED)
async def create_shelf(payload: ShelfCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: add a shelf to a section."""
    section_exists = await db.fetchval("SELECT section_id FROM sections WHERE section_id = $1", payload.section_id)
    if not section_exists:
        raise HTTPException(status_code=400, detail=f"Section {payload.section_id} does not exist.")
    try:
        row = await db.fetchrow(
            "INSERT INTO bookshelves (section_id, shelf_code) VALUES ($1, $2) RETURNING shelf_id, section_id, shelf_code;",
            payload.section_id, payload.shelf_code
        )
        return ShelfResponse(**dict(row))
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail=f"Shelf code '{payload.shelf_code}' already exists in section {payload.section_id}.")


@router.post("/shelf-rows", response_model=ShelfRowResponse, status_code=status.HTTP_201_CREATED)
async def create_shelf_row(payload: ShelfRowCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: add a row to a shelf. Each row maps to one book category."""
    shelf_exists = await db.fetchval("SELECT shelf_id FROM bookshelves WHERE shelf_id = $1", payload.shelf_id)
    if not shelf_exists:
        raise HTTPException(status_code=400, detail=f"Shelf {payload.shelf_id} does not exist.")
    category_exists = await db.fetchval("SELECT category_id FROM book_categories WHERE category_id = $1", payload.category_id)
    if not category_exists:
        raise HTTPException(status_code=400, detail=f"Category {payload.category_id} does not exist.")
    try:
        row = await db.fetchrow(
            "INSERT INTO shelf_rows (shelf_id, row_position, category_id) VALUES ($1, $2, $3) RETURNING row_id, shelf_id, row_position, category_id;",
            payload.shelf_id, payload.row_position, payload.category_id
        )
        return ShelfRowResponse(**dict(row))
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail=f"Row position '{payload.row_position}' already exists on shelf {payload.shelf_id}.")
