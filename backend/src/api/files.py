from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_workspace_id
from src.engine import filesystem as fs
from src.models import FileCreate, GrepSearchRequest

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
    """Search file contents with agent-friendly criteria and pagination."""
    result = await fs.grep(
        workspace_id,
        pattern=body.pattern,
        path=body.path,
        regex=body.regex,
        case_sensitive=body.case_sensitive,
        whole_word=body.whole_word,
        max_matches=body.max_matches,
        offset=body.offset,
        output_mode=body.output_mode,
        all_of=body.all_of,
        any_of=body.any_of,
        none_of=body.none_of,
        context_before=body.context_before,
        context_after=body.context_after,
    )
    return result.model_dump()


@router.delete("")
async def remove_file(path: str, workspace_id: str = Depends(get_workspace_id)) -> dict:
    """Delete a file."""
    await fs.delete_file(workspace_id, path)
    return {"path": path, "deleted": True}
