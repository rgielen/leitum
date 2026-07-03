"""Unit tests for load_dotenv_file in config/io.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from leitum.config.io import load_dotenv_file


class TestLoadDotenvFile:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = load_dotenv_file(tmp_path / ".leitumenv")
        assert result == {}

    def test_directory_path_returns_empty(self, tmp_path: Path) -> None:
        result = load_dotenv_file(tmp_path)
        assert result == {}

    def test_parses_simple_pair(self, tmp_path: Path) -> None:
        (tmp_path / ".leitumenv").write_text("MY_TOKEN=hello\n", encoding="utf-8")
        result = load_dotenv_file(tmp_path / ".leitumenv")
        assert result == {"MY_TOKEN": "hello"}

    def test_skips_comments_and_blank_lines(self, tmp_path: Path) -> None:
        content = "# comment\n\nFOO=bar\n"
        (tmp_path / ".leitumenv").write_text(content, encoding="utf-8")
        result = load_dotenv_file(tmp_path / ".leitumenv")
        assert result == {"FOO": "bar"}

    def test_strips_export_prefix(self, tmp_path: Path) -> None:
        (tmp_path / ".leitumenv").write_text("export TOKEN=secret\n", encoding="utf-8")
        result = load_dotenv_file(tmp_path / ".leitumenv")
        assert result == {"TOKEN": "secret"}

    def test_command_substitution(self, tmp_path: Path) -> None:
        (tmp_path / ".leitumenv").write_text(
            'export MY_VAR="$(echo hello_from_shell)"\n', encoding="utf-8"
        )
        result = load_dotenv_file(tmp_path / ".leitumenv")
        assert result == {"MY_VAR": "hello_from_shell"}

    def test_verbose_logs_file_name(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dotenv = tmp_path / ".leitumenv"
        dotenv.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
        load_dotenv_file(dotenv, verbose=True)
        captured = capsys.readouterr()
        assert str(dotenv) in captured.err
        assert "bar" not in captured.err
        assert "qux" not in captured.err

    def test_verbose_warns_malformed_line(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        dotenv = tmp_path / ".leitumenv"
        dotenv.write_text("GOOD=value\nBADLINE\n", encoding="utf-8")
        load_dotenv_file(dotenv, verbose=True)
        captured = capsys.readouterr()
        assert "malformed" in captured.err
        assert "BADLINE" not in captured.err  # content of line must not be logged

    def test_verbose_missing_file_no_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        load_dotenv_file(tmp_path / "nonexistent", verbose=True)
        captured = capsys.readouterr()
        assert captured.err == ""
        assert captured.out == ""
