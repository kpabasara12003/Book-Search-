# app/routers/books.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
import asyncpg
from app.database import get_raw_db
from app.schemas import BookCreate, BookUpdate, BookResponse, AddAuthorsToBookRequest, CopyResponse
from app.services.embedding import embedding_service
from app.services.vector_db import vdb_manager

router = APIRouter(prefix="/books", tags=["Books"])

def _row_to_book_response(record) -> BookResponse:
    return BookResponse(
        book_id=record["book_id"],
        title=record["title"],
        subtitle=record["subtitle"],
        isbn=record["isbn"],
        publisher=record["publisher"],
        edition=record["edition"],
        language=record["language"],
        publication_year=record["publication_year"],
        pages=record["pages"],
        summary=record["summary"],
        category_id=record["category_id"],
        category_name=record["category_name"],
        total_copies=record["total_copies"],
        authors=record["authors"] if record["authors"] != [None] else [],
    )

_BOOK_SELECT_SQL = """
    SELECT
        b.book_id, b.title, b.subtitle, b.isbn, b.publisher, b.edition,
        b.language, b.publication_year, b.pages, b.summary,
        b.category_id, b.total_copies,
        c.category_name,
        ARRAY_AGG(DISTINCT a.author_name) AS authors
    FROM books b
    JOIN book_categories c ON b.category_id = c.category_id
    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
    LEFT JOIN authors a ON ba.author_id = a.author_id
"""

