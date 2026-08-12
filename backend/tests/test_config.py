import importlib


def test_settings_defaults(monkeypatch, tmp_path):
    for key in ["MONGODB_URI", "GROQ_API_KEY", "MONGODB_DB_NAME", "LLM_MODEL",
                "CHUNK_SIZE", "CHUNK_OVERLAP", "EMBEDDING_MODEL", "CORS_ORIGINS"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    from app import config
    importlib.reload(config)
    s = config.settings
    assert s.mongodb_db_name == "documentor_db"
    assert s.llm_model == "llama-3.1-8b-instant"
    assert s.chunk_size == 500
    assert s.chunk_overlap == 50
    assert s.embedding_model == "all-MiniLM-L6-v2"
    assert s.cors_origins == "http://localhost:5173"

def test_settings_from_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MONGODB_DB_NAME", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://x:y@localhost/")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("MONGODB_DB_NAME", "custom_db")
    monkeypatch.setenv("CHUNK_SIZE", "300")
    from app import config
    importlib.reload(config)
    s = config.settings
    assert s.mongodb_uri == "mongodb://x:y@localhost/"
    assert s.groq_api_key == "gsk_test"
    assert s.mongodb_db_name == "custom_db"
    assert s.chunk_size == 300