from fastapi import HTTPException

from .config import settings
from .embeddings import Embedder, get_embedder as _get_embedder_singleton
from .llm_client import LLM
from .mongo_client import MongoStore

_store = None
_llm = None


def get_store() -> MongoStore:
    global _store
    if not settings.mongodb_uri:
        raise HTTPException(status_code=503, detail="MongoDB connection string (MONGODB_URI) is not configured")
    if _store is None:
        _store = MongoStore(settings.mongodb_uri, settings.mongodb_db_name)
        try:
            _store.ping()
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Could not reach MongoDB Atlas: {exc}") from exc
    return _store


def get_embedder() -> Embedder:
    return _get_embedder_singleton()


def get_llm() -> LLM:
    global _llm
    if not settings.groq_api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured")
    if _llm is None:
        _llm = LLM(settings.groq_api_key, settings.llm_model)
    return _llm
