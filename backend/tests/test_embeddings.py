from app import embeddings
from app.embeddings import Embedder


class FakeModel:
    def __init__(self):
        self.tokenizer = FakeTokenizer()

    def encode(self, texts, **kwargs):
        import math

        import numpy as np

        unit = np.full(384, 1.0 / math.sqrt(384.0))
        return np.array([unit for _ in texts])


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [1] * len(text.split())


def test_embedder_encode_dim_and_normalization(monkeypatch):
    from unittest.mock import patch

    with patch.object(embeddings, "SentenceTransformer", lambda name: FakeModel()):
        e = Embedder("fake")
        out = e.encode(["hello world", "hi"])
        assert len(out) == 2
        assert len(out[0]) == 384
        import math

        norm = math.sqrt(sum(v * v for v in out[0]))
        assert abs(norm - 1.0) < 1e-6


def test_embedder_count_tokens(monkeypatch):
    from unittest.mock import patch

    with patch.object(embeddings, "SentenceTransformer", lambda name: FakeModel()):
        e = Embedder("fake")
        assert e.count_tokens("one two three") == 3


def test_embedder_lazy_singleton(monkeypatch):
    from unittest.mock import patch

    with patch.object(embeddings, "SentenceTransformer", lambda name: FakeModel()):
        first = embeddings.get_embedder()
        second = embeddings.get_embedder()
        assert first is second