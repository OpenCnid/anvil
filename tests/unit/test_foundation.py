"""Tests for Phase 0 foundation: package identity, vendor import hook, exceptions.

Why:
    The vendor import hook is the most critical piece of infrastructure — if it
    breaks, ALL vendored rendercv code fails to import. These tests verify it
    works for both the top-level package and nested submodules.
"""

import sys


def test_anvilcv_version():
    """Package version is set and matches pyproject.toml."""
    import anvilcv

    assert anvilcv.__version__ == "0.1.0"
    assert anvilcv.__package_name__ == "anvilcv"


def test_vendor_import_hook_installed():
    """The _VendorImporter is in sys.meta_path after importing anvilcv."""
    import anvilcv  # noqa: F401

    importer_types = [type(f).__name__ for f in sys.meta_path]
    assert "_VendorImporter" in importer_types


def test_vendor_import_hook_top_level():
    """'import rendercv' resolves to anvilcv.vendor.rendercv."""
    __import__("anvilcv")
    rendercv = __import__("rendercv")

    assert "anvilcv.vendor.rendercv" in rendercv.__name__ or rendercv is sys.modules.get(
        "anvilcv.vendor.rendercv"
    )


def test_vendor_import_hook_submodule():
    """'from rendercv.exception import ...' works via the vendor hook."""
    __import__("anvilcv")
    from rendercv.exception import RenderCVUserError

    assert RenderCVUserError is not None


def test_vendored_init_has_anvil_version():
    """Vendored rendercv.__version__ matches anvilcv.__version__."""
    anvilcv = __import__("anvilcv")
    rendercv = __import__("rendercv")

    assert rendercv.__version__ == anvilcv.__version__
    assert rendercv.__rendercv_version__ == "2.7"


def test_exception_classes():
    """Anvil exception classes have correct exit codes."""
    from anvilcv.exceptions import (
        AnvilAIProviderError,
        AnvilCLIError,
        AnvilError,
        AnvilServiceError,
        AnvilUserError,
    )

    assert AnvilError(message="test").exit_code == 1
    assert AnvilUserError(message="test").exit_code == 1
    assert AnvilCLIError(message="test").exit_code == 2
    assert AnvilServiceError(message="test").exit_code == 3
    assert AnvilAIProviderError(message="test").exit_code == 4


def test_exception_inheritance():
    """All Anvil exceptions inherit from AnvilError and Exception."""
    from anvilcv.exceptions import (
        AnvilAIProviderError,
        AnvilCLIError,
        AnvilError,
        AnvilServiceError,
        AnvilUserError,
    )

    for cls in (AnvilUserError, AnvilCLIError, AnvilServiceError, AnvilAIProviderError):
        err = cls(message="test")
        assert isinstance(err, AnvilError)
        assert isinstance(err, Exception)
