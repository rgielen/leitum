from __future__ import annotations

import os
import tempfile
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from leitum.config.models import ProjectConfig, ProvidersConfig


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    return y


def load_yaml(path: Path) -> Any:
    y = _yaml()
    with path.open("r", encoding="utf-8") as f:
        return y.load(f)


def dump_yaml(data: Any, path: Path) -> None:
    y = _yaml()
    buf = StringIO()
    y.dump(data, buf)
    path.write_text(buf.getvalue(), encoding="utf-8")


def load_providers_config(path: Path) -> ProvidersConfig:
    from leitum.config.models import ProvidersConfig
    from leitum.config.permissions import check_file_permissions

    check_file_permissions(path)
    raw = load_yaml(path)
    return ProvidersConfig.model_validate(raw)


def load_project_config(path: Path) -> ProjectConfig:
    from leitum.config.models import ProjectConfig

    raw = load_yaml(path)
    return ProjectConfig.model_validate(raw)


# Slot order kept explicit so a written models block is deterministic and matches
# the resolver's ordering, independent of dict iteration order in the caller.
_PROJECT_MODEL_SLOTS = ("start", "opus", "sonnet", "haiku")


def save_project_config(path: Path, *, provider: str, models: dict[str, str]) -> None:
    """Write the resolved selection to a project ``leitum.yaml``.

    Merges into an existing file via a ruamel round-trip so comments and any
    ``extra_env`` block survive; only ``provider`` and ``models`` are rewritten.
    ``models`` must contain only the slots that are actually set — unset slots are
    omitted, which also prunes them from a previously pinned ``models`` block.

    Uses normal file permissions (this file lives in the repo working tree); it
    must never contain tokens, and the values written here (provider name, model
    ids) carry none.
    """
    from ruamel.yaml.comments import CommentedMap

    data: Any
    if path.exists():
        data = load_yaml(path)
        if not isinstance(data, CommentedMap):
            data = CommentedMap()
    else:
        data = CommentedMap()

    data["schema_version"] = data.get("schema_version", 1)
    data["provider"] = provider

    models_map: CommentedMap = CommentedMap()
    for slot in _PROJECT_MODEL_SLOTS:
        value = models.get(slot)
        if value:
            models_map[slot] = value
    if models_map:
        data["models"] = models_map
    elif "models" in data:
        del data["models"]

    dump_yaml(data, path)


EXAMPLE_PROVIDERS_CONFIG = """\
schema_version: 1
providers:
  - name: requesty
    base_url: https://router.requesty.ai
    auth:
      token: ${REQUESTY_API_KEY}
      # env_var: ANTHROPIC_AUTH_TOKEN  # default; change to ANTHROPIC_API_KEY if needed
    # defaults:
    #   start: anthropic/claude-sonnet-4-5
    #   opus: anthropic/claude-opus-4-5
    #   sonnet: anthropic/claude-sonnet-4-5
    #   haiku: anthropic/claude-haiku-4-5
    # models:
    #   - id: anthropic/claude-sonnet-4-5
    #     display: "Sonnet 4.5 (Requesty)"
    #     roles: [sonnet, start]
"""

EMPTY_STATE = """\
schema_version: 1
"""


def atomic_write_text(path: Path, content: str, mode: int = 0o600) -> None:
    """Write `content` to `path` atomically via a temp file in the same directory.

    On any failure the original file is left untouched and the temp file is
    removed. `mode` defaults to 0o600 because this helper is intended for
    security-sensitive config files that may contain tokens. The parent
    directory is created if missing and clamped to 0o700, mirroring
    `permissions.create_with_mode`, so the config directory stays private.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    fd, tmp_str = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix or ".yaml")
    tmp = Path(tmp_str)
    closed = False
    try:
        data = content.encode("utf-8")
        view = memoryview(data)
        offset = 0
        while offset < len(view):
            written = os.write(fd, view[offset:])
            if written == 0:
                raise OSError("short write")
            offset += written
        os.close(fd)
        closed = True
        tmp.chmod(mode)
        tmp.replace(path)
    except Exception:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def write_example_providers_config(path: Path) -> None:
    from leitum.config.permissions import create_with_mode

    create_with_mode(path, EXAMPLE_PROVIDERS_CONFIG, mode=0o600)


def write_empty_state(path: Path) -> None:
    from leitum.config.permissions import create_with_mode

    create_with_mode(path, EMPTY_STATE, mode=0o600)
