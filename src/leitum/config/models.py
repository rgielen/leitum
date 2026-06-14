import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ModelSlot = Literal["start", "opus", "sonnet", "haiku"]

_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


class ProviderAuth(BaseModel):
    model_config = {"extra": "forbid"}

    token: str
    env_var: str = "ANTHROPIC_AUTH_TOKEN"


class ModelEntry(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    display: str | None = None
    roles: list[ModelSlot] = Field(default_factory=list)


class ModelDefaults(BaseModel):
    model_config = {"extra": "forbid"}

    start: str | None = None
    opus: str | None = None
    sonnet: str | None = None
    haiku: str | None = None

    def get(self, slot: ModelSlot) -> str | None:
        if slot == "start":
            return self.start
        if slot == "opus":
            return self.opus
        if slot == "sonnet":
            return self.sonnet
        return self.haiku


class Provider(BaseModel):
    model_config = {"extra": "forbid"}

    name: Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]*$")]
    base_url: str
    auth: ProviderAuth
    defaults: ModelDefaults | None = None
    models: list[ModelEntry] | None = None
    extra_env: dict[str, str] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not _NAME_RE.match(v):
            raise ValueError(f"Provider name '{v}' must match ^[a-z][a-z0-9-]*$")
        return v


class ProvidersConfig(BaseModel):
    model_config = {"extra": "forbid"}

    schema_version: int
    providers: list[Provider] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_names(self) -> "ProvidersConfig":
        names = [p.name for p in self.providers]
        if len(names) != len(set(names)):
            raise ValueError("Provider names must be unique")
        return self

    def get_provider(self, name: str) -> Provider | None:
        for p in self.providers:
            if p.name == name:
                return p
        return None


class ProjectConfig(BaseModel):
    model_config = {"extra": "forbid"}

    schema_version: int
    provider: str | None = None
    models: ModelDefaults | None = None
    extra_env: dict[str, str] = Field(default_factory=dict)
