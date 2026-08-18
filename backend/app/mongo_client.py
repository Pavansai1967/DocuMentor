from datetime import UTC, datetime

from bson import ObjectId
from pymongo import MongoClient


def build_vector_search_pipeline(
    document_id: ObjectId, embedding: list[float], top_k: int = 4
) -> list[dict]:
    return [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": top_k * 10,
                "limit": top_k,
                "filter": {"document_id": document_id},
            }
        },
        {"$project": {"_id": 0, "text": 1, "page_number": 1}},
    ]


class MongoStore:
    def __init__(self, uri: str, db_name: str):
        self._client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        self._db = self._client[db_name]

    @property
    def documents(self):
        return self._db["documents"]

    @property
    def chunks(self):
        return self._db["chunks"]

    def ping(self) -> None:
        self._client.admin.command("ping")

    def insert_document(self, filename: str) -> ObjectId:
        result = self.documents.insert_one(
            {
                "filename": filename,
                "upload_date": datetime.now(UTC),
                "page_count": 0,
                "status": "processing",
                "error": None,
                "summary": None,
                "processing_started_at": datetime.now(UTC),
            }
        )
        return result.inserted_id

    def mark_document_ready(self, document_id: ObjectId, page_count: int, summary: str | None = None) -> None:
        update: dict = {"status": "ready", "page_count": page_count, "error": None}
        if summary is not None:
            update["summary"] = summary
        self.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update},
        )

    def mark_document_failed(self, document_id: ObjectId, error: str) -> None:
        self.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "failed", "error": error}},
        )

    def insert_chunks(self, rows: list[dict]) -> None:
        if rows:
            self.chunks.insert_many(rows, ordered=False)

    def get_document(self, document_id: ObjectId) -> dict | None:
        return self.documents.find_one({"_id": ObjectId(document_id)})

    def list_documents(self) -> list[dict]:
        return list(self.documents.find().sort("upload_date", -1))

    def vector_search(self, document_id: ObjectId, embedding: list[float], top_k: int = 4) -> list[dict]:
        pipeline = build_vector_search_pipeline(document_id, embedding, top_k)
        return list(self.chunks.aggregate(pipeline))

    def vector_search_all(self, embedding: list[float], top_k: int = 3) -> list[dict]:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                }
            },
            {"$project": {"_id": 1, "document_id": 1, "page_number": 1, "chunk_index": 1, "text": 1}},
        ]
        return list(self.chunks.aggregate(pipeline))