from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.database import get_raw_db
from app.schemas import StudentCreate, StudentResponse, StudentIdentifyRequest, BorrowResponse, FineResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/identify", response_model=StudentResponse)
async def identify_student(payload: StudentIdentifyRequest, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Kiosk entry point. The student taps their NFC card; this endpoint identifies
    them and returns their profile + borrow status.
    """
    row = await db.fetchrow(
        "SELECT student_id, full_name, email, phone, student_number, active_borrows, is_blocked, created_at "
        "FROM students WHERE nfc_uid = $1",
        payload.nfc_uid
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student NFC card not recognised. Please contact the library desk.")
    return StudentResponse(**dict(row))


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def register_student(payload: StudentCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: register a new student with their NFC card UID."""
    try:
        row = await db.fetchrow(
            """
            INSERT INTO students (full_name, email, phone, student_number, nfc_uid)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING student_id, full_name, email, phone, student_number, active_borrows, is_blocked, created_at;
            """,
            payload.full_name, payload.email, payload.phone, payload.student_number, payload.nfc_uid
        )
        return StudentResponse(**dict(row))
    except asyncpg.UniqueViolationError as e:
        detail = "Student number or NFC UID already registered."
        if "nfc_uid" in str(e):
            detail = "This NFC card is already linked to another student."
        elif "student_number" in str(e):
            detail = "This student number is already registered."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: get a student's full profile by their internal ID."""
    row = await db.fetchrow(
        "SELECT student_id, full_name, email, phone, student_number, active_borrows, is_blocked, created_at "
        "FROM students WHERE student_id = $1",
        student_id
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found.")
    return StudentResponse(**dict(row))


@router.get("/{student_id}/borrows", response_model=list[BorrowResponse])
async def get_student_borrows(student_id: int, active_only: bool = False, db: asyncpg.Connection = Depends(get_raw_db)):
    """Get all borrows for a student. Pass ?active_only=true to see only unreturned books."""
    exists = await db.fetchval("SELECT student_id FROM students WHERE student_id = $1", student_id)
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found.")

    sql = "SELECT borrow_id, copy_id, student_id, borrowed_at, due_date, returned_at, fine_issued FROM borrows WHERE student_id = $1"
    if active_only:
        sql += " AND returned_at IS NULL"
    sql += " ORDER BY borrowed_at DESC"
    rows = await db.fetch(sql, student_id)
    return [BorrowResponse(**dict(r)) for r in rows]


@router.get("/{student_id}/fines", response_model=list[FineResponse])
async def get_student_fines(student_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Get all fines for a student."""
    exists = await db.fetchval("SELECT student_id FROM students WHERE student_id = $1", student_id)
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student {student_id} not found.")
    rows = await db.fetch(
        "SELECT fine_id, borrow_id, student_id, amount, status, created_at FROM fines WHERE student_id = $1 ORDER BY created_at DESC",
        student_id
    )
    return [FineResponse(**dict(r)) for r in rows]
