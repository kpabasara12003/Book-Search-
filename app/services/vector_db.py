from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, PointStruct, SparseVector, Prefetch, FusionQuery, Fusion, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
from app.config import settings

class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, check_compatibility=False)
        self.collection_name = "hybrid_books"

    def init_collection(self):
        try:
            exists = self.client.collection_exists(self.collection_name)
        except UnexpectedResponse as e:
            exists = False if e.status_code == 404 else True
            if e.status_code != 404: raise e

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
                sparse_vectors_config={"sparse": SparseVectorParams(index=None)}
            )

    async def find_book_by_unique_fields(self, isbn: str | None, title: str, year: int | None) -> int | None:
        """Looks up a point in Qdrant by exact match filters. Returns the point ID if found."""
        filter_conditions = []
        if isbn:
            filter_conditions.append(FieldCondition(key="isbn", match=MatchValue(value=isbn)))
        else:
            filter_conditions.append(FieldCondition(key="title", match=MatchValue(value=title)))
            if year:
                filter_conditions.append(FieldCondition(key="publication_year", match=MatchValue(value=year)))

        points, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=filter_conditions),
            limit=1,
            with_payload=False,
            with_vectors=False
        )
        return points[0].id if points else None

    async def delete_point(self, point_id: int):
        """Removes a conflicting orphan point from Qdrant."""
        self.client.delete(collection_name=self.collection_name, points_selector=[point_id])

    async def upsert_book_vectors(self, book_id: int, dense: list[float], sparse: dict[int, float], isbn: str | None, title: str, year: int | None):
        """Indexes vector pair along with core metadata fields for precise lookup tracking."""
        indices = list(sparse.keys())
        values = list(sparse.values())

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=book_id,
                    vector={
                        "dense": dense,
                        "sparse": SparseVector(indices=indices, values=values)
                    },
                    payload={
                        "isbn": isbn,
                        "title": title,
                        "publication_year": year
                    }
                )
            ]
        )

    async def hybrid_search(self, dense_query: list[float], sparse_query: dict[int, float], limit: int) -> list[int]:
        sparse_obj = SparseVector(indices=list(sparse_query.keys()), values=list(sparse_query.values()))
        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(query=dense_query, using="dense", limit=limit * 2),
                Prefetch(query=sparse_obj, using="sparse", limit=limit * 2)
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit
        )
        return [int(point.id) for point in response.points]

vdb_manager = QdrantManager()