"""Unit tests for config/models.py."""

import pytest
from pydantic import ValidationError

from leitum.config.models import (
    ProjectConfig,
    Provider,
    ProviderAuth,
    ProvidersConfig,
)


def _minimal_provider(**kwargs):
    defaults = {
        "name": "requesty",
        "base_url": "https://router.requesty.ai",
        "auth": {"token": "${REQUESTY_API_KEY}"},
    }
    defaults.update(kwargs)
    return defaults


class TestProviderAuth:
    def test_default_env_var(self):
        auth = ProviderAuth(token="abc")
        assert auth.env_var == "ANTHROPIC_AUTH_TOKEN"

    def test_custom_env_var(self):
        auth = ProviderAuth(token="abc", env_var="ANTHROPIC_API_KEY")
        assert auth.env_var == "ANTHROPIC_API_KEY"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ProviderAuth(token="abc", unknown_field="x")


class TestProvider:
    def test_valid_name(self):
        p = Provider(**_minimal_provider())
        assert p.name == "requesty"

    @pytest.mark.parametrize("name", ["Bad", "bad_name", "bad name", "1bad", "-bad"])
    def test_invalid_name(self, name):
        with pytest.raises(ValidationError):
            Provider(**_minimal_provider(name=name))

    def test_models_optional(self):
        p = Provider(**_minimal_provider())
        assert p.models is None

    def test_extra_env_defaults_empty(self):
        p = Provider(**_minimal_provider())
        assert p.extra_env == {}


class TestProvidersConfig:
    def test_valid_config(self):
        cfg = ProvidersConfig(
            schema_version=1,
            providers=[_minimal_provider()],
        )
        assert len(cfg.providers) == 1

    def test_empty_providers_invalid(self):
        with pytest.raises(ValidationError):
            ProvidersConfig(schema_version=1, providers=[])

    def test_duplicate_names_invalid(self):
        with pytest.raises(ValidationError):
            ProvidersConfig(
                schema_version=1,
                providers=[_minimal_provider(), _minimal_provider()],
            )

    def test_get_provider_found(self):
        cfg = ProvidersConfig(schema_version=1, providers=[_minimal_provider()])
        assert cfg.get_provider("requesty") is not None

    def test_get_provider_not_found(self):
        cfg = ProvidersConfig(schema_version=1, providers=[_minimal_provider()])
        assert cfg.get_provider("openrouter") is None


class TestProjectConfig:
    def test_minimal(self):
        pc = ProjectConfig(schema_version=1)
        assert pc.provider is None
        assert pc.models is None

    def test_with_models(self):
        pc = ProjectConfig(
            schema_version=1,
            models={"start": "anthropic/claude-sonnet-4-5"},
        )
        assert pc.models is not None
        assert pc.models.start == "anthropic/claude-sonnet-4-5"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ProjectConfig(schema_version=1, unknown="x")
