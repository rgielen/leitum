"""Tests for atomic I/O in provider add/remove commands."""

from __future__ import annotations

import stat
from io import StringIO
from pathlib import Path

import pytest
from ruamel.yaml import YAML


def _raise_disk_full(self: Path, target: Path) -> Path:
    raise OSError("disk full")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_providers_yaml(path: Path, providers: list[dict]) -> None:
    """Write a minimal api-providers.yaml with the given providers list."""
    y = YAML()
    doc = {"schema_version": 1, "providers": providers}
    buf = StringIO()
    y.dump(doc, buf)
    path.write_text(buf.getvalue(), encoding="utf-8")
    path.chmod(0o600)


def _load_providers_yaml(path: Path) -> dict:
    y = YAML()
    with path.open("r", encoding="utf-8") as f:
        return y.load(f)  # type: ignore[no-any-return]


def _provider(name: str) -> dict:
    return {
        "name": name,
        "base_url": f"https://{name}.example",
        "auth": {"token": f"${{{name.upper()}_API_KEY}}"},
    }


# ---------------------------------------------------------------------------
# test_append_provider_preserves_0600_mode
# ---------------------------------------------------------------------------


def test_append_provider_preserves_0600_mode(tmp_config_dir: Path) -> None:
    path = tmp_config_dir / "api-providers.yaml"
    _write_providers_yaml(path, [_provider("existing")])
    assert stat.S_IMODE(path.stat().st_mode) == 0o600

    from leitum.commands.provider import _append_provider

    _append_provider("newprov", "https://x.example", "tok", "ANTHROPIC_AUTH_TOKEN")

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    doc = _load_providers_yaml(path)
    names = [p["name"] for p in doc["providers"]]
    assert "existing" in names
    assert "newprov" in names


# ---------------------------------------------------------------------------
# test_remove_provider_preserves_0600_mode
# ---------------------------------------------------------------------------


def test_remove_provider_preserves_0600_mode(tmp_config_dir: Path, tmp_state_dir: Path) -> None:
    path = tmp_config_dir / "api-providers.yaml"
    _write_providers_yaml(path, [_provider("oneprov"), _provider("twoprov")])
    assert stat.S_IMODE(path.stat().st_mode) == 0o600

    from leitum.commands.provider import run_provider_remove

    run_provider_remove("oneprov", yes=True)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    doc = _load_providers_yaml(path)
    names = [p["name"] for p in doc["providers"]]
    assert "oneprov" not in names
    assert "twoprov" in names


# ---------------------------------------------------------------------------
# test_append_provider_uses_utf8_roundtrip
# ---------------------------------------------------------------------------


def test_append_provider_uses_utf8_roundtrip(tmp_config_dir: Path) -> None:
    path = tmp_config_dir / "api-providers.yaml"
    # Write YAML with a comment containing non-ASCII characters.
    raw = (
        "schema_version: 1\n"
        "# Kommentar mit Umlauten: äöü\n"
        "providers:\n"
        "  - name: existing\n"
        "    base_url: https://existing.example\n"
        "    auth:\n"
        "      token: ${EXISTING_API_KEY}\n"
    )
    path.write_text(raw, encoding="utf-8")
    path.chmod(0o600)

    from leitum.commands.provider import _append_provider

    _append_provider("newprov", "https://x.example", "tok", "ANTHROPIC_AUTH_TOKEN")

    # Re-load and verify integrity.
    result = path.read_text(encoding="utf-8")
    assert "äöü" in result
    doc = _load_providers_yaml(path)
    names = [p["name"] for p in doc["providers"]]
    assert "existing" in names
    assert "newprov" in names


# ---------------------------------------------------------------------------
# test_append_provider_is_atomic_on_failure
# ---------------------------------------------------------------------------


def test_append_provider_is_atomic_on_failure(
    tmp_config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_config_dir / "api-providers.yaml"
    _write_providers_yaml(path, [_provider("existing")])
    original_content = path.read_text(encoding="utf-8")
    original_mtime = path.stat().st_mtime

    # Patch Path.replace to simulate a mid-write failure (e.g. disk full).
    monkeypatch.setattr(Path, "replace", _raise_disk_full)

    from leitum.commands.provider import _append_provider

    with pytest.raises(OSError, match="disk full"):
        _append_provider("newprov", "https://x.example", "tok", "ANTHROPIC_AUTH_TOKEN")

    # Original file must be intact.
    assert path.read_text(encoding="utf-8") == original_content
    assert path.stat().st_mtime == original_mtime

    # No leftover temp files.
    tmp_files = list(tmp_config_dir.glob(".tmp-*"))
    assert tmp_files == [], f"leftover temp files: {tmp_files}"


# ---------------------------------------------------------------------------
# test_atomic_write_text_helper
# ---------------------------------------------------------------------------


def test_atomic_write_text_helper_basic(tmp_path: Path) -> None:
    from leitum.config.io import atomic_write_text

    target = tmp_path / "target.yaml"
    target.write_text("old content", encoding="utf-8")

    atomic_write_text(target, "new content", mode=0o600)

    assert target.read_text(encoding="utf-8") == "new content"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_atomic_write_text_helper_rollback_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from leitum.config.io import atomic_write_text

    target = tmp_path / "target.yaml"
    target.write_text("original", encoding="utf-8")

    # Patch Path.replace to simulate a mid-write failure (e.g. disk full).
    monkeypatch.setattr(Path, "replace", _raise_disk_full)

    with pytest.raises(OSError, match="disk full"):
        atomic_write_text(target, "replacement", mode=0o600)

    # Original content preserved.
    assert target.read_text(encoding="utf-8") == "original"

    # No leftover temp files.
    tmp_files = list(tmp_path.glob(".tmp-*"))
    assert tmp_files == [], f"leftover temp files: {tmp_files}"
