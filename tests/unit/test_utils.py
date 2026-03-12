"""Tests for utility modules: config and cache.

Why:
    Config resolution and caching are used by multiple features (AI providers,
    GitHub scanner, debug logging). Bugs here cascade to every feature that
    needs API keys or cached data.
"""

import json
import pathlib
import time

from anvilcv.utils.cache import get_cache_dir, read_cache, save_debug_log, write_cache
from anvilcv.utils.config import get_api_key, load_config, resolve_provider


class TestConfig:
    def test_load_config_no_file(self, tmp_path: pathlib.Path):
        """Returns empty dict when no config file exists."""
        config = load_config(tmp_path)
        assert config == {}

    def test_load_config_with_file(self, tmp_path: pathlib.Path):
        """Loads config from .anvil/config.yaml."""
        anvil_dir = tmp_path / ".anvil"
        anvil_dir.mkdir()
        config_file = anvil_dir / "config.yaml"
        config_file.write_text("providers:\n  default: anthropic\n")

        config = load_config(tmp_path)
        assert config["providers"]["default"] == "anthropic"

    def test_get_api_key_from_env(self, monkeypatch):
        """API key resolved from environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        assert get_api_key("anthropic") == "sk-test-123"

    def test_get_api_key_missing(self, monkeypatch):
        """Returns None when no API key is available."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert get_api_key("anthropic") is None

    def test_get_api_key_custom_env(self, monkeypatch):
        """API key resolved from custom env var in config."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("MY_CUSTOM_KEY", "sk-custom-456")
        config = {"providers": {"anthropic": {"api_key_env": "MY_CUSTOM_KEY"}}}
        assert get_api_key("anthropic", config) == "sk-custom-456"

    def test_resolve_provider_cli_flag(self):
        """CLI --provider flag takes highest priority."""
        assert resolve_provider(cli_provider="openai") == "openai"

    def test_resolve_provider_config_default(self):
        """Config default provider used when no CLI flag."""
        config = {"providers": {"default": "anthropic"}}
        assert resolve_provider(config=config) == "anthropic"

    def test_resolve_provider_auto_detect(self, monkeypatch):
        """Auto-detects first provider with API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
        assert resolve_provider() == "openai"

    def test_resolve_provider_none(self, monkeypatch):
        """Returns None when no provider is configured."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert resolve_provider() is None


class TestCache:
    def test_get_cache_dir_creates_directory(self, tmp_path: pathlib.Path):
        """Creates .anvil/ directory if it doesn't exist."""
        cache_dir = get_cache_dir(tmp_path)
        assert cache_dir.exists()
        assert cache_dir == tmp_path / ".anvil"

    def test_get_cache_dir_with_subdirectory(self, tmp_path: pathlib.Path):
        """Creates nested subdirectory under .anvil/."""
        cache_dir = get_cache_dir(tmp_path, "github")
        assert cache_dir.exists()
        assert cache_dir == tmp_path / ".anvil" / "github"

    def test_write_and_read_cache(self, tmp_path: pathlib.Path):
        """Round-trip write then read returns the data."""
        cache_file = tmp_path / "test_cache.json"
        data = {"key": "value", "count": 42}
        write_cache(cache_file, data)

        result = read_cache(cache_file)
        assert result is not None
        assert result["key"] == "value"
        assert result["count"] == 42
        assert "_cached_at" in result

    def test_read_cache_missing_file(self, tmp_path: pathlib.Path):
        """Returns None for nonexistent cache file."""
        assert read_cache(tmp_path / "nonexistent.json") is None

    def test_read_cache_expired(self, tmp_path: pathlib.Path):
        """Returns None when cache has expired past TTL."""
        cache_file = tmp_path / "expired.json"
        data = {"key": "value", "_cached_at": time.time() - 3600}
        cache_file.write_text(json.dumps(data))

        assert read_cache(cache_file, ttl_seconds=60) is None

    def test_read_cache_not_expired(self, tmp_path: pathlib.Path):
        """Returns data when cache is within TTL."""
        cache_file = tmp_path / "fresh.json"
        data = {"key": "value", "_cached_at": time.time()}
        cache_file.write_text(json.dumps(data))

        result = read_cache(cache_file, ttl_seconds=3600)
        assert result is not None
        assert result["key"] == "value"

    def test_read_cache_corrupt_json(self, tmp_path: pathlib.Path):
        """Returns None for corrupted JSON."""
        cache_file = tmp_path / "corrupt.json"
        cache_file.write_text("not valid json {{{")

        assert read_cache(cache_file) is None

    def test_save_debug_log(self, tmp_path: pathlib.Path):
        """Debug logs are saved to .anvil/debug/."""
        debug_file = save_debug_log(tmp_path, "test_error.json", {"error": "test"})
        assert debug_file.exists()
        assert "debug" in str(debug_file)

        data = json.loads(debug_file.read_text())
        assert data["error"] == "test"
