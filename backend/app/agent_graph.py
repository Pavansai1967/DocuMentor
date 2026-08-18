import asyncio
import json
from dataclasses import dataclass, field
from typing import Literal

from bson import ObjectId
from langgraph.graph import END, StateGraph

from .config import settings
from .embeddings import Embedder
from .llm_client import LLM
from .mongo_client import MongoStore

_deps: dict = {}


@dataclass
class AgentState:
    question: str = ""
    documents: list[dict] = field(default_factory=list)
    sub_queries: list[dict] = field(default_factory=list)
    chunks: list[dict] = field(default_factory=list)
    iteration_count: int = 0
    sufficient_evidence: bool = False
    answer: str = ""
    trace: list[dict] = field(default_factory=list)


def _truncate(text: str, max_tokens: int = 150) -> str:
    words = text.split()
    return " ".join(words[:max_tokens])


async def _to_thread(func, *args):
    return await asyncio.to_thread(func, *args)


async def plan_node(state: AgentState) -> dict:
    llm: LLM = _deps["llm"]
    store: MongoStore = _deps["store"]
    documents = await _to_thread(store.list_documents)
    docs_block = "\n".join(
        f"- {d['_id']}: {d['filename']} — {d.get('summary', 'No summary')}"
        for d in documents
    )
    prompt = f"""You are DocuMentor's planning node. Given a question and available documents, decide which documents to search and what sub-queries to run.

Available documents:
{docs_block}

Question: {state.question}

Respond with JSON array of objects with keys: document_id (string), sub_query (string).
Example: [{{"document_id": "...", "sub_query": "what is X"}}]
If no documents are relevant, respond with empty array: []"""
    result = await llm.call(settings.plan_model, prompt, system="You are a search planner. Respond only with valid JSON.", max_tokens=512)
    try:
        cleaned = result.strip().removeprefix("```json").removesuffix("```").strip()
        sub_queries = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        sub_queries = []
    trace_entry = {"step": "plan", "sub_queries": sub_queries}
    return {
        "sub_queries": sub_queries,
        "trace": [*state.trace, trace_entry],
    }


async def retrieve_node(state: AgentState) -> dict:
    store: MongoStore = _deps["store"]
    embedder: Embedder = _deps["embedder"]
    all_chunks = list(state.chunks)
    seen_ids = {c.get("_id") for c in all_chunks}
    for sq in state.sub_queries:
        doc_id = sq.get("document_id")
        query = sq.get("sub_query", "")
        if not doc_id or not query:
            continue
        try:
            embedding = (await _to_thread(embedder.encode, [query]))[0]
            results = await _to_thread(store.vector_search, ObjectId(doc_id), embedding, settings.default_top_k)
        except Exception:  # noqa: S112
            continue
        for r in results:
            chunk_id = str(r.get("_id", ""))
            if chunk_id not in seen_ids:
                all_chunks.append(r)
                seen_ids.add(chunk_id)
        if len(all_chunks) >= settings.max_accumulated_chunks:
            break
    all_chunks = all_chunks[:settings.max_accumulated_chunks]
    trace_entry = {
        "step": "retrieve",
        "queries_run": len(state.sub_queries),
        "chunks_found": len(all_chunks),
    }
    return {
        "chunks": all_chunks,
        "trace": [*state.trace, trace_entry],
    }


async def evaluate_node(state: AgentState) -> dict:
    llm: LLM = _deps["llm"]
    chunks_text = "\n---\n".join(
        f"[chunk {i}] (doc {c.get('document_id', '?')}, p.{c.get('page_number', '?')}) {_truncate(c.get('text', ''))}"
        for i, c in enumerate(state.chunks)
    )
    prompt = f"""Evaluate whether the retrieved evidence is sufficient to answer the question.

Question: {state.question}

Retrieved chunks:
{chunks_text}

Respond with JSON: {{"sufficient": true/false, "reformulated_query": "..."}}
If sufficient is false, provide a reformulated query to try next.
If sufficient is true, reformulated_query can be empty."""
    result = await llm.call(settings.evaluate_model, prompt, system="You are an evidence evaluator. Respond only with valid JSON.", max_tokens=256)
    try:
        cleaned = result.strip().removeprefix("```json").removesuffix("```").strip()
        evaluation = json.loads(cleaned)
        sufficient = evaluation.get("sufficient", True)
        reformulated = evaluation.get("reformulated_query", "")
    except (json.JSONDecodeError, ValueError):
        sufficient = True
        reformulated = ""
    trace_entry = {"step": "evaluate", "sufficient": sufficient, "reformulated_query": reformulated}
    return {
        "sufficient_evidence": sufficient,
        "iteration_count": state.iteration_count + 1,
        "trace": [*state.trace, trace_entry],
        "sub_queries": [{"document_id": state.sub_queries[0].get("document_id", ""), "sub_query": reformulated}] if reformulated else state.sub_queries,
    }


def should_continue(state: AgentState) -> Literal["answer", "retrieve"]:
    if state.sufficient_evidence or state.iteration_count >= settings.max_agent_iterations:
        return "answer"
    return "retrieve"


async def answer_node(state: AgentState) -> dict:
    llm: LLM = _deps["llm"]
    chunks_text = "\n---\n".join(
        f"[{i+1}] (doc {c.get('document_id', '?')}, p.{c.get('page_number', '?')}) {c.get('text', '')}"
        for i, c in enumerate(state.chunks)
    )
    note = ""
    if not state.sufficient_evidence:
        note = "\nNote: The available documents may not fully cover this question. Answer based on what is available."
    prompt = f"""Answer the question using ONLY the provided source excerpts. Cite sources as [1], [2], etc.

Sources:
{chunks_text}

Question: {state.question}{note}
Answer:"""
    answer = ""
    on_token = _deps.get("on_token")
    async for token in llm.stream_answer(settings.answer_model, prompt, system="You are DocuMentor, answering questions about documents. Be helpful and cite sources."):
        answer += token
        if on_token:
            await on_token(token)
    trace_entry = {"step": "answer", "iteration_count": state.iteration_count}
    return {
        "answer": answer,
        "trace": [*state.trace, trace_entry],
    }


def build_graph(store: MongoStore, embedder: Embedder, llm: LLM, on_token=None) -> StateGraph:
    _deps["store"] = store
    _deps["embedder"] = embedder
    _deps["llm"] = llm
    _deps["on_token"] = on_token

    graph = StateGraph(AgentState)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("answer", answer_node)
    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges("evaluate", should_continue, {"answer": "answer", "retrieve": "retrieve"})
    graph.add_edge("answer", END)
    return graph.compile()
