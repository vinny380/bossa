from fastapi import APIRouter, HTTPException

from src.config import settings
from src.engine import filesystem as fs
from src.models import FileCreate, FileRead, GrepSearchRequest

router = APIRouter(prefix="/files", tags=["files"])


@router.post("")
async def create_file(body: FileCreate) -> dict:
    """Create or overwrite a file."""
    await fs.write_file(settings.default_workspace_id, body.path, body.content)
    return {"path": body.path, "content": body.content}


@router.get("")
async def get_file(path: str) -> dict:
    """Read a file."""
    content = await fs.read_file(settings.default_workspace_id, path)
    if content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=content)
    return {"path": path, "content": content}


@router.get("/list")
async def list_files(path: str = "/") -> dict:
    """List files and directories at path."""
    result = await fs.ls(settings.default_workspace_id, path)
    entries = [e.strip() for e in result.split("\n")] if result else []
    return {"items": entries}


@router.post("/search")
async def search_files(body: GrepSearchRequest) -> dict:
    """Search file contents for a pattern."""
    result = await fs.grep(
        settings.default_workspace_id, body.pattern, body.path
    )
    return {"results": result}


@router.delete("")
async def remove_file(path: str) -> dict:
    """Delete a file."""
    await fs.delete_file(settings.default_workspace_id, path)
    return {"path": path, "deleted": True}
