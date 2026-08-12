import threading

from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = SentenceTransformer(self.model_name)

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        self._load()
        vectors = self._model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True
        )
        return [v.tolist() for v in vectors]

    def count_tokens(self, text: str) -> int:
        self._load()
        return len(self._model.tokenizer.encode(text, add_special_tokens=False))


_embedder = None
_embedder_lock = threading.Lock()


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                from .config import settings

                _embedder = Embedder(settings.embedding_model)
    return _embedder