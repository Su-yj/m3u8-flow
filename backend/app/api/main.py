from fastapi import APIRouter, Depends

from app.api.deps import jwt_auth_dependency
from app.api.routes import auth, global_config, tasks

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(
    global_config.router, dependencies=[Depends(jwt_auth_dependency)]
)
api_router.include_router(tasks.router, dependencies=[Depends(jwt_auth_dependency)])
api_router.include_router(auth.router)
