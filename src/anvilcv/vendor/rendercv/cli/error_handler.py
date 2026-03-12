import functools
from collections.abc import Callable

import rich.panel
import typer
from rendercv.exception import RenderCVUserError
from rich import print

from anvilcv.exceptions import AnvilError

# Map Anvil error categories to Rich panel styles for clear visual distinction.
_ANVIL_ERROR_STYLES: dict[int, tuple[str, str]] = {
    1: ("Error", "bold red"),
    2: ("CLI Error", "bold red"),
    3: ("Service Error", "bold yellow"),
    4: ("AI Provider Error", "bold magenta"),
}


def handle_user_errors[T, **P](function: Callable[P, None]) -> Callable[P, None]:
    """Decorator that catches user errors and displays friendly messages without stack traces.

    Why:
        CLI commands should show clean error messages for expected user errors
        (invalid YAML, missing files) while preserving stack traces for
        unexpected errors. This decorator wraps all command functions.

        Handles both vendored RenderCVUserError (exit code 1) and all Anvil
        exception types (exit codes 1-4) with category-specific panel styling.

    Example:
        ```py
        @app.command()
        @handle_user_errors
        def my_command():
            # Any RenderCVUserError or AnvilError gets caught and displayed cleanly
            pass
        ```

    Args:
        function: CLI command function to wrap.

    Returns:
        Wrapped function with error handling.
    """

    @functools.wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            return function(*args, **kwargs)
        except AnvilError as e:
            title, style = _ANVIL_ERROR_STYLES.get(
                e.exit_code, ("Error", "bold red")
            )
            if e.message:
                print(
                    rich.panel.Panel(
                        e.message,
                        title=f"[{style}]{title}[/{style}]",
                        title_align="left",
                        border_style=style,
                    )
                )
            raise typer.Exit(code=e.exit_code) from e
        except RenderCVUserError as e:
            if e.message:
                print(
                    rich.panel.Panel(
                        e.message,
                        title="[bold red]Error[/bold red]",
                        title_align="left",
                        border_style="bold red",
                    )
                )
            raise typer.Exit(code=1) from e

    return wrapper
