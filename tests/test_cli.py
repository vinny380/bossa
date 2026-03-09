"""CLI tests for file upload commands."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_bossa_url():
    """Point CLI at test ASGI app."""
    with patch.dict(
        os.environ,
        {"BOSSA_API_KEY": "sk-default", "BOSSA_API_URL": "http://test"},
    ):
        with patch("cli.files.BOSSA_API_URL", "http://test"):
            yield


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.Client to return success for post requests."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"created": 1, "updated": 0, "failed": []}

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        yield


@pytest.fixture
def temp_file(tmp_path):
    """Create a temp file with content."""
    f = tmp_path / "hello.txt"
    f.write_text("Hello from CLI test")
    return f


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temp dir with nested files."""
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("c")
    return tmp_path


def test_files_put_uploads_single(mock_httpx_client, mock_bossa_url, temp_file) -> None:
    """bossa files put uploads a single file."""
    result = runner.invoke(
        app,
        ["files", "put", str(temp_file), "--target", "/test/cli-put/hello.txt"],
    )
    assert result.exit_code == 0
    assert "Uploaded" in result.output


def test_files_upload_bulk(mock_httpx_client, mock_bossa_url, temp_dir) -> None:
    """bossa files upload uploads a directory."""
    result = runner.invoke(
        app,
        ["files", "upload", str(temp_dir), "--target", "/test/cli-upload"],
    )
    assert result.exit_code == 0
    assert "Uploaded" in result.output or "files" in result.output.lower()


def test_files_ls_returns_items(mock_bossa_url) -> None:
    """bossa files ls outputs directory items."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": ["a/", "b.txt"]}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "ls", "/"])
    assert result.exit_code == 0
    assert "a/" in result.output
    assert "b.txt" in result.output


def test_files_ls_json_output(mock_bossa_url) -> None:
    """bossa files ls --json outputs valid JSON."""
    import json

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": ["docs/", "readme.txt"]}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "ls", "/", "--json"])
    assert result.exit_code == 0
    # Extract JSON line (banner may precede it)
    for line in result.output.split("\n"):
        if line.strip().startswith("{"):
            data = json.loads(line)
            break
    else:
        pytest.fail("No JSON in output")
    assert "items" in data
    assert "docs/" in data["items"]


def test_files_read_outputs_content(mock_bossa_url) -> None:
    """bossa files read outputs file content to stdout."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": "/x.txt", "content": "1: hello world"}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "read", "/x.txt"])
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_files_delete_removes_file(mock_bossa_url) -> None:
    """bossa files delete succeeds."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": "/test/delete.txt", "deleted": True}
    mock_client = MagicMock()
    mock_client.delete.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "delete", "/test/delete.txt"])
    assert result.exit_code == 0
    assert "Deleted" in result.output or "deleted" in result.output.lower()


def test_files_write_from_stdin(mock_bossa_url) -> None:
    """bossa files write reads content from stdin."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "path": "/test/stdin.txt",
        "content": "from stdin",
    }
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(
            app, ["files", "write", "/test/stdin.txt"], input="from stdin"
        )
    assert result.exit_code == 0
    mock_client.post.assert_called_once()
    call_json = mock_client.post.call_args[1]["json"]
    assert call_json["path"] == "/test/stdin.txt"
    assert call_json["content"] == "from stdin"


def test_files_write_from_content(mock_bossa_url) -> None:
    """bossa files write --content works."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": "/x.txt", "content": "hello"}
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "write", "/x.txt", "--content", "hello"])
    assert result.exit_code == 0
    call_json = mock_client.post.call_args[1]["json"]
    assert call_json["content"] == "hello"


def test_files_grep_returns_matches(mock_bossa_url) -> None:
    """bossa files grep returns matches."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output_mode": "matches",
        "matches": [{"path": "/a.txt", "line_number": 1, "line": "needle here"}],
        "has_more": False,
    }
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "grep", "needle", "--path", "/"])
    assert result.exit_code == 0
    assert "needle" in result.output


def test_files_glob_returns_paths(mock_bossa_url) -> None:
    """bossa files glob returns matching paths."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"paths": ["/docs/a.md", "/docs/b.md"]}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(app, ["files", "glob", "*.md", "--path", "/docs/"])
    assert result.exit_code == 0
    assert "/docs/a.md" in result.output
    assert "/docs/b.md" in result.output


def test_files_edit_replaces_string(mock_bossa_url) -> None:
    """bossa files edit --old X --new Y works."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"path": "/config.txt", "edited": True}
    mock_client = MagicMock()
    mock_client.patch.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.files.httpx.Client", return_value=mock_client):
        result = runner.invoke(
            app,
            ["files", "edit", "/config.txt", "--old", "foo", "--new", "bar"],
        )
    assert result.exit_code == 0
    call_json = mock_client.patch.call_args[1]["json"]
    assert call_json["path"] == "/config.txt"
    assert call_json["old_string"] == "foo"
    assert call_json["new_string"] == "bar"


def test_files_ls_json_when_env_set(mock_bossa_url) -> None:
    """BOSSA_CLI_JSON=1 yields JSON output without --json flag."""
    import json

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": ["agent-mode/"]}
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch.dict(os.environ, {"BOSSA_CLI_JSON": "1"}, clear=False):
        with patch("cli.files.httpx.Client", return_value=mock_client):
            result = runner.invoke(app, ["files", "ls", "/"])
    assert result.exit_code == 0
    for line in result.output.split("\n"):
        if line.strip().startswith("{"):
            data = json.loads(line)
            assert "items" in data
            assert "agent-mode/" in data["items"]
            break
    else:
        pytest.fail("No JSON in output")


def test_keys_create_with_save_calls_set_active_workspace() -> None:
    """bossa keys create my-app --save stores key in config."""
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = [
        {"id": "9f2b6471-b966-44b8-bc99-403877666923", "name": "my-app"},
    ]
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {"key": "sk-new-key-123"}

    mock_client = MagicMock()
    mock_client.get.return_value = mock_get_resp
    mock_client.post.return_value = mock_post_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=None)

    with patch("cli.keys.get_access_token", return_value="fake-token"):
        with patch("cli.keys.httpx.Client", return_value=mock_client):
            with patch("cli.keys.set_active_workspace") as mock_set:
                result = runner.invoke(app, ["keys", "create", "my-app", "--save"])
    assert result.exit_code == 0
    mock_set.assert_called_once_with("my-app", "9f2b6471-b966-44b8-bc99-403877666923", "sk-new-key-123")
    assert "Active workspace: my-app" in result.output
