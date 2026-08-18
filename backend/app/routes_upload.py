import asyncio

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from .chunker import chunk_pages
from .config import settings
from .deps import get_embedder, get_llm, get_store
from .embeddings import Embedder
from .llm_client import LLM
from .mongo_client import MongoStore
from .pdf_parser import parse_pdf
from .schemas import UploadOut

router = APIRouter()


async def run_ingestion(document_id: ObjectId, data: bytes, store: MongoStore, embedder: Embedder, llm: LLM) -> None:
    try:
        pages, page_count = await asyncio.to_thread(parse_pdf, data)
        if not "".join(pages).strip():
            await asyncio.to_thread(store.mark_document_failed, document_id, "PDF contains no extractable text")
            return
        chunks = await asyncio.to_thread(
            chunk_pages, pages, embedder.count_tokens, settings.chunk_size, settings.chunk_overlap
        )
        texts = [c.text for c in chunks]
        vectors = await asyncio.to_thread(embedder.encode, texts)
        rows = [
            {
                "document_id": ObjectId(document_id),
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "text": c.text,
                "embedding": v,
            }
            for c, v in zip(chunks, vectors)
        ]
        await asyncio.to_thread(store.insert_chunks, rows)
        full_text = " ".join(texts)[:3000]
        summary = await llm.call(
            settings.plan_model,
            f"Summarize this document in 2-3 sentences:\n\n{full_text}",
            system="You are a document summarizer. Be concise.",
            max_tokens=256,
        )
        await asyncio.to_thread(store.mark_document_ready, document_id, page_count, summary)
    except Exception as exc:
        await asyncio.to_thread(store.mark_document_failed, document_id, str(exc))


@router.post("/upload", response_model=UploadOut)
async def upload_pdf(
    file: UploadFile = File(...),
    background: BackgroundTasks = BackgroundTasks(),
    store: MongoStore = Depends(get_store),
    embedder: Embedder = Depends(get_embedder),
    llm: LLM = Depends(get_llm),
) -> UploadOut:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type: upload a PDF")
    data = await file.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid file type: not a PDF")
    document_id = await asyncio.to_thread(store.insert_document, file.filename)
    background.add_task(run_ingestion, document_id, data, store, embedder, llm)
    return UploadOut(document_id=str(document_id), status="processing")
