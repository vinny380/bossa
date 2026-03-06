from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import get_workspace_id
from src.engine import filesystem as fs
from src.models import FileCreate, FileRead, GrepSearchRequest

router = APIRouter(prefix="/files", tags=["files"])


@router.post("")
async def create_file(
    body: FileCreate, workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """Create or overwrite a file."""
    await fs.write_file(workspace_id, body.path, body.content)
    return {"path": body.path, "content": body.content}


@router.get("")
async def get_file(path: str, workspace_id: str = Depends(get_workspace_id)) -> dict:
    """Read a file."""
    content = await fs.read_file(workspace_id, path)
    if content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=content)
    return {"path": path, "content": content}


@router.get("/list")
async def list_files(
    path: str = "/", workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """List files and directories at path."""
    result = await fs.ls(workspace_id, path)
    entries = [e.strip() for e in result.split("\n")] if result else []
    return {"items": entries}


@router.post("/search")
async def search_files(
    body: GrepSearchRequest, workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """Search file contents for a pattern."""
    result = await fs.grep(workspace_id, body.pattern, body.path)
    return {"results": result}


@router.delete("")
async def remove_file(
    path: str, workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """Delete a file."""
    await fs.delete_file(workspace_id, path)
    return {"path": path, "deleted": True}
