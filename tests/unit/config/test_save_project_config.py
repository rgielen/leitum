"""Tests for writing a project leitum.yaml via save_project_config."""

from __future__ import annotations

from pathlib import Path

from leitum.config.io import load_project_config, save_project_config


def test_creates_fresh_file(tmp_path: Path) -> None:
    path = tmp_path / "leitum.yaml"
    save_project_config(
        path,
        provider="requesty",
        models={"start": "anthropic/claude-sonnet-4-5", "sonnet": "anthropic/claude-sonnet-4-5"},
    )
    assert path.exists()
    cfg = load_project_config(path)
    assert cfg.schema_version == 1
    assert cfg.provider == "requesty"
    assert cfg.models is not None
    assert cfg.models.start == "anthropic/claude-sonnet-4-5"
    assert cfg.models.sonnet == "anthropic/claude-sonnet-4-5"
    assert cfg.models.opus is None
    assert cfg.models.haiku is None


def test_models_written_in_slot_order(tmp_path: Path) -> None:
    path = tmp_path / "leitum.yaml"
    # Provide models out of slot order; the written file must be deterministic.
    save_project_config(
        path,
        provider="requesty",
        models={"haiku": "h", "start": "s", "opus": "o"},
    )
    text = path.read_text(encoding="utf-8")
    start = text.index("start:")
    opus = text.index("opus:")
    haiku = text.index("haiku:")
    assert start < opus < haiku


def test_merge_preserves_comments_and_extra_env(tmp_path: Path) -> None:
    path = tmp_path / "leitum.yaml"
    path.write_text(
        "schema_version: 1\n"
        "provider: old-provider  # team default\n"
        "models:\n"
        "  start: old-start\n"
        "  opus: old-opus\n"
        "extra_env:\n"
        '  ANTHROPIC_CUSTOM_HEADERS: "x-project: demo"\n',
        encoding="utf-8",
    )

    save_project_config(
        path,
        provider="requesty",
        models={"start": "new-start", "sonnet": "new-sonnet"},
    )

    text = path.read_text(encoding="utf-8")
    # Comment survives the round-trip.
    assert "# team default" in text

    cfg = load_project_config(path)
    assert cfg.provider == "requesty"
    assert cfg.extra_env == {"ANTHROPIC_CUSTOM_HEADERS": "x-project: demo"}
    assert cfg.models is not None
    assert cfg.models.start == "new-start"
    assert cfg.models.sonnet == "new-sonnet"
    # A slot that was pinned before but is not in the new selection is pruned.
    assert cfg.models.opus is None


def test_empty_selection_removes_existing_models(tmp_path: Path) -> None:
    path = tmp_path / "leitum.yaml"
    path.write_text(
        "schema_version: 1\nprovider: requesty\nmodels:\n  start: old-start\n",
        encoding="utf-8",
    )

    save_project_config(path, provider="requesty", models={})

    cfg = load_project_config(path)
    assert cfg.provider == "requesty"
    assert cfg.models is None


def test_never_writes_auth_or_tokens(tmp_path: Path) -> None:
    path = tmp_path / "leitum.yaml"
    save_project_config(path, provider="requesty", models={"start": "s"})
    text = path.read_text(encoding="utf-8")
    assert "auth" not in text
    assert "token" not in text
