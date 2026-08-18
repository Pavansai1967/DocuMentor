import pytest

from app.llm_client import LLM


@pytest.mark.asyncio
async def test_stream_answer_yields_token_deltas(monkeypatch):
    class FakeDelta:
        content = "hi"

    class FakeChoice:
        def __init__(self):
            self.delta = FakeDelta()

    class FakePart:
        def __init__(self):
            self.choices = [FakeChoice()]

    class FakeStream:
        def __init__(self):
            self._parts = iter([FakePart(), FakePart()])

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self._parts)
            except StopIteration:
                raise StopAsyncIteration

    class FakeCompletions:
        async def create(self, **kwargs):
            return FakeStream()

    class FakeChat:
        def __init__(self):
            self.completions = FakeCompletions()

    class FakeClient:
        def __init__(self, api_key=None):
            self.chat = FakeChat()

    from app import llm_client

    monkeypatch.setattr(llm_client, "AsyncGroq", FakeClient)
    llm = LLM(api_key="gsk_test")
    tokens = [t async for t in llm.stream_answer("fake-model", "prompt")]
    assert tokens == ["hi", "hi"]
