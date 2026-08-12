import pytest
from fastapi import HTTPException

from app import deps


def test_get_store_raises_503_without_uri(monkeypatch):
    monkeypatch.setattr(deps, "_store", None)
    monkeypatch.setattr(deps.settings, "mongodb_uri", "")
    with pytest.raises(HTTPException) as exc:
        deps.get_store()
    assert exc.value.status_code == 503


def test_get_llm_raises_503_without_key(monkeypatch):
    monkeypatch.setattr(deps, "_llm", None)
    monkeypatch.setattr(deps.settings, "groq_api_key", "")
    with pytest.raises(HTTPException) as exc:
        deps.get_llm()
    assert exc.value.status_code == 503
