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
