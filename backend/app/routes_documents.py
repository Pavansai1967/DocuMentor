from fastapi import APIRouter, Depends

from .deps import get_store
from .mongo_client import MongoStore
from .schemas import DocumentOut

router = APIRouter()


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(store: MongoStore = Depends(get_store)) -> list[dict]:
    return store.list_documents()
