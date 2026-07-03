"""Provider preset registry and models for local and generic providers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderPreset(BaseModel):
    """Preset configuration for a provider."""

    key: str
    display: str
    default_name: str
    base_url: str
    token: str
    auth_env_var: str = "ANTHROPIC_AUTH_TOKEN"
    extra_env: dict[str, str] = Field(default_factory=dict)
    is_local: bool
    detect_ports: list[int] = Field(default_factory=list)
    docs_url: str | None = None


# Immutable shipped presets
PRESETS: list[ProviderPreset] = [
    ProviderPreset(
        key="ollama",
        display="Ollama (local)",
        default_name="ollama",
        base_url="http://localhost:11434",
        token="ollama",
        extra_env={"OLLAMA_CONTEXT_LENGTH": "32768"},
        is_local=True,
        detect_ports=[11434],
        docs_url="https://docs.ollama.com/api/anthropic-compatibility",
    ),
    ProviderPreset(
        key="lm-studio",
        display="LM Studio (local)",
        default_name="lm-studio",
        base_url="http://localhost:1234",
        token="lmstudio",
        is_local=True,
        detect_ports=[1234],
        docs_url="https://lmstudio.ai/docs/developer/anthropic-compat",
    ),
    ProviderPreset(
        key="llama-cpp",
        display="llama.cpp (local)",
        default_name="llama-cpp",
        base_url="http://localhost:8080",
        token="local",
        is_local=True,
        detect_ports=[8080],
    ),
    ProviderPreset(
        key="vllm",
        display="vLLM (local)",
        default_name="vllm",
        base_url="http://localhost:8000",
        token="local",
        is_local=True,
        detect_ports=[8000],
    ),
    ProviderPreset(
        key="local-generic",
        display="Generic local (Anthropic-compat)",
        default_name="local-generic",
        base_url="http://localhost:8080",
        token="local",
        is_local=True,
        detect_ports=[],
    ),
]


def get_preset(key: str) -> ProviderPreset | None:
    """Get a preset by key."""
    for p in PRESETS:
        if p.key == key:
            return p
    return None
