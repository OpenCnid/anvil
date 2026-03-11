# [ANVIL PATCH] Redirect to Anvil entry point
# Original: from .cli.entry_point import entry_point; entry_point()
from anvilcv.cli.entry_point import main

if __name__ == "__main__":
    main()
