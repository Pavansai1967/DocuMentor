import asyncio
import json

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from .deps import get_embedder, get_llm, get_store
from .embeddings import Embedder
from .llm_client import LLM, build_prompt
from .mongo_client import MongoStore
from .schemas import ChatRequest

router = APIRouter()


def _sse(event_type: str, payload: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **payload})}\n\n"


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    store: MongoStore = Depends(get_store),
    embedder: Embedder = Depends(get_embedder),
    llm: LLM = Depends(get_llm),
) -> StreamingResponse:
    try:
        document = await asyncio.to_thread(store.get_document, ObjectId(payload.document_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.get("status") != "ready":
        raise HTTPException(status_code=409, detail="Document is not ready to chat yet")

    async def generate():
        try:
            question_vector = (await asyncio.to_thread(embedder.encode, [payload.question]))[0]
            sources = await asyncio.to_thread(store.vector_search, ObjectId(payload.document_id), question_vector, 4)
            prompt = build_prompt(payload.question, sources)
            async for token in llm.stream_answer(prompt):
                yield _sse("token", {"text": token})
            yield _sse("sources", {"sources": sources})
            yield _sse("done", {})
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream")
