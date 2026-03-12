import rich
import rich.panel
from rich import print

import anvilcv


def print_welcome():
    """Display welcome banner with version and useful links.

    Why:
        New users need guidance on where to find documentation and support.

    Modified from upstream rendercv to reflect AnvilCV branding.
    """
    print(f"\nWelcome to [dodger_blue3]AnvilCV v{anvilcv.__version__}[/dodger_blue3]!\n")
    links = {
        "Source code": "https://github.com/stillforesting/anvil",
        "Bug reports": "https://github.com/stillforesting/anvil/issues",
        "Built on": "https://github.com/rendercv/rendercv (rendercv v2.7)",
    }
    link_strings = [
        f"[bold cyan]{title + ':':<15}[/bold cyan] [link={link}]{link}[/link]"
        for title, link in links.items()
    ]
    link_panel = rich.panel.Panel(
        "\n".join(link_strings),
        title="Useful Links",
        title_align="left",
        border_style="bright_black",
    )

    print(link_panel)
