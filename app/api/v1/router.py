from fastapi import APIRouter
from app.api.v1.endpoints import kb, health, session

api_router = APIRouter(prefix="/api")
api_router.include_router(kb.router)
api_router.include_router(health.router)
api_router.include_router(session.router)
