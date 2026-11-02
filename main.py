#!/usr/bin/env python3
"""Main entry point for Dragon Roaster.

Run the enhanced version (default) or the original prototype with --classic.
"""
from __future__ import annotations

import sys


def main() -> None:
    if "--classic" in sys.argv:
        from dragon_shooter import Game

        Game().run()
        return

    from enhanced_shooter import EnhancedGame

    EnhancedGame().run()


if __name__ == "__main__":
    main()
