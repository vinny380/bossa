from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_workspace_id_with_tracking
from src.engine import filesystem as fs
from src.models import (BatchRequest, FileBulkCreate, FileCreate, FileEdit,
                        GrepSearchRequest)
from src.usage import LimitError

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/bulk")
async def create_files_bulk(
    body: FileBulkCreate, workspace_id: str = Depends(get_workspace_id_with_tracking)
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
    body: FileCreate, workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Create or overwrite a file."""
    await fs.write_file(workspace_id, body.path, body.content)
    return {"path": body.path, "content": body.content}


@router.get("")
async def get_file(
    path: str, workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Read a file."""
    content = await fs.read_file(workspace_id, path)
    if content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=content)
    return {"path": path, "content": content}


@router.get("/list")
async def list_files(
    path: str = "/",
    metadata: bool = False,
    workspace_id: str = Depends(get_workspace_id_with_tracking),
) -> dict:
    """List files and directories at path. Use metadata=true for size, type, modified."""
    result = await fs.ls(workspace_id, path, include_metadata=metadata)
    if metadata:
        return {"items": result}
    entries = [e.strip() for e in result.split("\n")] if result else []
    return {"items": entries}


@router.get("/glob")
async def glob_files(
    pattern: str,
    path: str = "/",
    workspace_id: str = Depends(get_workspace_id_with_tracking),
) -> dict:
    """Find files matching glob pattern."""
    result = await fs.glob_search(workspace_id, pattern, path)
    items = [line for line in result.split("\n") if line.strip()]
    return {"paths": items}


@router.post("/search")
async def search_files(
    body: GrepSearchRequest, workspace_id: str = Depends(get_workspace_id_with_tracking)
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
    body: FileEdit, workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Replace old_string with new_string. Use replace_all=true for replace-all."""
    msg = await fs.edit_file(
        workspace_id,
        body.path,
        body.old_string,
        body.new_string,
        replace_all=body.replace_all,
    )
    if msg.startswith("Error:"):
        raise HTTPException(status_code=404, detail=msg)
    return {"path": body.path, "edited": True}


@router.delete("")
async def remove_file(
    path: str, workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Delete a file."""
    await fs.delete_file(workspace_id, path)
    return {"path": path, "deleted": True}


@router.get("/stat")
async def stat_file_endpoint(
    path: str, workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Get file metadata: path, size, modified, created."""
    result = await fs.stat_file(workspace_id, path)
    if result is None:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return result


@router.get("/tree")
async def tree_endpoint(
    path: str = "/",
    depth: int | None = None,
    workspace_id: str = Depends(get_workspace_id_with_tracking),
) -> dict:
    """Get directory tree as indented text."""
    result = await fs.tree(workspace_id, path, depth=depth)
    return {"tree": result}


@router.get("/du")
async def du_endpoint(
    path: str = "/", workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Get disk usage per directory."""
    result = await fs.du(workspace_id, path)
    return {"usage": result}


@router.post("/batch")
async def batch_endpoint(
    body: BatchRequest, workspace_id: str = Depends(get_workspace_id_with_tracking)
) -> dict:
    """Execute multiple file ops in one request. Max 100 ops."""
    if not body.ops:
        raise HTTPException(status_code=400, detail="ops array cannot be empty")
    if len(body.ops) > 100:
        raise HTTPException(status_code=413, detail="batch size exceeds 100 ops")
    results = []
    for op in body.ops:
        try:
            if op.op == "read":
                content = await fs.read_file(workspace_id, op.path)
                if content.startswith("Error:"):
                    results.append({"op": "read", "path": op.path, "error": content})
                else:
                    results.append({"op": "read", "path": op.path, "content": content})
            elif op.op == "write":
                if op.content is None:
                    results.append(
                        {"op": "write", "path": op.path, "error": "content required"}
                    )
                else:
                    await fs.write_file(workspace_id, op.path, op.content)
                    results.append({"op": "write", "path": op.path, "wrote": True})
            elif op.op == "delete":
                await fs.delete_file(workspace_id, op.path)
                results.append({"op": "delete", "path": op.path, "deleted": True})
        except LimitError:
            raise
        except Exception as e:
            results.append({"op": op.op, "path": op.path, "error": str(e)})
    return {"results": results}
