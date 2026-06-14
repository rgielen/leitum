"""Unit tests for config/permissions.py."""

import stat
from pathlib import Path

from leitum.config.permissions import check_file_permissions, create_with_mode


class TestCheckFilePermissions:
    def test_missing_file_ok(self, tmp_path: Path):
        assert check_file_permissions(tmp_path / "nonexistent") is True

    def test_mode_600_ok(self, tmp_path: Path):
        f = tmp_path / "secret"
        f.write_text("data")
        f.chmod(0o600)
        assert check_file_permissions(f) is True

    def test_mode_644_warns(self, tmp_path: Path, capsys):
        f = tmp_path / "secret"
        f.write_text("data")
        f.chmod(0o644)
        result = check_file_permissions(f)
        assert result is False
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestCreateWithMode:
    def test_creates_file_with_mode_600(self, tmp_path: Path):
        p = tmp_path / "new_dir" / "file.yaml"
        create_with_mode(p, "content: 1", mode=0o600)
        assert p.exists()
        assert stat.S_IMODE(p.stat().st_mode) == 0o600
        assert p.read_text() == "content: 1"
