"""Caching utilities for .anvil/ directory management.

Why:
    Multiple features write to .anvil/ subdirectories: GitHub scanner caches
    API responses, job parser stores parsed descriptions, AI features save
    debug logs of failed requests. This module provides a consistent interface
    for timestamped JSON caching with TTL-based expiry.
"""

import json
import pathlib
import time
from typing import Any


def get_cache_dir(
    base_path: pathlib.Path | None = None,
    subdirectory: str | None = None,
) -> pathlib.Path:
    """Return a cache directory under .anvil/, creating it if needed."""
    base = base_path or pathlib.Path.cwd()
    cache_dir = base / ".anvil"
    if subdirectory:
        cache_dir = cache_dir / subdirectory
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def read_cache(
    cache_file: pathlib.Path,
    ttl_seconds: float | None = None,
) -> Any | None:
    """Read a JSON cache file, returning None if missing, expired, or corrupt."""
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if ttl_seconds is not None:
        cached_at = data.get("_cached_at", 0)
        if time.time() - cached_at > ttl_seconds:
            return None

    return data


def write_cache(cache_file: pathlib.Path, data: dict[str, Any]) -> None:
    """Write data to a JSON cache file with a ``_cached_at`` timestamp."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = time.time()
    cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_debug_log(
    base_path: pathlib.Path | None = None,
    filename: str = "debug.json",
    data: dict[str, Any] | None = None,
) -> pathlib.Path:
    """Save debug data to .anvil/debug/ for troubleshooting failed AI requests."""
    debug_dir = get_cache_dir(base_path, "debug")
    debug_file = debug_dir / filename
    write_cache(debug_file, data or {})
    return debug_file
