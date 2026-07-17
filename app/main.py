from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import db_manager
from app.services.embedding import embedding_service
from app.services.vector_db import vdb_manager

from app.routers import students, books, copies, location, borrows, fines, catalog


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_manager.connect()
    await vdb_manager.init_collection()
    yield
    await db_manager.disconnect()
    await embedding_service.close()


app = FastAPI(
    title="University Library Self-Service 30 API",
    description=(
        "Hybrid semantic search (BGE-M3 + Qdrant) combined with a full self-service "
        "borrowing system. Students identify via NFC card; every physical book."
        "carries a unique NFC tag for contactless checkout and return."
    ),
    version="1.2.0",
    lifespan=lifespan,
    swagger_ui_parameters={"tryItOutEnabled": True},
)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "healthy", "message": "University Library Self-Service API is running."}


app.include_router(students.router)
app.include_router(books.router)
app.include_router(copies.router)
app.include_router(location.router)
app.include_router(borrows.router)
app.include_router(fines.router)
app.include_router(catalog.router)