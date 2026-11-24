from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database import init_db
from app.api.v1.router import api_router

settings = get_settings()
logger = setup_logging(debug=settings.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    logger.info("Initializing relational database tables...")
    init_db()
    logger.info("Application '%s' initialized and ready.", settings.APP_NAME)
    yield
    logger.info("Application shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend RAG pipeline and coaching engine for AI Customer Support Coaching Assistant (Milestone 1)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for live frontend console
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing request %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.PORT, reload=True)
