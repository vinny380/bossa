import pytest
from src.engine.filesystem import (delete_file, edit_file, glob_search, grep,
                                   ls, read_file, write_file)


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
    """grep returns structured match results for a literal pattern."""
    path = "/test/grep-basic/grep-file.txt"
    await write_file(workspace_id, path, "line1\nneedle here\nline3")
    result = await grep(workspace_id, "needle", "/test/grep-basic/")
    assert result.output_mode == "matches"
    assert result.total_matches == 1
    assert result.returned_matches == 1
    assert result.has_more is False
    assert len(result.matches) == 1
    assert result.matches[0].path == path
    assert result.matches[0].line_number == 2
    assert "needle here" in result.matches[0].line
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_grep_case_sensitive_search(workspace_id: str) -> None:
    """grep can do case-sensitive matching."""
    path = "/test/grep-case/grep-case.txt"
    await write_file(workspace_id, path, "Needle here\nneedle here")
    result = await grep(workspace_id, "Needle", "/test/grep-case/", case_sensitive=True)
    assert result.total_matches == 1
    assert result.matches[0].line_number == 1
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_grep_regex_search(workspace_id: str) -> None:
    """grep can do regex matching."""
    path = "/test/grep-regex/grep-regex.txt"
    await write_file(workspace_id, path, "ticket-001\nticket-abc\norder-123")
    result = await grep(workspace_id, r"ticket-\d+", "/test/grep-regex/", regex=True)
    assert result.total_matches == 1
    assert result.matches[0].line == "ticket-001"
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_grep_supports_all_any_none_of(workspace_id: str) -> None:
    """grep supports structured include and exclude criteria."""
    path = "/test/grep-criteria/grep-criteria.txt"
    await write_file(
        workspace_id,
        path,
        "enterprise pricing\nstarter pricing\nenterprise onboarding",
    )
    result = await grep(
        workspace_id,
        path="/test/grep-criteria/",
        all_of=["enterprise"],
        any_of=["pricing", "discount"],
        none_of=["starter"],
    )
    assert result.total_matches == 1
    assert result.matches[0].line == "enterprise pricing"
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_grep_files_with_matches_output_mode(workspace_id: str) -> None:
    """grep can return only file paths with matches."""
    path_a = "/test/grep-files/a.txt"
    path_b = "/test/grep-files/b.txt"
    await write_file(workspace_id, path_a, "enterprise account")
    await write_file(workspace_id, path_b, "starter account")
    result = await grep(
        workspace_id,
        "enterprise",
        "/test/grep-files/",
        output_mode="files_with_matches",
    )
    assert result.output_mode == "files_with_matches"
    assert result.files == [path_a]
    assert result.total_matches == 1
    await delete_file(workspace_id, path_a)
    await delete_file(workspace_id, path_b)


@pytest.mark.asyncio
async def test_grep_count_output_mode(workspace_id: str) -> None:
    """grep can return only a count."""
    path = "/test/grep-count/grep-count.txt"
    await write_file(workspace_id, path, "match one\nmatch two\nnope")
    result = await grep(
        workspace_id,
        "match",
        "/test/grep-count/",
        output_mode="count",
    )
    assert result.output_mode == "count"
    assert result.total_matches == 2
    assert result.count == 2
    assert result.matches == []
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_grep_paginates_matches(workspace_id: str) -> None:
    """grep paginates over matches with metadata."""
    path = "/test/grep-page/grep-page.txt"
    await write_file(workspace_id, path, "hit 1\nhit 2\nhit 3")
    result = await grep(
        workspace_id,
        "hit",
        "/test/grep-page/",
        max_matches=2,
        offset=1,
    )
    assert result.total_matches == 3
    assert result.returned_matches == 2
    assert result.has_more is False
    assert result.next_offset is None
    assert [match.line_number for match in result.matches] == [2, 3]
    await delete_file(workspace_id, path)


@pytest.mark.asyncio
async def test_grep_returns_context_lines(workspace_id: str) -> None:
    """grep returns surrounding context lines when requested."""
    path = "/test/grep-context/grep-context.txt"
    await write_file(workspace_id, path, "before\nneedle\nafter")
    result = await grep(
        workspace_id,
        "needle",
        "/test/grep-context/",
        context_before=1,
        context_after=1,
    )
    assert result.total_matches == 1
    assert result.matches[0].context_before == ["before"]
    assert result.matches[0].context_after == ["after"]
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
async def test_glob_search_with_base_path_returns_only_scoped_files(
    workspace_id: str,
) -> None:
    """glob_search with base_path scopes to that directory only."""
    await write_file(workspace_id, "/test/glob-scope/customers/acme/profile.md", "a")
    await write_file(workspace_id, "/test/glob-scope/customers/globex/profile.md", "b")
    await write_file(workspace_id, "/test/glob-scope/tickets/ticket-001.md", "c")
    result = await glob_search(
        workspace_id, "*.md", base_path="/test/glob-scope/customers/"
    )
    assert "/test/glob-scope/customers/acme/profile.md" in result
    assert "/test/glob-scope/customers/globex/profile.md" in result
    assert "/test/glob-scope/tickets/ticket-001.md" not in result
    await delete_file(workspace_id, "/test/glob-scope/customers/acme/profile.md")
    await delete_file(workspace_id, "/test/glob-scope/customers/globex/profile.md")
    await delete_file(workspace_id, "/test/glob-scope/tickets/ticket-001.md")


@pytest.mark.asyncio
async def test_glob_search_with_root_base_path_returns_all_matching(
    workspace_id: str,
) -> None:
    """glob_search with base_path=/ returns all .md files in workspace."""
    await write_file(workspace_id, "/test/glob-root/a.md", "a")
    await write_file(workspace_id, "/test/glob-root/b/c.md", "b")
    result = await glob_search(workspace_id, "*.md", base_path="/")
    assert "/test/glob-root/a.md" in result
    assert "/test/glob-root/b/c.md" in result
    await delete_file(workspace_id, "/test/glob-root/a.md")
    await delete_file(workspace_id, "/test/glob-root/b/c.md")


@pytest.mark.asyncio
async def test_glob_search_absolute_pattern_ignores_base_path(
    workspace_id: str,
) -> None:
    """glob_search with absolute pattern ignores base_path."""
    await write_file(workspace_id, "/test/glob-abs/tickets/ticket-001.md", "a")
    await write_file(workspace_id, "/test/glob-abs/customers/acme.md", "b")
    result = await glob_search(
        workspace_id,
        "/test/glob-abs/tickets/*.md",
        base_path="/test/glob-abs/customers/",
    )
    assert "/test/glob-abs/tickets/ticket-001.md" in result
    assert "/test/glob-abs/customers/acme.md" not in result
    await delete_file(workspace_id, "/test/glob-abs/tickets/ticket-001.md")
    await delete_file(workspace_id, "/test/glob-abs/customers/acme.md")


@pytest.mark.asyncio
async def test_glob_search_relative_pattern_with_segments(
    workspace_id: str,
) -> None:
    """glob_search with base_path and pattern like */profile.md returns nested paths."""
    await write_file(workspace_id, "/test/glob-nested/acme/profile.md", "a")
    await write_file(workspace_id, "/test/glob-nested/globex/profile.md", "b")
    result = await glob_search(
        workspace_id, "*/profile.md", base_path="/test/glob-nested/"
    )
    assert "/test/glob-nested/acme/profile.md" in result
    assert "/test/glob-nested/globex/profile.md" in result
    await delete_file(workspace_id, "/test/glob-nested/acme/profile.md")
    await delete_file(workspace_id, "/test/glob-nested/globex/profile.md")


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
