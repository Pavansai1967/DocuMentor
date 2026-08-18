import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from .agent_graph import AgentState, build_graph
from .deps import get_embedder, get_llm, get_store
from .embeddings import Embedder
from .llm_client import LLM
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
    async def generate():
        try:
            graph = build_graph(store, embedder, llm)
            initial_state = AgentState(question=payload.question)

            final_state = None
            async for event in graph.astream(initial_state):
                for node_output in event.values():
                    if node_output:
                        final_state = node_output

            if final_state:
                answer = final_state.get("answer", "")
                for char in answer:
                    yield _sse("token", {"text": char})

                chunks = final_state.get("chunks", [])
                sources = [
                    {
                        "document_id": str(c.get("document_id", "")),
                        "page_number": c.get("page_number", 0),
                        "text": c.get("text", ""),
                    }
                    for c in chunks
                ]
                trace = final_state.get("trace", [])
                yield _sse("sources", {"sources": sources})
                yield _sse("trace", {"trace": trace})
            yield _sse("done", {})
        except Exception as exc:
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(generate(), media_type="text/event-stream")
