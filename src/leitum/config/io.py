from __future__ import annotations

import os
import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from leitum.config.models import ProjectConfig, ProvidersConfig


def load_dotenv_file(path: Path, *, verbose: bool = False) -> dict[str, str]:
    """Source a .leitumenv file in a bash subshell and return vars it declares.

    Shell expansions including command substitutions (e.g. ``$(op read ...)``)
    are evaluated by bash before the values are captured.  Returns an empty
    dict when the file does not exist or is not a regular file.  Values are
    never logged even in verbose mode.
    """
    import json
    import shlex
    import subprocess

    from leitum.config.env import parse_dotenv

    if not path.is_file():
        return {}

    text = path.read_text(encoding="utf-8")

    if verbose:
        print(f"Loaded dotenv file: {path}", file=sys.stderr)
        for lineno, raw in enumerate(text.splitlines(), 1):
            stripped = raw.strip()
            if stripped and not stripped.startswith("#"):
                if "=" not in stripped.removeprefix("export "):
                    print(
                        f"  Warning: {path}:{lineno}: skipping malformed line",
                        file=sys.stderr,
                    )

    declared_keys = set(parse_dotenv(text).keys())
    if not declared_keys:
        return {}

    # Source the file in a bash subshell that inherits the current env, then
    # dump the resulting environment as JSON so values survive newlines/quotes.
    # set -a exports every assignment automatically (handles lines without "export").
    # source errors (e.g. malformed lines) are suppressed via 2>/dev/null because
    # we already warned about them above; the shell always continues to the JSON dump.
    _dump = "import json,os,sys; json.dump(dict(os.environ), sys.stdout)"
    _script = f'set -a; source "$1" 2>/dev/null; set +a; {sys.executable} -c {shlex.quote(_dump)}'
    try:
        proc = subprocess.run(
            ["bash", "--noprofile", "--norc", "-c", _script, "--", str(path.resolve())],
            capture_output=True,
            text=True,
            env=os.environ,
        )
    except FileNotFoundError:
        if verbose:
            print("  Warning: bash not found; falling back to static parse", file=sys.stderr)
        return parse_dotenv(text)

    if proc.returncode != 0:
        if verbose:
            print("  Warning: could not capture subshell environment", file=sys.stderr)
        return {}

    try:
        subshell_env: dict[str, str] = json.loads(proc.stdout)
    except json.JSONDecodeError:
        if verbose:
            print("  Warning: could not parse subshell environment", file=sys.stderr)
        return {}

    return {k: subshell_env[k] for k in declared_keys if k in subshell_env}


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
