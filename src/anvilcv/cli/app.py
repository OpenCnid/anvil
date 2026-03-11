"""Anvil CLI application.

Why:
    This is the single Typer app instance that all commands (both Anvil-native
    and vendored rendercv) register on. Vendored ``app.py`` re-exports this
    ``app`` so that vendored commands' ``from ..app import app`` picks up the
    Anvil app.

    Stub subcommands are defined here for CLI completeness (``anvil --help``
    lists all planned commands). Each stub prints "Not yet implemented" and
    exits cleanly until the real implementation lands.
"""

from typing import Annotated

import typer
from rich import print as rprint

import anvilcv

app = typer.Typer(
    rich_markup_mode="rich",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def cli_main(
    ctx: typer.Context,
    version_requested: Annotated[
        bool | None, typer.Option("--version", "-v", help="Show the version")
    ] = None,
):
    """AnvilCV: Developer-native, AI-powered resume engine built on rendercv."""
    if version_requested:
        rprint(f"AnvilCV v{anvilcv.__version__}")
        raise typer.Exit()
    elif ctx.invoked_subcommand is None:
        rprint(ctx.get_help())
        raise typer.Exit()


# --- Stub subcommands for commands not yet implemented ---
# These ensure `anvil --help` lists all planned commands and each has --help.
# Real implementations replace these stubs in later phases.


def _not_implemented(command_name: str) -> None:
    rprint(f"[yellow]{command_name}[/yellow] is not yet implemented.")
    raise typer.Exit(0)


@app.command(
    name="scan",
    help="Scan your GitHub profile for resume-worthy projects.",
)
def cli_command_scan():
    _not_implemented("anvil scan")


@app.command(
    name="prep",
    help="Generate interview preparation notes.",
)
def cli_command_prep(
    input_file: Annotated[str, typer.Argument(help="YAML input file")] = "",
):
    _not_implemented("anvil prep")


@app.command(
    name="cover",
    help="Generate a cover letter from your resume and a job description.",
)
def cli_command_cover(
    input_file: Annotated[str, typer.Argument(help="YAML input file")] = "",
):
    _not_implemented("anvil cover")


@app.command(
    name="watch",
    help="Monitor GitHub for new activity.",
)
def cli_command_watch():
    _not_implemented("anvil watch")


@app.command(
    name="deploy",
    help="Deploy your resume as a static website.",
)
def cli_command_deploy(
    input_file: Annotated[str, typer.Argument(help="YAML input file")] = "",
):
    _not_implemented("anvil deploy")


