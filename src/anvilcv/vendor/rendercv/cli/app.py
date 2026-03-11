# [ANVIL PATCH] Re-export Anvil CLI app; auto-discover vendored commands
# Original: created own Typer app, version checking against rendercv on PyPI,
#           auto-discovered *_command.py files and registered them.
#
# Now: imports the single Typer app from anvilcv.cli.app so vendored commands
# (render, new, create_theme) register on the Anvil app via `from ..app import app`.

import importlib
import pathlib

from anvilcv.cli.app import app  # noqa: F401

# Auto-discover vendored commands (render_command, new_command, create_theme_command)
cli_folder_path = pathlib.Path(__file__).parent
for _file in cli_folder_path.rglob("*_command.py"):
    _folder_name = _file.parent.name
    _py_file_name = _file.stem
    _full_module = f"anvilcv.vendor.rendercv.cli.{_folder_name}.{_py_file_name}"
    importlib.import_module(_full_module)
