import pytest

from app.llm_client import LLM, build_prompt


def test_build_prompt_includes_sources_and_indexes():
    sources = [
        {"page_number": 3, "text": "Alpha is 42."},
        {"page_number": 7, "text": "Beta is 99."},
    ]
    prompt = build_prompt("What is alpha?", sources)
    assert "DocuMentor" in prompt
    assert "[1] (p. 3) Alpha is 42." in prompt
    assert "[2] (p. 7) Beta is 99." in prompt
    assert "What is alpha?" in prompt


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
    llm = LLM(api_key="gsk_test", model="fake-model")
    tokens = [t async for t in llm.stream_answer("prompt")]
    assert tokens == ["hi", "hi"]
