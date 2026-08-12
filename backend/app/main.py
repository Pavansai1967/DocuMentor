from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from .config import settings
from .routes_chat import router as chat_router
from .routes_documents import router as documents_router
from .routes_upload import router as upload_router


def create_app() -> FastAPI:
    app = FastAPI(title="DocuMentor")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(upload_router)
    app.include_router(documents_router)
    app.include_router(chat_router)

    @app.exception_handler(PyMongoError)
    async def mongo_error_handler(request: Request, exc: PyMongoError):
        return JSONResponse(status_code=503, content={"detail": f"Database error: {exc}"})

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
