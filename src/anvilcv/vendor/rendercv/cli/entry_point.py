# [ANVIL PATCH] Redirect to Anvil entry point
# Original: imported .app and called cli_app() with dependency-safe error handling


def entry_point() -> None:
    """Redirect to Anvil's CLI entry point."""
    from anvilcv.cli.entry_point import main

    main()
