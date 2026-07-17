from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.database import get_raw_db
from app.schemas import CopyCreate, CopyStatusUpdate, CopyResponse

router = APIRouter(prefix="/copies", tags=["Book Copies"])

_COPY_LOCATION_SQL = """
    SELECT
        bc.copy_id, bc.book_id, bc.nfc_id, bc.status,
        lf.floor_name, s.section_code, s.section_name,
        bs.shelf_code, sr.row_position
    FROM book_copies bc
    JOIN shelf_rows sr ON bc.row_id = sr.row_id
    JOIN bookshelves bs ON sr.shelf_id = bs.shelf_id
    JOIN sections s ON bs.section_id = s.section_id
    JOIN library_floors lf ON s.floor_id = lf.floor_id
"""

def _row_to_copy_response(r) -> CopyResponse:
    return CopyResponse(
        copy_id=r["copy_id"], book_id=r["book_id"], nfc_id=r["nfc_id"], status=r["status"],
        location={
            "floor_name": r["floor_name"], "section_code": r["section_code"],
            "section_name": r["section_name"], "shelf_code": r["shelf_code"],
            "row_position": r["row_position"]
        }
    )


@router.post("", response_model=CopyResponse, status_code=status.HTTP_201_CREATED)
async def register_copy(payload: CopyCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: register a new physical book copy by linking book_id, row_id, and NFC tag."""
    book_exists = await db.fetchval("SELECT book_id FROM books WHERE book_id = $1", payload.book_id)
    if not book_exists:
        raise HTTPException(status_code=400, detail=f"Book {payload.book_id} does not exist.")
    row_exists = await db.fetchval("SELECT row_id FROM shelf_rows WHERE row_id = $1", payload.row_id)
    if not row_exists:
        raise HTTPException(status_code=400, detail=f"Shelf row {payload.row_id} does not exist.")
    try:
        await db.execute(
            "INSERT INTO book_copies (book_id, row_id, nfc_id) VALUES ($1, $2, $3);",
            payload.book_id, payload.row_id, payload.nfc_id
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail=f"NFC tag '{payload.nfc_id}' is already registered to another copy.")

    row = await db.fetchrow(_COPY_LOCATION_SQL + " WHERE bc.nfc_id = $1", payload.nfc_id)
    return _row_to_copy_response(row)


@router.get("/nfc/{nfc_id}", response_model=CopyResponse)
async def get_copy_by_nfc(nfc_id: str, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Look up a physical book copy by scanning its NFC tag.
    Used by kiosk to identify which book is being placed on the scanner.
    """
    row = await db.fetchrow(_COPY_LOCATION_SQL + " WHERE bc.nfc_id = $1", nfc_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"No book copy found with NFC tag '{nfc_id}'.")
    return _row_to_copy_response(row)


@router.patch("/{copy_id}/status", status_code=status.HTTP_200_OK)
async def update_copy_status(copy_id: int, payload: CopyStatusUpdate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: manually update a copy's status (e.g., mark as lost or damaged)."""
    exists = await db.fetchval("SELECT copy_id FROM book_copies WHERE copy_id = $1", copy_id)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Copy {copy_id} not found.")
    await db.execute("UPDATE book_copies SET status = $1 WHERE copy_id = $2", payload.status.value, copy_id)
    return {"status": "success", "copy_id": copy_id, "new_status": payload.status.value}
