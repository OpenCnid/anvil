"""Prompt selector: picks per-provider prompt builders by provider name.

Why:
    Per design principle P5 ("Providers are pluggable not fungible"), each
    AI provider gets optimized prompts. This module dispatches to the right
    prompt builder based on provider name, falling back to common prompts
    for unknown providers.
"""

from __future__ import annotations

import importlib
import logging
from types import ModuleType

logger = logging.getLogger(__name__)

# Task → module path mapping
_TASK_MODULES = {
    "tailor_bullets": "anvilcv.ai.prompts.tailor_bullets",
    "cover_letter": "anvilcv.ai.prompts.cover_letter",
    "interview_prep": "anvilcv.ai.prompts.interview_prep",
    "keyword_extraction": "anvilcv.ai.prompts.keyword_extraction",
}


def _load_prompt_module(task: str, provider_name: str) -> ModuleType | None:
    """Try to load a per-provider prompt module, return None on failure."""
    base = _TASK_MODULES.get(task)
    if base is None:
        return None
    try:
        return importlib.import_module(f"{base}.{provider_name}")
    except (ImportError, ModuleNotFoundError):
        return None


def _load_common_module(task: str) -> ModuleType | None:
    """Load the common prompt module for a task."""
    base = _TASK_MODULES.get(task)
    if base is None:
        return None
    try:
        return importlib.import_module(f"{base}.common")
    except (ImportError, ModuleNotFoundError):
        return None


def get_prompt_builder(task: str, provider_name: str):
    """Get the prompt builder function for a task and provider.

    Tries provider-specific module first (e.g., tailor_bullets.anthropic),
    falls back to common module (e.g., tailor_bullets.common).

    Returns:
        The build_prompt function, or None if no prompt module exists.
    """
    # Try per-provider first
    module = _load_prompt_module(task, provider_name)
    if module is not None and hasattr(module, "build_prompt"):
        logger.debug("Using %s-specific prompt for %s", provider_name, task)
        return module.build_prompt

    # Fall back to common
    common = _load_common_module(task)
    if common is not None:
        # Common modules use varied function names — check both patterns
        for fn_name in (
            "build_prompt",
            "build_tailor_prompt",
            "build_cover_letter_prompt",
            "build_prep_prompt",
            "build_extraction_prompt",
        ):
            if hasattr(common, fn_name):
                logger.debug("Using common prompt for %s (no %s-specific)", task, provider_name)
                return getattr(common, fn_name)

    return None
