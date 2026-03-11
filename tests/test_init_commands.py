"""TDD tests for bossa init command."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


# --- Discovery tests ---


def test_discover_project_paths_finds_agents_md_at_project_root(tmp_path: Path) -> None:
    """Discovery returns AGENTS.md when it exists at project root."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "AGENTS.md").write_text("# Project")
    with patch("cli.init_commands._find_project_root", return_value=tmp_path):
        from cli.init_commands import discover_project_paths

        paths = discover_project_paths(tmp_path)
    assert any("AGENTS.md" in str(p) for p in paths)


def test_discover_project_paths_finds_claude_md_at_project_root(tmp_path: Path) -> None:
    """Discovery returns CLAUDE.md when it exists at project root."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# Claude")
    with patch("cli.init_commands._find_project_root", return_value=tmp_path):
        from cli.init_commands import discover_project_paths

        paths = discover_project_paths(tmp_path)
    assert any("CLAUDE.md" in str(p) for p in paths)


def test_discover_project_paths_finds_gemini_md_at_project_root(tmp_path: Path) -> None:
    """Discovery returns GEMINI.md when it exists at project root."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "GEMINI.md").write_text("# Gemini")
    with patch("cli.init_commands._find_project_root", return_value=tmp_path):
        from cli.init_commands import discover_project_paths

        paths = discover_project_paths(tmp_path)
    assert any("GEMINI.md" in str(p) for p in paths)


def test_discover_global_paths_returns_existing_files(tmp_path: Path) -> None:
    """Discovery returns global paths where file or parent dir exists."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude").mkdir()
    (home / ".claude" / "CLAUDE.md").write_text("# Global")
    with patch("cli.init_commands.Path.home", return_value=home):
        from cli.init_commands import discover_global_paths

        paths = discover_global_paths()
    assert any(".claude" in str(p) and "CLAUDE.md" in str(p) for p in paths)


def test_discover_global_paths_finds_gemini_md(tmp_path: Path) -> None:
    """Discovery returns ~/.gemini/GEMINI.md when it exists."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".gemini").mkdir()
    (home / ".gemini" / "GEMINI.md").write_text("# Gemini")
    with patch("cli.init_commands.Path.home", return_value=home):
        from cli.init_commands import discover_global_paths

        paths = discover_global_paths()
    assert any(".gemini" in str(p) and "GEMINI.md" in str(p) for p in paths)


# --- Template tests ---


def test_bossa_template_contains_expected_keywords() -> None:
    """Bossa section contains commands, exit codes, BOSSA_API_KEY."""
    from cli.init_commands import _get_bossa_template

    template = _get_bossa_template("both")
    assert "bossa files ls" in template
    assert "bossa files read" in template
    assert "bossa files write" in template
    assert "BOSSA_API_KEY" in template
    assert "exit" in template.lower() or "0" in template
    assert "<!-- Bossa: start -->" in template
    assert "<!-- Bossa: end -->" in template
    assert "bossa init --overwrite" in template


# --- Append tests ---


def test_init_append_adds_bossa_section_to_file(tmp_path: Path) -> None:
    """bossa init --path X --yes appends Bossa section to file."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# My Agent\n\nExisting content.\n")
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "Existing content" in content
    assert "<!-- Bossa: start -->" in content
    assert "bossa files ls" in content


def test_init_append_creates_file_if_missing(tmp_path: Path) -> None:
    """bossa init --path X --yes creates file if it does not exist."""
    target = tmp_path / "AGENTS.md"
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--yes"],
    )
    assert result.exit_code == 0
    assert target.exists()
    assert "<!-- Bossa: start -->" in target.read_text()


# --- Overwrite tests ---


def test_init_overwrite_replaces_existing_bossa_section(tmp_path: Path) -> None:
    """bossa init --path X --overwrite --yes replaces existing Bossa section."""
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# My Agent\n\n"
        "<!-- Bossa: start -->\n"
        "old bossa content\n"
        "<!-- Bossa: end -->\n"
    )
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--overwrite", "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "old bossa content" not in content
    assert "bossa files ls" in content
    assert "# My Agent" in content


def test_init_without_overwrite_replaces_existing_bossa_section(tmp_path: Path) -> None:
    """When Bossa section exists, it is replaced (never duplicated)."""
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# My Agent\n\n"
        "<!-- Bossa: start -->\n"
        "old bossa content\n"
        "<!-- Bossa: end -->\n"
    )
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "old bossa content" not in content
    assert "bossa files ls" in content
    assert content.count("<!-- Bossa: start -->") == 1


def test_init_collapses_duplicate_bossa_sections(tmp_path: Path) -> None:
    """Multiple Bossa sections are collapsed into a single one."""
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# My Agent\n\n"
        "<!-- Bossa: start -->\n"
        "first copy\n"
        "<!-- Bossa: end -->\n\n"
        "<!-- Bossa: start -->\n"
        "second copy\n"
        "<!-- Bossa: end -->\n"
    )
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert content.count("<!-- Bossa: start -->") == 1
    assert content.count("<!-- Bossa: end -->") == 1
    assert "first copy" not in content
    assert "second copy" not in content
    assert "bossa files ls" in content


# --- Mode tests ---


def test_init_mode_cli(tmp_path: Path) -> None:
    """--mode cli produces CLI-only content, no MCP."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# Agent")
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--mode", "cli", "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "bossa files ls" in content
    assert "read_file" not in content
    assert "/mcp" not in content.lower()


