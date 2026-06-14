"""Unit tests for providers/discovery.py."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx

from leitum.config.models import ModelEntry, Provider, ProviderAuth
from leitum.providers.discovery import discover_models


def _make_provider(models=None):
    return Provider(
        name="test-provider",
        base_url="https://test.example.com",
        auth=ProviderAuth(token="tok"),
        models=models,
    )


def _api_response(ids: list[str]) -> dict:
    return {"data": [{"id": i} for i in ids]}


class TestDiscoverYamlModels:
    def test_uses_yaml_models_when_present(self):
        provider = _make_provider(
            models=[
                ModelEntry(id="m1", display="Model 1"),
                ModelEntry(id="m2"),
            ]
        )
        infos = discover_models(provider)
        assert [m.id for m in infos] == ["m1", "m2"]
        assert infos[0].display == "Model 1"

    def test_yaml_models_no_api_call(self, tmp_cache_dir: Path):
        provider = _make_provider(models=[ModelEntry(id="m1")])
        with respx.mock(assert_all_called=False):
            infos = discover_models(provider)
        assert infos[0].id == "m1"


class TestDiscoverCache:
    def test_cache_hit(self, tmp_cache_dir: Path, monkeypatch: pytest.MonkeyPatch):
        provider = _make_provider()
        cache_p = tmp_cache_dir / "models" / "test-provider.json"
        cache_p.parent.mkdir(parents=True, exist_ok=True)
        cache_p.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fetched_at": datetime.now(tz=UTC).isoformat(),
                    "base_url": "https://test.example.com",
                    "models": [{"id": "cached-model", "display": None}],
                }
            )
        )
        infos = discover_models(provider)
        assert infos[0].id == "cached-model"

    def test_stale_cache_triggers_api(self, tmp_cache_dir: Path, monkeypatch: pytest.MonkeyPatch):
        cache_p = tmp_cache_dir / "models" / "test-provider.json"
        cache_p.parent.mkdir(parents=True, exist_ok=True)
        old_ts = (datetime.now(tz=UTC) - timedelta(hours=25)).isoformat()
        cache_p.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fetched_at": old_ts,
                    "base_url": "https://test.example.com",
                    "models": [{"id": "stale-model", "display": None}],
                }
            )
        )

        monkeypatch.setenv("TEST_TOKEN", "tok")
        with respx.mock() as mock:
            mock.get("https://test.example.com/v1/models").mock(
                return_value=httpx.Response(200, json=_api_response(["fresh-model"]))
            )
            provider_with_env = Provider(
                name="test-provider",
                base_url="https://test.example.com",
                auth=ProviderAuth(token="tok"),
            )
            infos = discover_models(provider_with_env)
        assert infos[0].id == "fresh-model"

    def test_api_error_falls_back_to_stale(self, tmp_cache_dir: Path, capsys):
        provider = _make_provider()
        cache_p = tmp_cache_dir / "models" / "test-provider.json"
        cache_p.parent.mkdir(parents=True, exist_ok=True)
        old_ts = (datetime.now(tz=UTC) - timedelta(hours=25)).isoformat()
        cache_p.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fetched_at": old_ts,
                    "base_url": "https://test.example.com",
                    "models": [{"id": "stale-model", "display": None}],
                }
            )
        )

        with respx.mock() as mock:
            mock.get("https://test.example.com/v1/models").mock(return_value=httpx.Response(500))
            infos = discover_models(provider)

        assert infos[0].id == "stale-model"
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_api_error_no_cache_raises(self, tmp_cache_dir: Path):
        provider = _make_provider()
        with respx.mock() as mock:
            mock.get("https://test.example.com/v1/models").mock(return_value=httpx.Response(500))
            with pytest.raises(RuntimeError, match="Model discovery failed"):
                discover_models(provider)

    def test_force_refresh_bypasses_fresh_cache(self, tmp_cache_dir: Path):
        provider = _make_provider()
        cache_p = tmp_cache_dir / "models" / "test-provider.json"
        cache_p.parent.mkdir(parents=True, exist_ok=True)
        cache_p.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fetched_at": datetime.now(tz=UTC).isoformat(),
                    "base_url": "https://test.example.com",
                    "models": [{"id": "cached-model", "display": None}],
                }
            )
        )

        with respx.mock() as mock:
            mock.get("https://test.example.com/v1/models").mock(
                return_value=httpx.Response(200, json=_api_response(["fresh-model"]))
            )
            infos = discover_models(provider, force=True)

        assert infos[0].id == "fresh-model"