@router.get("/search/semantic", response_model=list[BookResponse])
async def search_books_semantic(
    query: str = Query(..., description="Natural language search query"),
    limit: int = Query(5, ge=1, le=50),
    db: asyncpg.Connection = Depends(get_raw_db)
):
    """
    Hybrid semantic + keyword search powered by BGE-M3 and Qdrant RRF.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    # OPTIONAL PROMPT IMPROVEMENT: BGE-M3 handles asymmetric search significantly better
    # if you instruct the query side on what it's looking for.
    processed_query = f"Represent this sentence for searching relevant book passages: {query.strip()}"

    dense_query, sparse_query = await embedding_service.get_hybrid_embeddings(processed_query)
    matched_ids = await vdb_manager.hybrid_search(dense_query=dense_query, sparse_query=sparse_query, limit=limit)

    if not matched_ids:
        return []

    raw_rows = await db.fetch(
        _BOOK_SELECT_SQL + " WHERE b.book_id = ANY($1) GROUP BY b.book_id, c.category_name;",
        matched_ids
    )
    id_to_row = {row["book_id"]: row for row in raw_rows}
    return [_row_to_book_response(id_to_row[bid]) for bid in matched_ids if bid in id_to_row]

@router.get("/search/standard", response_model=list[BookResponse])
async def search_books_standard(
    query: str = Query(None, description="Search query by title or author"),
    category_id: int | None = Query(None, description="Optional category filter"),
    limit: int = Query(10, ge=1, le=50),
    db: asyncpg.Connection = Depends(get_raw_db)
):
    """
    Standard SQL search using ILIKE on title and author, and exact category match.
    """
    if not query and not category_id:
        raise HTTPException(status_code=400, detail="Must provide query or category_id.")

    params = []
    conditions = []
    
    if query and query.strip():
        params.append(f"%{query.strip()}%")
        conditions.append(f"(b.title ILIKE ${len(params)} OR a.author_name ILIKE ${len(params)})")
        
    if category_id:
        params.append(category_id)
        conditions.append(f"b.category_id = ${len(params)}")
        
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    limit_clause = f" LIMIT ${len(params) + 1}"
    params.append(limit)
    
    full_sql = f"{_BOOK_SELECT_SQL} {where} GROUP BY b.book_id, c.category_name ORDER BY b.title {limit_clause}"
    
    raw_rows = await db.fetch(full_sql, *params)
    return [_row_to_book_response(row) for row in raw_rows]



@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Get full book details by ID."""
    row = await db.fetchrow(
        _BOOK_SELECT_SQL + " WHERE b.book_id = $1 GROUP BY b.book_id, c.category_name;",
        book_id
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found.")
    return _row_to_book_response(row)


@router.get("/{book_id}/copies", response_model=list[CopyResponse])
async def get_book_copies(book_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """List all physical copies of a book with their location and current status."""
    book_exists = await db.fetchval("SELECT book_id FROM books WHERE book_id = $1", book_id)
    if not book_exists:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found.")

    rows = await db.fetch(
        """
        SELECT
            bc.copy_id, bc.book_id, bc.nfc_id, bc.status,
            lf.floor_name, s.section_code, s.section_name,
            bs.shelf_code, sr.row_position
        FROM book_copies bc
        JOIN shelf_rows sr ON bc.row_id = sr.row_id
        JOIN bookshelves bs ON sr.shelf_id = bs.shelf_id
        JOIN sections s ON bs.section_id = s.section_id
        JOIN library_floors lf ON s.floor_id = lf.floor_id
        WHERE bc.book_id = $1
        ORDER BY bc.copy_id;
        """,
        book_id
    )
    return [
        CopyResponse(
            copy_id=r["copy_id"], book_id=r["book_id"], nfc_id=r["nfc_id"], status=r["status"],
            location={
                "floor_name": r["floor_name"], "section_code": r["section_code"],
                "section_name": r["section_name"], "shelf_code": r["shelf_code"],
                "row_position": r["row_position"]
            }
        )
        for r in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_book(payload: BookCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Bulletproof ingestion: detects out-of-sync states between PostgreSQL and Qdrant
    and runs self-healing routines automatically. Stripped of structural noise 
    to maximize summary search accuracy.
    """
    # 1. Structural Pre-validation
    category_check = await db.fetchval(
        "SELECT category_id FROM book_categories WHERE category_id = $1", 
        payload.category_id
    )
    if not category_check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Category '{payload.category_id}' does not exist."
        )

    # 2. Check current synchronization states across engines
    pg_book = None
    if payload.isbn:
        pg_book = await db.fetchrow("SELECT book_id FROM books WHERE isbn = $1", payload.isbn)
    else:
        pg_book = await db.fetchrow(
            "SELECT book_id FROM books WHERE title = $1 AND publication_year = $2", 
            payload.title, payload.publication_year
        )

    qdrant_id = await vdb_manager.find_book_by_unique_fields(
        payload.isbn, payload.title, payload.publication_year
    )

    if pg_book and qdrant_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Book already exists. Postgres ID: {pg_book['book_id']}, Qdrant ID: {qdrant_id}."
        )

    # 3. Standardize text structure for high-accuracy asymmetric search
    text_components = [payload.title, payload.subtitle, payload.summary]
    context_string = "\n".join([item for item in text_components if item]).strip()

    # Self-healing path: Postgres record exists but Qdrant index is missing
    if pg_book and qdrant_id is None:
        target_id = pg_book["book_id"]
        dense_vec, sparse_vec = await embedding_service.get_hybrid_embeddings(context_string)
        await vdb_manager.upsert_book_vectors(
            book_id=target_id, dense=dense_vec, sparse=sparse_vec, 
            isbn=payload.isbn, title=payload.title, year=payload.publication_year, 
            subtitle=payload.subtitle, summary=payload.summary
        )
        return {
            "status": "healed", 
            "book_id": target_id, 
            "message": "Qdrant index repaired for existing PostgreSQL record."
        }

    # Clean up orphan vectors in Qdrant before proceeding with fresh entry creation
    if qdrant_id is not None and not pg_book:
        await vdb_manager.delete_point(qdrant_id)

    # 4. Generate embeddings outside the relational database transaction window
    dense_vec, sparse_vec = await embedding_service.get_hybrid_embeddings(context_string)

    # 5. Core transactional execution block
    try:
        async with db.transaction():
            book_id = await db.fetchval(
                """
                INSERT INTO books (title, subtitle, isbn, publisher, edition, language, publication_year, pages, summary, category_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING book_id;
                """,
                payload.title, payload.subtitle, payload.isbn, payload.publisher,
                payload.edition, payload.language, payload.publication_year,
                payload.pages, payload.summary, payload.category_id
            )
            
            author_ids = list(set(payload.author_ids))
            count = await db.fetchval(
                "SELECT count(*) FROM authors WHERE author_id = ANY($1::int[])", 
                author_ids
            )
            if count != len(author_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="One or more Author IDs are invalid."
                )
                
            await db.execute(
                "INSERT INTO book_authors (book_id, author_id) SELECT $1, unnest($2::int[])", 
                book_id, author_ids
            )
            
            # Upsert vectors safely inside the transaction block boundaries
            await vdb_manager.upsert_book_vectors(
                book_id=book_id, dense=dense_vec, sparse=sparse_vec, 
                isbn=payload.isbn, title=payload.title, year=payload.publication_year, 
                subtitle=payload.subtitle, summary=payload.summary
            )
            
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="A book with this ISBN already exists."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Write aborted, database rollback complete. Error: {str(e)}"
        )

    return {
        "status": "success", 
        "book_id": book_id, 
        "message": "Book inserted into PostgreSQL and indexed in Qdrant."
    }


@router.put("/{book_id}", status_code=status.HTTP_200_OK)
async def update_book(book_id: int, payload: BookUpdate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Admin: update book metadata fields. Only provided fields are updated."""
    book = await db.fetchrow("SELECT * FROM books WHERE book_id = $1", book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book {book_id} not found."
        )

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return {"status": "no-op", "message": "No fields provided to update."}

    # Execute partial SQL metadata updates
    set_clauses = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
    values = list(updates.values())
    await db.execute(f"UPDATE books SET {set_clauses} WHERE book_id = $1", book_id, *values)

    # Re-index in Qdrant only if fields that build the semantic profile changed
    if any(key in updates for key in ("title", "subtitle", "summary")):
        merged_record = {**dict(book), **updates}
        
        # Structure payload elements cleanly using clean spacing layout rules
        text_components = [
            merged_record['title'], 
            merged_record.get('subtitle'), 
            merged_record.get('summary')
        ]
        context_string = "\n".join([item for item in text_components if item]).strip()
        
        dense_vec, sparse_vec = await embedding_service.get_hybrid_embeddings(context_string)
        await vdb_manager.upsert_book_vectors(
            book_id=book_id, 
            dense=dense_vec, 
            sparse=sparse_vec, 
            isbn=merged_record.get("isbn"), 
            title=merged_record["title"], 
            year=merged_record.get("publication_year"), 
            subtitle=merged_record.get("subtitle"), 
            summary=merged_record.get("summary")
        )

    return {
        "status": "success", 
        "book_id": book_id, 
        "updated_fields": list(updates.keys())
    }
@router.post("/{book_id}/authors", status_code=status.HTTP_200_OK)
async def add_authors_to_book(book_id: int, payload: AddAuthorsToBookRequest, db: asyncpg.Connection = Depends(get_raw_db)):
    """Link additional authors to a book."""
    book_exists = await db.fetchval("SELECT book_id FROM books WHERE book_id = $1", book_id)
    if not book_exists:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found.")

    author_ids = list(set(payload.author_ids))
    count = await db.fetchval("SELECT count(*) FROM authors WHERE author_id = ANY($1::int[])", author_ids)
    if count != len(author_ids):
        raise HTTPException(status_code=400, detail="One or more Author IDs are invalid.")

    await db.execute(
        "INSERT INTO book_authors (book_id, author_id) SELECT $1, unnest($2::int[]) ON CONFLICT DO NOTHING;",
        book_id, author_ids
    )
    return {"status": "success", "message": f"Authors linked to book {book_id}."}
