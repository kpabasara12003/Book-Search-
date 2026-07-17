from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from app.database import get_raw_db
from app.schemas import FineResponse

router = APIRouter(prefix="/fines", tags=["Fines"])


@router.get("/{fine_id}", response_model=FineResponse)
async def get_fine(fine_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Get details about a specific fine."""
    row = await db.fetchrow(
        "SELECT fine_id, borrow_id, student_id, amount, status, created_at FROM fines WHERE fine_id = $1",
        fine_id
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Fine {fine_id} not found.")
    return FineResponse(**dict(row))


@router.post("/{fine_id}/pay", status_code=status.HTTP_200_OK)
async def pay_fine(fine_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Mark a pending fine as paid and unblock the student if they have no remaining pending fines."""
    fine = await db.fetchrow("SELECT fine_id, student_id, status FROM fines WHERE fine_id = $1", fine_id)
    if not fine:
        raise HTTPException(status_code=404, detail=f"Fine {fine_id} not found.")
    if fine["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Fine is already '{fine['status']}' and cannot be paid again.")

    async with db.transaction():
        await db.execute("UPDATE fines SET status = 'paid' WHERE fine_id = $1", fine_id)
        # Unblock student only if no other pending fines remain
        other_pending = await db.fetchval(
            "SELECT fine_id FROM fines WHERE student_id = $1 AND status = 'pending' AND fine_id != $2 LIMIT 1",
            fine["student_id"], fine_id
        )
        if not other_pending:
            await db.execute("UPDATE students SET is_blocked = FALSE WHERE student_id = $1", fine["student_id"])

    return {"status": "success", "fine_id": fine_id, "message": "Fine paid. Account unblocked." if not other_pending else "Fine paid. Other fines still pending."}


@router.post("/{fine_id}/waive", status_code=status.HTTP_200_OK)
async def waive_fine(fine_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: waive a fine (mark as waived without payment)."""
    fine = await db.fetchrow("SELECT fine_id, student_id, status FROM fines WHERE fine_id = $1", fine_id)
    if not fine:
        raise HTTPException(status_code=404, detail=f"Fine {fine_id} not found.")
    if fine["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Fine is already '{fine['status']}' and cannot be waived.")

    async with db.transaction():
        await db.execute("UPDATE fines SET status = 'waived' WHERE fine_id = $1", fine_id)
        other_pending = await db.fetchval(
            "SELECT fine_id FROM fines WHERE student_id = $1 AND status = 'pending' AND fine_id != $2 LIMIT 1",
            fine["student_id"], fine_id
        )
        if not other_pending:
            await db.execute("UPDATE students SET is_blocked = FALSE WHERE student_id = $1", fine["student_id"])

    return {"status": "success", "fine_id": fine_id, "message": "Fine waived. Account unblocked." if not other_pending else "Fine waived. Other fines still pending."}
