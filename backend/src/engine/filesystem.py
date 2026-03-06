import re
from typing import Literal

from src.db import fetch_one, fetch_all, execute
from src.engine.path_utils import escape_for_like, glob_to_sql_like, normalize_path
from src.models import GrepMatch, GrepSearchRequest, GrepSearchResponse


async def ls(workspace_id: str, path: str = "/") -> str:
    """List files and directories at the given path."""
    path = normalize_path(path)
    if not path.endswith("/"):
        path = path + "/"

    rows = await fetch_all(
        """
        SELECT path FROM files
        WHERE workspace_id = $1 AND path LIKE $2
        """,
        workspace_id,
        path + "%",
    )

    if not rows:
        return ""

    seen: set[str] = set()
    entries: list[str] = []
    for row in rows:
        rest = row["path"][len(path) :]
        if not rest:
            continue
        parts = rest.split("/")
        name = parts[0]
        if name in seen:
            continue
        seen.add(name)
        if len(parts) > 1:
            entries.append(name + "/")
        else:
            entries.append(name)

    return "\n".join(sorted(entries)) if entries else ""


async def read_file(workspace_id: str, path: str) -> str:
    """Read the contents of a file. Returns content with line numbers (LangChain convention)."""
    path = normalize_path(path)
    row = await fetch_one(
        "SELECT content FROM files WHERE workspace_id = $1 AND path = $2",
        workspace_id,
        path,
    )
    if not row:
        return f"Error: File not found: {path}"
    content = row["content"]
    lines = content.split("\n")
    return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))


async def write_file(workspace_id: str, path: str, content: str) -> str:
    """Create or overwrite a file."""
    path = normalize_path(path)
    await execute(
        """
        INSERT INTO files (workspace_id, path, content)
        VALUES ($1, $2, $3)
        ON CONFLICT (workspace_id, path) DO UPDATE SET
            content = EXCLUDED.content,
            updated_at = NOW()
        """,
        workspace_id,
        path,
        content,
    )
    return f"Wrote {path}"


async def edit_file(
    workspace_id: str, path: str, old_string: str, new_string: str
) -> str:
    """Replace old_string with new_string in a file."""
    path = normalize_path(path)
    row = await fetch_one(
        "SELECT content FROM files WHERE workspace_id = $1 AND path = $2",
        workspace_id,
        path,
    )
    if not row:
        return f"Error: File not found: {path}"
    content = row["content"]
    if old_string not in content:
        return f"Error: old_string not found in {path}"
    new_content = content.replace(old_string, new_string, 1)
    await write_file(workspace_id, path, new_content)
    return f"Edited {path}"


def _build_path_like_pattern(path_glob: str) -> str:
    path_glob = normalize_path(path_glob)
    if path_glob.endswith("/"):
        return path_glob + "%"
    if "*" in path_glob or "?" in path_glob:
        return glob_to_sql_like(path_glob)
    return path_glob + "%"


def _line_matches_term(
    line: str,
    term: str,
    *,
    regex: bool,
    case_sensitive: bool,
    whole_word: bool,
) -> bool:
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.search(term, line, flags) is not None

    if whole_word:
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.search(rf"\b{re.escape(term)}\b", line, flags) is not None

    if case_sensitive:
        return term in line
    return term.lower() in line.lower()


def _line_matches_request(line: str, request: GrepSearchRequest) -> bool:
    positive_terms: list[str] = []
    if request.pattern:
        positive_terms.append(request.pattern)
    positive_terms.extend(request.all_of)

    if positive_terms and not all(
        _line_matches_term(
            line,
            term,
            regex=request.regex,
            case_sensitive=request.case_sensitive,
            whole_word=request.whole_word,
        )
        for term in positive_terms
    ):
        return False

    if request.any_of and not any(
        _line_matches_term(
            line,
            term,
            regex=request.regex,
            case_sensitive=request.case_sensitive,
            whole_word=request.whole_word,
        )
        for term in request.any_of
    ):
        return False

    if request.none_of and any(
        _line_matches_term(
            line,
            term,
            regex=request.regex,
            case_sensitive=request.case_sensitive,
            whole_word=request.whole_word,
        )
        for term in request.none_of
    ):
        return False

    return True


def _sql_match_clause(
    field: str,
    placeholder: int,
    search_term: str,
    *,
    regex: bool,
    case_sensitive: bool,
) -> tuple[str, str]:
    if regex:
        return (f"{field} {'~' if case_sensitive else '~*'} ${placeholder}", search_term)
    operator = "LIKE" if case_sensitive else "ILIKE"
    return (f"{field} {operator} ${placeholder}", f"%{search_term}%")


