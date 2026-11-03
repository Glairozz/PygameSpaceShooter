#!/usr/bin/env python3
"""Main entry point for Dragon Roaster.

Run the enhanced v4 game (default) or the original prototype with --classic.

Usage:
    python main.py            # enhanced game
    python main.py --classic  # original prototype
    python main.py --version  # print version
"""
from __future__ import annotations

import sys

USAGE = """\
Dragon Roaster - Space Battle

Usage:
  python main.py             Run the enhanced game (default)
  python main.py --classic   Run the original prototype
  python main.py --version   Print the version and exit
  python main.py --help      Show this help
"""


def main() -> None:
    arguments = set(sys.argv[1:])

    if "--help" in arguments or "-h" in arguments:
        print(USAGE)
        return

    if "--version" in arguments:
        from config import VERSION

        print(f"Dragon Roaster v{VERSION}")
        return

    try:
        if "--classic" in arguments:
            from dragon_shooter import Game

            Game().run()
            return

        from enhanced_shooter import EnhancedGame

        EnhancedGame().run()
    except ImportError as exc:
        if exc.name and exc.name.startswith("pygame"):
            print(
                "Pygame is required to play Dragon Roaster.\n"
                "Install it with:  pip install -r requirements.txt"
            )
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
