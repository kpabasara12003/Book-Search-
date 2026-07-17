from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date, timedelta
import asyncpg
from app.database import get_raw_db
from app.schemas import BorrowRequest, ReturnRequest, BorrowResponse

router = APIRouter(prefix="/borrows", tags=["Borrowing & Returns"])

MAX_ACTIVE_BORROWS = 3
LOAN_PERIOD_DAYS   = 14
FINE_PER_DAY       = 10.00  # currency units per overdue day


@router.post("", response_model=BorrowResponse, status_code=status.HTTP_201_CREATED)
async def borrow_book(payload: BorrowRequest, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Self-service borrow. Student taps their card (student_nfc_uid) then places
    the book on the NFC scanner (copy_nfc_id). All eligibility rules are enforced atomically.
    """
    # 1. Identify student
    student = await db.fetchrow(
        "SELECT student_id, is_blocked, active_borrows FROM students WHERE nfc_uid = $1",
        payload.student_nfc_uid
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student NFC card not recognised.")
    if student["is_blocked"]:
        raise HTTPException(status_code=403, detail="Your library account is blocked due to pending fines. Please clear them at the library desk.")
    if student["active_borrows"] >= MAX_ACTIVE_BORROWS:
        raise HTTPException(status_code=403, detail=f"Borrow limit reached ({MAX_ACTIVE_BORROWS} books). Please return a book before borrowing another.")

    # 2. Check for unpaid fines
    pending_fine = await db.fetchval(
        "SELECT fine_id FROM fines WHERE student_id = $1 AND status = 'pending' LIMIT 1",
        student["student_id"]
    )
    if pending_fine:
        raise HTTPException(status_code=403, detail="You have outstanding fines. Please settle them at the library desk before borrowing.")

    # 3. Identify and validate the book copy
    copy = await db.fetchrow(
        "SELECT copy_id, book_id, status FROM book_copies WHERE nfc_id = $1",
        payload.copy_nfc_id
    )
    if not copy:
        raise HTTPException(status_code=404, detail=f"Book NFC tag '{payload.copy_nfc_id}' not found in system.")
    if copy["status"] != "available":
        raise HTTPException(status_code=409, detail=f"This copy is currently '{copy['status']}' and cannot be borrowed.")

    # 4. Atomic borrow transaction
    due = date.today() + timedelta(days=LOAN_PERIOD_DAYS)
    async with db.transaction():
        borrow = await db.fetchrow(
            """
            INSERT INTO borrows (copy_id, student_id, due_date)
            VALUES ($1, $2, $3)
            RETURNING borrow_id, copy_id, student_id, borrowed_at, due_date, returned_at, fine_issued;
            """,
            copy["copy_id"], student["student_id"], due
        )
        await db.execute("UPDATE book_copies SET status = 'borrowed' WHERE copy_id = $1", copy["copy_id"])
        await db.execute("UPDATE students SET active_borrows = active_borrows + 1 WHERE student_id = $1", student["student_id"])

    return BorrowResponse(**dict(borrow))


@router.post("/return", status_code=status.HTTP_200_OK)
async def return_book(payload: ReturnRequest, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Self-service return. Student places the book on the scanner. The system finds
    the active borrow, closes it, and auto-generates a fine if overdue.
    """
    # 1. Identify copy
    copy = await db.fetchrow(
        "SELECT copy_id FROM book_copies WHERE nfc_id = $1",
        payload.copy_nfc_id
    )
    if not copy:
        raise HTTPException(status_code=404, detail=f"Book NFC tag '{payload.copy_nfc_id}' not found in system.")

    # 2. Find the active (unreturned) borrow for this copy
    borrow = await db.fetchrow(
        "SELECT borrow_id, student_id, due_date FROM borrows WHERE copy_id = $1 AND returned_at IS NULL",
        copy["copy_id"]
    )
    if not borrow:
        raise HTTPException(status_code=409, detail="This book copy has no active borrow record. It may already have been returned.")

    today = date.today()
    days_overdue = (today - borrow["due_date"]).days
    fine_amount  = round(max(0, days_overdue) * FINE_PER_DAY, 2)
    fine_created = fine_amount > 0

    async with db.transaction():
        # Close borrow record
        await db.execute(
            "UPDATE borrows SET returned_at = NOW(), fine_issued = $1 WHERE borrow_id = $2",
            fine_created, borrow["borrow_id"]
        )
        # Restore copy to shelf
        await db.execute("UPDATE book_copies SET status = 'available' WHERE copy_id = $1", copy["copy_id"])
        # Decrement student active counter
        await db.execute(
            "UPDATE students SET active_borrows = GREATEST(active_borrows - 1, 0) WHERE student_id = $1",
            borrow["student_id"]
        )
        # Generate fine if overdue
        if fine_created:
            await db.execute(
                "INSERT INTO fines (borrow_id, student_id, amount) VALUES ($1, $2, $3)",
                borrow["borrow_id"], borrow["student_id"], fine_amount
            )
            # Block student account until fine is cleared
            await db.execute(
                "UPDATE students SET is_blocked = TRUE WHERE student_id = $1",
                borrow["student_id"]
            )

    response = {
        "status": "returned",
        "borrow_id": borrow["borrow_id"],
        "days_overdue": max(0, days_overdue),
        "fine_issued": fine_created,
    }
    if fine_created:
        response["fine_amount"] = fine_amount
        response["message"] = (
            f"Book returned {days_overdue} day(s) late. A fine of {fine_amount:.2f} has been issued. "
            "Your account is now blocked until the fine is cleared at the library desk."
        )
    else:
        response["message"] = "Book returned successfully. Thank you!"
    return response


@router.get("/{borrow_id}", response_model=BorrowResponse)
async def get_borrow(borrow_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Get details of a specific borrow transaction."""
    row = await db.fetchrow(
        "SELECT borrow_id, copy_id, student_id, borrowed_at, due_date, returned_at, fine_issued FROM borrows WHERE borrow_id = $1",
        borrow_id
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Borrow record {borrow_id} not found.")
    return BorrowResponse(**dict(row))
