"""Unit tests for state.py."""

import os
import stat
from pathlib import Path

import pytest

from leitum.state import State, load_state, save_state


class TestStateRoundtrip:
    def test_save_and_load(self, tmp_path: Path):
        p = tmp_path / "state.yaml"
        s = State()
        s.last_provider = "requesty"
        s.set_model("requesty", "start", "anthropic/claude-sonnet-4-5")
        save_state(s, p)

        loaded = load_state(p)
        assert loaded.last_provider == "requesty"
        assert loaded.get_model("requesty", "start") == "anthropic/claude-sonnet-4-5"

    def test_file_mode_600(self, tmp_path: Path):
        p = tmp_path / "state.yaml"
        save_state(State(), p)
        assert stat.S_IMODE(p.stat().st_mode) == 0o600

    def test_missing_file_returns_empty_state(self, tmp_path: Path):
        p = tmp_path / "nonexistent.yaml"
        s = load_state(p)
        assert s.last_provider is None
        assert s.providers == {}

    def test_corrupt_file_returns_empty_state(self, tmp_path: Path, capsys):
        p = tmp_path / "state.yaml"
        p.write_text("not: valid: yaml: [[[")
        s = load_state(p)
        assert s.last_provider is None
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_atomic_write(self, tmp_path: Path):
        p = tmp_path / "state.yaml"
        s1 = State()
        s1.last_provider = "requesty"
        save_state(s1, p)

        s2 = State()
        s2.last_provider = "openrouter"
        save_state(s2, p)

        loaded = load_state(p)
        assert loaded.last_provider == "openrouter"

    def test_no_slots_written_for_not_set(self, tmp_path: Path):
        p = tmp_path / "state.yaml"
        s = State()
        s.last_provider = "requesty"
        save_state(s, p)

        loaded = load_state(p)
        assert loaded.get_model("requesty", "opus") is None


def _make_state() -> State:
    s = State()
    s.last_provider = "requesty"
    s.set_model("requesty", "start", "anthropic/claude-sonnet-4-5")
    return s


class TestSaveStateErrorHandling:
    def test_save_state_surfaces_replace_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = tmp_path / "state.yaml"
        monkeypatch.setattr(
            Path, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full"))
        )
        with pytest.raises(OSError, match="disk full"):
            save_state(_make_state(), path=p)

    def test_save_state_cleans_temp_on_replace_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = tmp_path / "state.yaml"
        monkeypatch.setattr(
            Path, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full"))
        )
        with pytest.raises(OSError):
            save_state(_make_state(), path=p)
        leftover = list(tmp_path.glob(".state-*.yaml"))
        assert leftover == [], f"temp files left behind: {leftover}"

    def test_save_state_surfaces_chmod_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = tmp_path / "state.yaml"
        monkeypatch.setattr(
            Path, "chmod", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("perm"))
        )
        with pytest.raises(OSError, match="perm"):
            save_state(_make_state(), path=p)
        leftover = list(tmp_path.glob(".state-*.yaml"))
        assert leftover == [], f"temp files left behind: {leftover}"

    def test_save_state_write_error_still_cleans_up(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p = tmp_path / "state.yaml"
        monkeypatch.setattr(
            os, "write", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("io"))
        )
        with pytest.raises(OSError, match="io"):
            save_state(_make_state(), path=p)
        leftover = list(tmp_path.glob(".state-*.yaml"))
        assert leftover == [], f"temp files left behind: {leftover}"
