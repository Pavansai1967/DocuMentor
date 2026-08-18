import importlib


def test_settings_defaults(monkeypatch, tmp_path):
    for key in ["MONGODB_URI", "GROQ_API_KEY", "MONGODB_DB_NAME", "PLAN_MODEL",
                "EVALUATE_MODEL", "ANSWER_MODEL", "CHUNK_SIZE", "CHUNK_OVERLAP",
                "EMBEDDING_MODEL", "CORS_ORIGINS", "MAX_AGENT_ITERATIONS",
                "DEFAULT_TOP_K", "MAX_ACCUMULATED_CHUNKS"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir(tmp_path)
    from app import config
    importlib.reload(config)
    s = config.settings
    assert s.mongodb_db_name == "documentor_db"
    assert s.plan_model == "qwen/qwen3.6-27b"
    assert s.evaluate_model == "openai/gpt-oss-20b"
    assert s.answer_model == "openai/gpt-oss-120b"
    assert s.chunk_size == 500
    assert s.chunk_overlap == 50
    assert s.embedding_model == "all-MiniLM-L6-v2"
    assert s.cors_origins == "http://localhost:5173"
    assert s.max_agent_iterations == 2
    assert s.default_top_k == 3
    assert s.max_accumulated_chunks == 10


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
