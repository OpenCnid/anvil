"""GitHub scan result caching with ETag support.

Why:
    GitHub API has rate limits (60/hr unauth, 5000/hr auth). Aggressive caching
    with conditional requests (ETag/If-None-Match) minimizes API calls on
    re-scans while keeping data fresh.
"""

from __future__ import annotations

import json
import pathlib
import time

from anvilcv.schema.github_profile import GitHubProfile
from anvilcv.utils.cache import get_cache_dir

DEFAULT_TTL_SECONDS = 3600  # 1 hour


def get_github_cache_dir(base_path: pathlib.Path | None = None) -> pathlib.Path:
    """Return the GitHub cache directory."""
    return get_cache_dir(base_path, "github")


def get_cache_path(
    username: str,
    base_path: pathlib.Path | None = None,
) -> pathlib.Path:
    """Get the cache file path for a username."""
    return get_github_cache_dir(base_path) / f"{username}.json"


def read_cached_profile(
    username: str,
    base_path: pathlib.Path | None = None,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> GitHubProfile | None:
    """Read a cached GitHub profile if it exists and hasn't expired."""
    cache_file = get_cache_path(username, base_path)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    cached_at = data.get("_cached_at", 0)
    if time.time() - cached_at > ttl_seconds:
        return None

    try:
        return GitHubProfile.model_validate(data.get("profile", {}))
    except Exception:
        return None


def write_cached_profile(
    profile: GitHubProfile,
    base_path: pathlib.Path | None = None,
    etag: str | None = None,
) -> pathlib.Path:
    """Write a GitHub profile to cache."""
    cache_file = get_cache_path(profile.username, base_path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "_cached_at": time.time(),
        "etag": etag,
        "profile": profile.model_dump(mode="json"),
    }
    cache_file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return cache_file


def read_cached_etag(
    username: str,
    base_path: pathlib.Path | None = None,
) -> str | None:
    """Read the cached ETag for conditional requests."""
    cache_file = get_cache_path(username, base_path)
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return data.get("etag")
    except (json.JSONDecodeError, OSError):
        return None


def clear_cache(
    username: str | None = None,
    base_path: pathlib.Path | None = None,
) -> None:
    """Clear cached data for a user or all users."""
    if username:
        cache_file = get_cache_path(username, base_path)
        if cache_file.exists():
            cache_file.unlink()
    else:
        cache_dir = get_github_cache_dir(base_path)
        if cache_dir.exists():
            for f in cache_dir.glob("*.json"):
                f.unlink()
