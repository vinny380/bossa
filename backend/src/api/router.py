from fastapi import APIRouter
from src.api.files import router as files_router
from src.api.keys import router as keys_router
from src.api.workspaces import router as workspaces_router

api_router = APIRouter()
api_router.include_router(files_router)
api_router.include_router(workspaces_router)
api_router.include_router(keys_router)
