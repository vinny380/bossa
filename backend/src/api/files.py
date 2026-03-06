from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_workspace_id
from src.engine import filesystem as fs
from src.models import FileBulkCreate, FileCreate, FileEdit, GrepSearchRequest

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/bulk")
async def create_files_bulk(
    body: FileBulkCreate, workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """Create or overwrite multiple files."""
    if not body.files:
        raise HTTPException(status_code=400, detail="files array cannot be empty")
    if len(body.files) > 100:
        raise HTTPException(status_code=413, detail="batch size exceeds 100 files")
    files_tuples = [(f.path, f.content) for f in body.files]
    result = await fs.write_files_bulk(workspace_id, files_tuples)
    return result


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


@router.get("/glob")
async def glob_files(
    pattern: str, path: str = "/", workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """Find files matching glob pattern."""
    result = await fs.glob_search(workspace_id, pattern, path)
    items = [line for line in result.split("\n") if line.strip()]
    return {"paths": items}


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


@router.patch("")
async def edit_file_endpoint(
    body: FileEdit, workspace_id: str = Depends(get_workspace_id)
) -> dict:
    """Replace first occurrence of old_string with new_string."""
    msg = await fs.edit_file(workspace_id, body.path, body.old_string, body.new_string)
    if msg.startswith("Error:"):
        raise HTTPException(status_code=404, detail=msg)
    return {"path": body.path, "edited": True}


@router.delete("")
async def remove_file(path: str, workspace_id: str = Depends(get_workspace_id)) -> dict:
    """Delete a file."""
    await fs.delete_file(workspace_id, path)
    return {"path": path, "deleted": True}
