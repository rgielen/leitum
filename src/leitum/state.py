import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from leitum.config.models import ModelSlot
from leitum.config.paths import state_path


class ProviderState(BaseModel):
    models: dict[str, str] = Field(default_factory=dict)
    last_used: datetime | None = None


class State(BaseModel):
    schema_version: int = 1
    last_provider: str | None = None
    providers: dict[str, ProviderState] = Field(default_factory=dict)

    def get_model(self, provider: str, slot: ModelSlot) -> str | None:
        ps = self.providers.get(provider)
        if ps is None:
            return None
        return ps.models.get(slot)

    def set_model(self, provider: str, slot: ModelSlot, model: str) -> None:
        if provider not in self.providers:
            self.providers[provider] = ProviderState()
        self.providers[provider].models[slot] = model

    def touch_provider(self, provider: str) -> None:
        if provider not in self.providers:
            self.providers[provider] = ProviderState()
        self.providers[provider].last_used = datetime.now(tz=UTC)


def load_state(path: Path | None = None) -> State:
    p = path or state_path()
    if not p.exists():
        return State()
    try:
        from ruamel.yaml import YAML

        y = YAML()
        raw = y.load(p.read_text(encoding="utf-8"))
        if raw is None:
            return State()
        return State.model_validate(dict(raw))
    except Exception as exc:
        print(f"Warning: state file {p} is corrupt ({exc}), resetting.", file=sys.stderr)
        return State()


def save_state(state: State, path: Path | None = None) -> None:
    p = path or state_path()
    p.parent.mkdir(parents=True, exist_ok=True)

    from io import StringIO

    from ruamel.yaml import YAML

    y = YAML()
    data: dict[str, object] = {"schema_version": state.schema_version}
    if state.last_provider is not None:
        data["last_provider"] = state.last_provider
    if state.providers:
        providers_data: dict[str, object] = {}
        for name, ps in state.providers.items():
            ps_data: dict[str, object] = {}
            if ps.models:
                ps_data["models"] = dict(ps.models)
            if ps.last_used is not None:
                ps_data["last_used"] = ps.last_used.isoformat()
            providers_data[name] = ps_data
        data["providers"] = providers_data

    buf = StringIO()
    y.dump(data, buf)
    content = buf.getvalue()

    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".state-", suffix=".yaml")
    closed = False
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        closed = True
        Path(tmp).chmod(0o600)
        Path(tmp).replace(p)
    except Exception:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass
        Path(tmp).unlink(missing_ok=True)
        raise
