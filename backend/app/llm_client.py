import asyncio

from groq import AsyncGroq, RateLimitError


class LLM:
    def __init__(self, api_key: str):
        self._client = AsyncGroq(api_key=api_key)

    async def _call_with_retry(self, model: str, messages: list[dict], temperature: float = 0.2, max_tokens: int = 1024) -> str:
        try:
            resp = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except RateLimitError as exc:
            retry_after = float(exc.response.headers.get("retry-after", "5"))
            await asyncio.sleep(retry_after)
            resp = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""

    async def call(self, model: str, prompt: str, system: str = "", temperature: float = 0.2, max_tokens: int = 1024) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self._call_with_retry(model, messages, temperature, max_tokens)

    async def stream_answer(self, model: str, prompt: str, system: str = ""):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.2,
            )
            async for part in stream:
                delta = part.choices[0].delta.content
                if delta:
                    yield delta
        except RateLimitError as exc:
            retry_after = float(exc.response.headers.get("retry-after", "5"))
            await asyncio.sleep(retry_after)
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.2,
            )
            async for part in stream:
                delta = part.choices[0].delta.content
                if delta:
                    yield delta