def test_init_mode_mcp(tmp_path: Path) -> None:
    """--mode mcp produces MCP-only content, no CLI commands."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# Agent")
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--mode", "mcp", "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "read_file" in content
    assert "/mcp" in content.lower()
    assert "bossa files ls" not in content


def test_init_mode_both(tmp_path: Path) -> None:
    """--mode both produces both CLI and MCP sections."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# Agent")
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--mode", "both", "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "bossa files ls" in content
    assert "read_file" in content
    assert "/mcp" in content.lower()


def test_init_default_mode_is_both(tmp_path: Path) -> None:
    """Without --mode, default is both."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# Agent")
    result = runner.invoke(
        app,
        ["init", "--path", str(target), "--yes"],
    )
    assert result.exit_code == 0
    content = target.read_text()
    assert "bossa files ls" in content
    assert "read_file" in content


# --- Confirmation tests ---


def test_init_without_yes_prompts_for_confirmation(tmp_path: Path) -> None:
    """Without --yes, init prompts for confirmation before appending."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# Agent")
    with patch("typer.confirm", return_value=False) as mock_confirm:
        result = runner.invoke(
            app,
            ["init", "--path", str(target)],
            input="n\n",
        )
    mock_confirm.assert_called()
    # User declined, file unchanged
    assert target.read_text() == "# Agent"


def test_init_with_yes_skips_confirmation(tmp_path: Path) -> None:
    """With --yes, init does not prompt and proceeds with append."""
    target = tmp_path / "AGENTS.md"
    target.write_text("# Agent")
    with patch("typer.confirm", return_value=False) as mock_confirm:
        result = runner.invoke(
            app,
            ["init", "--path", str(target), "--yes"],
        )
    mock_confirm.assert_not_called()
    assert "<!-- Bossa: start -->" in target.read_text()


# --- Multi-select tests ---


def test_init_multi_select_updates_only_selected_files(tmp_path: Path) -> None:
    """When multiple files found, checkbox selection updates only selected."""
    (tmp_path / ".git").mkdir()
    agents = tmp_path / "AGENTS.md"
    claude = tmp_path / "CLAUDE.md"
    agents.write_text("# Agent")
    claude.write_text("# Claude")
    with patch.dict(os.environ, {"BOSSA_INIT_FORCE_CHECKBOX": "1"}):
        with patch("cli.init_commands.Path.cwd", return_value=tmp_path):
            with patch("cli.init_commands._find_project_root", return_value=tmp_path):
                with patch("cli.init_commands.discover_global_paths", return_value=[]):
                    mock_checkbox = MagicMock()
                    mock_checkbox.return_value.ask.return_value = [agents]
                    mock_select = MagicMock()
                    mock_select.return_value.ask.return_value = "both"
                    with patch("cli.init_commands.questionary.checkbox", mock_checkbox):
                        with patch("cli.init_commands.questionary.select", mock_select):
                            result = runner.invoke(app, ["init"])
    assert mock_checkbox.called, "checkbox should have been called"
    assert result.exit_code == 0
    assert "<!-- Bossa: start -->" in agents.read_text()
    assert "<!-- Bossa: start -->" not in claude.read_text()


def test_init_multi_select_none_exits_gracefully(tmp_path: Path) -> None:
    """Selecting no files exits without writing."""
    (tmp_path / ".git").mkdir()
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Agent")
    with patch.dict(os.environ, {"BOSSA_INIT_FORCE_CHECKBOX": "1"}):
        with patch("cli.init_commands.Path.cwd", return_value=tmp_path):
            with patch("cli.init_commands._find_project_root", return_value=tmp_path):
                with patch("cli.init_commands.questionary.checkbox") as mock_checkbox:
                    mock_checkbox.return_value.ask.return_value = []
                    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert agents.read_text() == "# Agent"


def test_init_multi_select_cancel_exits_gracefully(tmp_path: Path) -> None:
    """Cancelling checkbox (None) exits without writing."""
    (tmp_path / ".git").mkdir()
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Agent")
    with patch.dict(os.environ, {"BOSSA_INIT_FORCE_CHECKBOX": "1"}):
        with patch("cli.init_commands.Path.cwd", return_value=tmp_path):
            with patch("cli.init_commands._find_project_root", return_value=tmp_path):
                with patch("cli.init_commands.questionary.checkbox") as mock_checkbox:
                    mock_checkbox.return_value.ask.return_value = None
                    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert agents.read_text() == "# Agent"
