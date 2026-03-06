import pytest
from src.engine.filesystem import (
    ls,
    read_file,
    write_file,
    edit_file,
    grep,
    glob_search,
    delete_file,
)


@pytest.fixture
def workspace_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_write_file_then_read_file_returns_content(
    workspace_id: str,
) -> None:
    """write_file then read_file returns the content."""
    path = "/test/write-read.txt"
    content = "Hello, filesystem!"
    await write_file(workspace_id, path, content)
    result = await read_file(workspace_id, path)
    assert "Hello, filesystem!" in result
    assert result.startswith("1: ")  # LangChain line number convention
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_ls_on_empty_returns_empty(workspace_id: str) -> None:
    """ls on empty directory returns empty."""
    path = "/test/empty-dir/"
    result = await ls(workspace_id, path)
    assert result == "" or "empty" in result.lower() or len(result.strip()) == 0


@pytest.mark.asyncio
async def test_ls_after_write_returns_path(workspace_id: str) -> None:
    """ls after write returns the path."""
    path = "/test/ls-check/"
    file_path = "/test/ls-check/file.txt"
    await write_file(workspace_id, file_path, "content")
    result = await ls(workspace_id, path)
    assert "file.txt" in result
    await delete_file(workspace_id, file_path)


@pytest.mark.asyncio
async def test_grep_finds_pattern(workspace_id: str) -> None:
    """grep finds a pattern in file content."""
    path = "/test/grep-file.txt"
    await write_file(workspace_id, path, "line1\nneedle here\nline3")
    result = await grep(workspace_id, "needle", "/test/")
    assert "needle" in result
    assert path in result or "grep-file" in result
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_glob_matches_paths(workspace_id: str) -> None:
    """glob matches paths."""
    await write_file(workspace_id, "/test/glob/a.md", "a")
    await write_file(workspace_id, "/test/glob/b.md", "b")
    result = await glob_search(workspace_id, "/test/glob/*.md")
    assert "a.md" in result or "/test/glob/a.md" in result
    assert "b.md" in result or "/test/glob/b.md" in result
    await delete_file(workspace_id, "/test/glob/a.md")
    await delete_file(workspace_id, "/test/glob/b.md")


@pytest.mark.asyncio
async def test_delete_file_removes_file(workspace_id: str) -> None:
    """delete_file removes a file."""
    path = "/test/delete-me.txt"
    await write_file(workspace_id, path, "to be deleted")
    await delete_file(workspace_id, path)
    result = await read_file(workspace_id, path)
    assert "not found" in result.lower() or "error" in result.lower() or result == ""


@pytest.mark.asyncio
async def test_edit_file_replaces_string(workspace_id: str) -> None:
    """edit_file replaces old_string with new_string."""
    path = "/test/edit-file.txt"
    await write_file(workspace_id, path, "old content here")
    await edit_file(workspace_id, path, "old content", "new content")
    result = await read_file(workspace_id, path)
    assert "new content" in result
    assert "old content" not in result
    await delete_file(workspace_id, path)
