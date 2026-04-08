from fastapi import APIRouter

from app.api.routes import global_config
from app.api.routes import tasks

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(global_config.router)
api_router.include_router(tasks.router)
