"""AnvilCV: Developer-native, AI-powered resume engine — a fork of rendercv."""

import importlib
import importlib.abc
import importlib.machinery
import sys

__version__ = "0.1.0"
__package_name__ = "anvilcv"


class _VendorImporter(importlib.abc.MetaPathFinder):
    """Make bare 'rendercv' imports resolve to 'anvilcv.vendor.rendercv'.

    Why:
        Vendored rendercv code uses absolute imports like ``from rendercv.exception
        import ...``. Rather than rewriting every import in 80+ vendored files
        (violating the Untouched classification), this meta-path finder transparently
        redirects ``rendercv.*`` lookups to ``anvilcv.vendor.rendercv.*``.

        Uses ``find_spec`` (not deprecated ``find_module``) for Python 3.12+.
    """

    _PREFIX = "rendercv"
    _VENDOR = "anvilcv.vendor.rendercv"

    def find_spec(self, fullname, path, target=None):  # noqa: ARG002
        if fullname != self._PREFIX and not fullname.startswith(self._PREFIX + "."):
            return None

        actual = self._VENDOR + fullname[len(self._PREFIX) :]
        return importlib.machinery.ModuleSpec(fullname, _VendorLoader(actual))


class _VendorLoader(importlib.abc.Loader):
    """Loader that imports the actual vendored module and aliases it."""

    def __init__(self, actual_name: str):
        self._actual_name = actual_name

    def create_module(self, spec):  # noqa: ARG002
        return None  # Use default module creation

    def exec_module(self, module):
        actual = importlib.import_module(self._actual_name)
        # Copy all attributes from the real module
        module.__dict__.update(actual.__dict__)
        # Preserve package structure for sub-imports
        if hasattr(actual, "__path__"):
            module.__path__ = actual.__path__
        module.__loader__ = self
        # Also alias in sys.modules so future lookups are fast
        sys.modules[module.__name__] = module


# Install vendor import hook before any vendored code is imported
sys.meta_path.insert(0, _VendorImporter())