async def grep(
    workspace_id: str,
    pattern: str | None = None,
    path: str = "/",
    *,
    regex: bool = False,
    case_sensitive: bool = False,
    whole_word: bool = False,
    max_matches: int = 100,
    offset: int = 0,
    output_mode: Literal["matches", "files_with_matches", "count"] = "matches",
    all_of: list[str] | None = None,
    any_of: list[str] | None = None,
    none_of: list[str] | None = None,
    context_before: int = 0,
    context_after: int = 0,
) -> GrepSearchResponse:
    """Search file contents using one agent-friendly grep surface."""
    request = GrepSearchRequest(
        pattern=pattern,
        path=path,
        regex=regex,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        max_matches=max_matches,
        offset=offset,
        output_mode=output_mode,
        all_of=all_of or [],
        any_of=any_of or [],
        none_of=none_of or [],
        context_before=context_before,
        context_after=context_after,
    )

    like_pattern = _build_path_like_pattern(request.path)
    query = [
        "SELECT path, content FROM files",
        "WHERE workspace_id = $1 AND path LIKE $2",
    ]
    args: list[object] = [workspace_id, like_pattern]
    placeholder = 3

    required_terms: list[str] = []
    if request.pattern:
        required_terms.append(request.pattern)
    required_terms.extend(request.all_of)

    for term in required_terms:
        clause, value = _sql_match_clause(
            "content",
            placeholder,
            term,
            regex=request.regex,
            case_sensitive=request.case_sensitive,
        )
        query.append(f"AND {clause}")
        args.append(value)
        placeholder += 1

    if request.any_of:
        any_clauses: list[str] = []
        for term in request.any_of:
            clause, value = _sql_match_clause(
                "content",
                placeholder,
                term,
                regex=request.regex,
                case_sensitive=request.case_sensitive,
            )
            any_clauses.append(clause)
            args.append(value)
            placeholder += 1
        query.append(f"AND ({' OR '.join(any_clauses)})")

    rows = await fetch_all("\n".join(query), *args)

    matches: list[GrepMatch] = []
    matching_files: set[str] = set()
    for row in rows:
        file_path = row["path"]
        lines = row["content"].split("\n")
        for index, line in enumerate(lines):
            if not _line_matches_request(line, request):
                continue
            matching_files.add(file_path)
            matches.append(
                GrepMatch(
                    path=file_path,
                    line_number=index + 1,
                    line=line,
                    context_before=lines[max(0, index - request.context_before) : index],
                    context_after=lines[
                        index + 1 : index + 1 + request.context_after
                    ],
                )
            )

    if request.output_mode == "count":
        return GrepSearchResponse(
            output_mode="count",
            count=len(matches),
            total_matches=len(matches),
            returned_matches=0,
            has_more=False,
            next_offset=None,
        )

    if request.output_mode == "files_with_matches":
        files = sorted(matching_files)
        paged_files = files[request.offset : request.offset + request.max_matches]
        next_offset = request.offset + len(paged_files)
        has_more = next_offset < len(files)
        return GrepSearchResponse(
            output_mode="files_with_matches",
            files=paged_files,
            count=len(files),
            total_matches=len(files),
            returned_matches=len(paged_files),
            has_more=has_more,
            next_offset=next_offset if has_more else None,
        )

    paged_matches = matches[request.offset : request.offset + request.max_matches]
    next_offset = request.offset + len(paged_matches)
    has_more = next_offset < len(matches)
    return GrepSearchResponse(
        output_mode="matches",
        matches=paged_matches,
        count=len(matches),
        total_matches=len(matches),
        returned_matches=len(paged_matches),
        has_more=has_more,
        next_offset=next_offset if has_more else None,
    )


async def glob_search(workspace_id: str, pattern: str, base_path: str = "/") -> str:
    """Find files matching a glob pattern. base_path scopes the search to that directory."""
    pattern = pattern.strip()
    base_path = normalize_path(base_path)

    if pattern.startswith("/"):
        like_pattern = glob_to_sql_like(normalize_path(pattern))
    else:
        if not base_path.endswith("/"):
            base_path = base_path + "/"
        like_pattern = escape_for_like(base_path) + glob_to_sql_like(pattern)

    rows = await fetch_all(
        """
        SELECT path FROM files
        WHERE workspace_id = $1 AND path LIKE $2
        ORDER BY path
        """,
        workspace_id,
        like_pattern,
    )
    return "\n".join(r["path"] for r in rows)


async def delete_file(workspace_id: str, path: str) -> str:
    """Delete a file."""
    path = normalize_path(path)
    await execute(
        "DELETE FROM files WHERE workspace_id = $1 AND path = $2",
        workspace_id,
        path,
    )
    return f"Deleted {path}"
