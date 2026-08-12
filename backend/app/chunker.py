from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Chunk:
    page_number: int
    chunk_index: int
    text: str


def _word_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = None
    for i, ch in enumerate(text):
        if ch.isspace():
            if start is not None:
                spans.append((start, i))
                start = None
        elif start is None:
            start = i
    if start is not None:
        spans.append((start, len(text)))
    return spans


def chunk_pages(
    pages: list[str],
    count_tokens: Callable[[str], int],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    index = 0
    for page_no, text in enumerate(pages, start=1):
        spans = _word_spans(text)
        costs = [count_tokens(text[s:e]) for s, e in spans]
        i = 0
        n = len(spans)
        while i < n:
            start_i = i
            running = 0
            while i < n and running + costs[i] <= chunk_size:
                running += costs[i]
                i += 1
            if i == start_i:
                # single word longer than chunk_size: emit on its own
                s, e = spans[start_i]
                if text[s:e].strip():
                    chunks.append(Chunk(page_number=page_no, chunk_index=index, text=text[s:e].strip()))
                    index += 1
                i += 1
                continue
            s, e = spans[start_i][0], spans[i - 1][1]
            chunks.append(Chunk(page_number=page_no, chunk_index=index, text=text[s:e].strip()))
            index += 1
            if i >= n and start_i > 0:
                break
            advance = 0
            next_i = start_i
            while next_i < i and advance + costs[next_i] <= chunk_size - chunk_overlap:
                advance += costs[next_i]
                next_i += 1
            if next_i <= start_i:
                break
            i = next_i
    return chunks