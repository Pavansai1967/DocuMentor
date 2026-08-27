# DocuMentor

Chat with your PDFs. Upload a PDF, and DocuMentor chunks, embeds, and indexes it, then answers questions about it using retrieval-augmented generation — with the answer citing the exact source pages.

Features:

- Drag-and-drop PDF upload with per-file status (uploading, indexing, ready, failed)
- Document library with status badges and polling while a document is being indexed
- Per-document chat with streaming answers and expandable sources (page numbers + excerpts)
- Stateless chat — every question is answered independently against the document's chunks

## Architecture

FastAPI backend ingests PDFs in background tasks (PyMuPDF parse → token-aware chunking → local `sentence-transformers` embeddings → batched insert into MongoDB Atlas). Chat embeds the question, runs an Atlas `$vectorSearch` aggregation scoped to one `document_id`, builds a stateless prompt, and streams the Groq response as SSE events (`token`, then `sources`, then `done`). React (Vite) frontend provides upload, the library, and chat with a plain-CSS, single-accent design.

Backend modules: `config`, `pdf_parser`, `chunker`, `embeddings`, `mongo_client`, `llm_client`, `schemas`, `deps`, `routes_upload`, `routes_documents`, `routes_chat`, `main`, plus `setup_vector_index.py`.

## Prerequisites

- Python 3.12
- Node 20+
- Free accounts: MongoDB Atlas (M0) and Groq

## 1. MongoDB Atlas (M0 free)

1. Create a cluster (M0 free tier).
2. Create a database user and note the password.
3. Network access: allow access from anywhere (`0.0.0.0/0`) for local development.
4. Get the connection string: Cluster > Connect > Connect your application, replace `<db_password>`, and use `databaseName=documentor_db`.

## 2. Create the Vector Search index

The `chunks` collection must exist first (Atlas cannot host an index on a missing collection). Upload at least one document, or create it with `db.create_collection('chunks')`.

Programmatic (from `backend/`, with `MONGODB_URI` exported):

```bash
python setup_vector_index.py
```

Manual alternative: Atlas > Search > Create Search Index → JSON editor with:

```json
{
  "fields": [
    { "type": "vector", "path": "embedding", "numDimensions": 384, "similarity": "cosine" },
    { "type": "filter", "path": "document_id" }
  ]
}
```

## 3. Environment variables

Copy `backend/.env.example` to `backend/.env` and fill in the values.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `MONGODB_URI` | yes | — | Atlas connection string |
| `GROQ_API_KEY` | yes | — | Groq API key for chat |
| `MONGODB_DB_NAME` | no | `documentor_db` | Database name |
| `LLM_MODEL` | no | `llama-3.1-8b-instant` | Groq model |
| `CHUNK_SIZE` | no | `500` | Chunk size in tokens |
| `CHUNK_OVERLAP` | no | `50` | Chunk overlap in tokens |
| `EMBEDDING_MODEL` | no | `all-MiniLM-L6-v2` | sentence-transformers model |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Comma-separated allowed origins |

## 4. Run locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## 5. Tests

```bash
cd backend
python -m pytest            # unit tests (no external services)
python -m pytest -m live    # live end-to-end test (needs .env)
cd ../frontend
npx vitest run
```

## 6. Deploy backend to Render (free, no Docker)

1. Create a Blueprint from `backend/render.yaml`, or add a New Web Service: root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. Set environment variables (`MONGODB_URI`, `GROQ_API_KEY`).
3. Note:the free tier re-downloads the embedding model(~90MB) on cold start.

## 7. Deploy frontend to Vercel/Netlify (free)

1. Import the repo, root directory `frontend`, build command `npm run build`, output `dist`.
2. Set `VITE_API_BASE_URL=https://<your-render-url>`.
3. Local development defaults to `http://localhost:8000`.

## How it works

- **Upload pipeline:** `POST /upload` returns immediately; a background task parses the PDF, chunks each page's text (continuous `chunk_index`, page-scoped), embeds the chunks with `all-MiniLM-L6-v2` (384-dim, normalized), and inserts them batched into `chunks` alongside the `documents` record .
- **Chat/vector search:** the question is embedded, an Atlas `$vectorSearch` (index `vector_index`, cosine, top-k 4, filtered to the selected `document_id`) returns the most relevant chunks, a stateless prompt asks the model to answer only from those excerpts and cite them as `[1]`, `[2]`, …, and tokens stream back as SSE.
- **Stateless:** each question is answered independently — there is no conversation memory.

## Limitations

- Single user, no authentication.
- No conversation memory between messages.
- M0 free-tier warm-up latency on the first request after idle.
