"""Anvil-specific exceptions with structured exit codes.

Why:
    The CLI spec (specs/cli-interface.md) defines four exit codes:
    1 = user error (bad input, missing file)
    2 = CLI usage error
    3 = external service error (GitHub API, URL fetch)
    4 = AI provider error (API failure, rate limit, malformed response)

    Each exception class maps to one exit code so error handlers can
    translate exceptions to the correct exit status without switch logic.
"""

from dataclasses import dataclass


@dataclass
class AnvilError(Exception):
    """Base exception for all Anvil-specific errors."""

    message: str
    exit_code: int = 1


@dataclass
class AnvilUserError(AnvilError):
    """User error: bad input, missing file, validation failure. Exit code 1."""

    exit_code: int = 1


@dataclass
class AnvilCLIError(AnvilError):
    """CLI usage error: invalid flag combination, missing required arg. Exit code 2."""

    exit_code: int = 2


@dataclass
class AnvilServiceError(AnvilError):
    """External service error: GitHub API, URL fetch, network failure. Exit code 3."""

    exit_code: int = 3


@dataclass
class AnvilAIProviderError(AnvilError):
    """AI provider error: API failure, rate limit, malformed response. Exit code 4."""

    exit_code: int = 4
