from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, status, APIRouter
import asyncpg
from app.database import db_manager, get_raw_db
from app.services.embedding import embedding_service
from app.services.vector_db import vdb_manager
from app.schemas import BookCreate, BookResponse
from app.schemas import (
    CategoryCreate, CategoryResponse, 
    AuthorCreate, AuthorResponse, 
    AddAuthorsToBookRequest
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executed on system initialization
    await db_manager.connect()
    vdb_manager.init_collection()
    yield
    # Executed on teardown
    await db_manager.disconnect()
    await embedding_service.close()

app = FastAPI(
    title="Raw-SQL Hybrid Search Book API", 
    lifespan=lifespan,
    swagger_ui_parameters={"tryItOutEnabled": True}
)

@app.get("/")
async def root():
    return {"status": "healthy", "message": "API is fully reachable"}

@app.post("/books", status_code=status.HTTP_201_CREATED)
async def create_book(payload: BookCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Bulletproof Ingestion Engine. Detects out-of-sync entries across PostgreSQL 
    and Qdrant, running atomic self-healing routines dynamically.
    """
    # 1. Verify Category Validity
    category_check = await db.fetchval("SELECT category_id FROM book_categories WHERE category_id = $1", payload.category_id)
    if not category_check:
        raise HTTPException(status_code=400, detail=f"Category '{payload.category_id}' does not exist.")

    # 2. Query Postgres for existing match
    pg_book = None
    if payload.isbn:
        pg_book = await db.fetchrow("SELECT book_id FROM books WHERE isbn = $1", payload.isbn)
    else:
        pg_book = await db.fetchrow("SELECT book_id FROM books WHERE title = $1 AND publication_year = $2", payload.title, payload.publication_year)

    # 3. Query Qdrant for existing match
    qdrant_id = await vdb_manager.find_book_by_unique_fields(payload.isbn, payload.title, payload.publication_year)

    # -------------------------------------------------------------------------
    # STATE EVALUATION MATRIX
    # -------------------------------------------------------------------------
    
    # CASE 1: Book is perfectly healthy and already exists in BOTH systems.
    if pg_book and qdrant_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book already exists cleanly. Postgres ID: {pg_book['book_id']}, Qdrant ID: {qdrant_id}."
        )

    # CASE 2: State A (The Old Bug) -> Book lives in Postgres but is missing from Qdrant.
    if pg_book and qdrant_id is None:
        target_id = pg_book["book_id"]
        context_string = f"Title: {payload.title}. Subtitle: {payload.subtitle or ''}. Context: {payload.summary or ''}"
        dense_vec, sparse_vec = await embedding_service.get_hybrid_embeddings(context_string)
        
        # Self-Heal Qdrant index
        await vdb_manager.upsert_book_vectors(
            book_id=target_id, dense=dense_vec, sparse=sparse_vec,
            isbn=payload.isbn, title=payload.title, year=payload.publication_year
        )
        return {
            "status": "healed",
            "book_id": target_id,
            "message": "Data asymmetry detected: Book existed in Postgres but was missing from Qdrant. Vector index successfully repaired."
        }

    # CASE 3: State B -> Orphan point exists in Qdrant, but row is missing from Postgres.
    if qdrant_id is not None and not pg_book:
        # Erase the orphan point from Qdrant to prevent ID collisions, then allow clean write
        await vdb_manager.delete_point(qdrant_id)
        print(f"Purged orphan Qdrant point vector ID {qdrant_id} to clear path for relational alignment.")

    # -------------------------------------------------------------------------
    # CLEAN INSERTION PIPELINE (For Case 3 fallback or brand-new records)
    # -------------------------------------------------------------------------
    context_string = f"Title: {payload.title}. Subtitle: {payload.subtitle or ''}. Context: {payload.summary or ''}"
    dense_vec, sparse_vec = await embedding_service.get_hybrid_embeddings(context_string)

    try:
        async with db.transaction():
            # Insert relational rows
            book_id = await db.fetchval(
                """
                INSERT INTO books (title, subtitle, isbn, publisher, edition, language, publication_year, pages, summary, category_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING book_id;
                """,
                payload.title, payload.subtitle, payload.isbn, payload.publisher, 
                payload.edition, payload.language, payload.publication_year, 
                payload.pages, payload.summary, payload.category_id
            )

            for author_id in payload.author_ids:
                author_exists = await db.fetchval("SELECT author_id FROM authors WHERE author_id = $1", author_id)
                if not author_exists:
                    raise HTTPException(status_code=400, detail=f"Author ID '{author_id}' invalid.")
                
                await db.execute("INSERT INTO book_authors (book_id, author_id) VALUES ($1, $2);", book_id, author_id)

            # Sync with Qdrant inside the active transaction block
            await vdb_manager.upsert_book_vectors(
                book_id=book_id, dense=dense_vec, sparse=sparse_vec,
                isbn=payload.isbn, title=payload.title, year=payload.publication_year
            )

    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=400, detail="A book with this ISBN record already exists.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Write operations aborted. Distributed engine rollback completed. Error: {str(e)}"
        )

    return {
        "status": "success",
        "book_id": book_id,
        "message": "Book inserted into PostgreSQL and indexed in Qdrant successfully."
    }
@app.get("/books/search", response_model=list[BookResponse])
async def search_books(
    query: str = Query(..., description="The descriptive natural language query phrase"),
    limit: int = Query(5, ge=1, le=50),
    db: asyncpg.Connection = Depends(get_raw_db)
):
    """
    Accepts natural, descriptive queries, processes them via hybrid embedding models,
    matches IDs using Qdrant RRF ranking, and yields rich data views from PostgreSQL using raw SQL joins.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    # 1. Turn query text into dense & sparse mathematical components
    dense_query, sparse_query = await embedding_service.get_hybrid_embeddings(query)

    # 2. Query Qdrant for matched list of keys
    matched_ids = await vdb_manager.hybrid_search(dense_query=dense_query, sparse_query=sparse_query, limit=limit)

    if not matched_ids:
        return []

    # 3. Use standard raw SQL to join tables, pull metadata records, and collect structured objects
    # We use a explicit ARRAY_AGG function execution to retrieve author lists cleanly inside a single query pass
    raw_rows = await db.fetch(
        """
        SELECT 
            b.book_id, b.title, b.subtitle, b.isbn, b.publisher, b.edition, 
            b.language, b.publication_year, b.pages, b.summary, b.category_id,
            c.category_name,
            ARRAY_AGG(a.author_name) as authors
        FROM books b
        JOIN book_categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        WHERE b.book_id = ANY($1)
        GROUP BY b.book_id, c.category_name;
        """,
        matched_ids
    )

    # 4. Sort fetched database lines to keep the precise ordering score returned from Qdrant vector spaces
    id_to_row_map = {row["book_id"]: row for row in raw_rows}
    sorted_responses = []
    
    for b_id in matched_ids:
        if b_id in id_to_row_map:
            record = id_to_row_map[b_id]
            sorted_responses.append(
                BookResponse(
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
                    authors=record["authors"] if record["authors"] != [None] else []
                )
            )

    return sorted_responses

@app.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Creates a new book category with raw SQL, handling uniqueness validation errors."""
    try:
        row = await db.fetchrow(
            """
            INSERT INTO book_categories (category_name, description)
            VALUES ($1, $2)
            RETURNING category_id, category_name, description;
            """,
            payload.category_name, payload.description
        )
        return CategoryResponse(**dict(row))
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Category identity classification '{payload.category_name}' already exists."
        )


@app.get("/categories", response_model=list[CategoryResponse])
async def get_all_categories(db: asyncpg.Connection = Depends(get_raw_db)):
    """Retrieves all book categories recorded inside the relational system using a raw SQL scan."""
    rows = await db.fetch("SELECT category_id, category_name, description FROM book_categories ORDER BY category_id ASC;")
    return [CategoryResponse(**dict(row)) for row in rows]


# --- AUTHOR MANAGEMENT ENDPOINTS ---

@app.post("/authors", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(payload: AuthorCreate, db: asyncpg.Connection = Depends(get_raw_db)):
    """Inserts a new author record using raw positional parameter SQL queries."""
    row = await db.fetchrow(
        """
        INSERT INTO authors (author_name)
        VALUES ($1)
        RETURNING author_id, author_name;
        """,
        payload.author_name
    )
    return AuthorResponse(**dict(row))


@app.get("/authors/{author_id}", response_model=AuthorResponse)
async def get_author_by_id(author_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """Fetches a specific author entity by primary key, throwing a 404 error if missing."""
    row = await db.fetchrow("SELECT author_id, author_name FROM authors WHERE author_id = $1;", author_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Author record with ID {author_id} does not exist inside the database."
        )
    return AuthorResponse(**dict(row))


# --- MANY-TO-MANY RELATIONSHIP MANAGEMENT ENDPOINTS ---

@app.post("/books/{book_id}/authors", status_code=status.HTTP_200_OK)
async def add_authors_to_book(book_id: int, payload: AddAuthorsToBookRequest, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Safely adds multiple authors to a target book entity using a structured transactional operation loop.
    Implements ON CONFLICT DO NOTHING to avoid crashing on duplicate association entries.
    """
    # 1. Verify the book exists before handling associative assignments
    book_exists = await db.fetchval("SELECT book_id FROM books WHERE book_id = $1;", book_id)
    if not book_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Target book reference with ID {book_id} could not be resolved."
        )

    # 2. Run validations and insertions securely wrapped in an atomic database transaction
    async with db.transaction():
        for author_id in payload.author_ids:
            # Verify identity validity of each provided author key
            author_exists = await db.fetchval("SELECT author_id FROM authors WHERE author_id = $1;", author_id)
            if not author_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Author identifier '{author_id}' is invalid. Transaction aborted."
                )
            
            # Map parameters into many-to-many junction ledger table
            await db.execute(
                """
                INSERT INTO book_authors (book_id, author_id) 
                VALUES ($1, $2)
                ON CONFLICT (book_id, author_id) DO NOTHING;
                """,
                book_id, author_id
            )

    return {"status": "success", "message": f"Successfully mapped author cluster updates to book identity {book_id}."}


@app.get("/books/{book_id}/authors", response_model=list[AuthorResponse])
async def get_authors_of_book(book_id: int, db: asyncpg.Connection = Depends(get_raw_db)):
    """
    Executes a high-speed raw SQL INNER JOIN operation across the book_authors junction table
    to pull a complete list of author entities explicitly mapped to the specified book_id.
    """
    # Verify the book exists
    book_exists = await db.fetchval("SELECT book_id FROM books WHERE book_id = $1;", book_id)
    if not book_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Book identity matrix referencing {book_id} not found."
        )

    rows = await db.fetch(
        """
        SELECT a.author_id, a.author_name 
        FROM authors a
        INNER JOIN book_authors ba ON a.author_id = ba.author_id
        WHERE ba.book_id = $1
        ORDER BY a.author_name ASC;
        """,
        book_id
    )
    
    return [AuthorResponse(**dict(row)) for row in rows]