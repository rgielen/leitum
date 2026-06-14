"""Unit tests for state.py."""

import stat
from pathlib import Path

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
