from groq import AsyncGroq


def build_prompt(question: str, sources: list[dict]) -> str:
    lines = [
        "You are DocuMentor, answering questions about a document.",
        "Use ONLY the provided source excerpts. If the answer is not in them,",
        "say you don't know. Cite sources as [1], [2], ... in your answer.",
        "",
        "Sources:",
    ]
    for i, source in enumerate(sources, start=1):
        lines.append(f"[{i}] (p. {source['page_number']}) {source['text']}")
    lines += ["", f"Question: {question}", "Answer:"]
    return "\n".join(lines)


class LLM:
    def __init__(self, api_key: str, model: str):
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def stream_answer(self, prompt: str):
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            temperature=0.2,
        )
        async for part in stream:
            delta = part.choices[0].delta.content
            if delta:
                yield delta
