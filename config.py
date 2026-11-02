"""Game configuration, constants and persistent save data.

This module is intentionally dependency free (only the standard library) so it
can be imported by tools and tests without creating a Pygame window.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Window / game settings
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 700, 1000
FPS = 60
TITLE = "Dragon Roaster - Space Battle"
VERSION = "3.0"
MAX_ROUNDS = 7
STARTING_LIVES = 3

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
MAGENTA = (255, 0, 180)
GOLD = (255, 210, 70)
DARK_BLUE = (0, 0, 139)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
PINK = (255, 105, 180)
TEAL = (0, 200, 170)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
SAVES_DIR = BASE_DIR / "saves"
SAVE_FILE = SAVES_DIR / "save_data.json"

# ---------------------------------------------------------------------------
# Achievements
# ---------------------------------------------------------------------------
ACHIEVEMENTS = {
    "first_blood": {
        "name": "First Blood",
        "description": "Defeat your first boss.",
    },
    "score_1000": {
        "name": "Rookie Pilot",
        "description": "Reach a score of 1,000.",
    },
    "score_5000": {
        "name": "Ace Pilot",
        "description": "Reach a score of 5,000.",
    },
    "score_10000": {
        "name": "Living Legend",
        "description": "Reach a score of 10,000.",
    },
    "combo_10": {
        "name": "Combo Starter",
        "description": "Reach a 10x combo.",
    },
    "combo_25": {
        "name": "Chain Reaction",
        "description": "Reach a 25x combo.",
    },
    "boss_hunter": {
        "name": "Boss Hunter",
        "description": "Defeat 10 bosses across all runs.",
    },
    "wave_3": {
        "name": "Survivor",
        "description": "Reach wave 3.",
    },
    "victory": {
        "name": "Dragon Slayer",
        "description": "Complete all 7 waves.",
    },
    "untouchable": {
        "name": "Untouchable",
        "description": "Win without losing a life.",
    },
    "collector": {
        "name": "Collector",
        "description": "Collect 25 power-ups across all runs.",
    },
    "sharpshooter": {
        "name": "Sharpshooter",
        "description": "Fire 500 lasers across all runs.",
    },
}

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "music_volume": 0.35,
    "sfx_volume": 0.65,
    "muted": False,
    "fullscreen": False,
    "resolution": [WIDTH, HEIGHT],
    "particle_quality": "high",
    "key_bindings": {
        "up": ["w", "UP"],
        "down": ["s", "DOWN"],
        "left": ["a", "LEFT"],
        "right": ["d", "RIGHT"],
        "shoot": ["SPACE"],
        "pause": ["p"],
        "restart": ["r"],
        "quit": ["o"],
    },
}

DEFAULT_PROGRESSION = {
    "high_score": 0,
    "best_combo": 0,
    "total_enemies_defeated": 0,
    "total_powerups_collected": 0,
    "total_lasers_fired": 0,
    "bosses_defeated": 0,
    "games_played": 0,
    "victories": 0,
    "achievements": [],
}

_NUMERIC_PROGRESSION_KEYS = (
    "high_score",
    "best_combo",
    "total_enemies_defeated",
    "total_powerups_collected",
    "total_lasers_fired",
    "bosses_defeated",
    "games_played",
    "victories",
)


def _deep_merge(defaults, override):
    """Recursively merge *override* into a deep copy of *defaults*."""
    result = copy.deepcopy(defaults)
    if not isinstance(override, dict):
        return result
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class GameConfig:
    """Loads and saves player settings and persistent progression."""

    def __init__(self) -> None:
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.progression = copy.deepcopy(DEFAULT_PROGRESSION)
        self.load()

    # -- persistence --------------------------------------------------------
    def load(self) -> None:
        if not SAVE_FILE.exists():
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as exc:
            print(f"Error loading save data: {exc}")
            return

        if not isinstance(data, dict):
            return
        self.settings = _deep_merge(DEFAULT_SETTINGS, data.get("settings", {}))
        self.progression = _deep_merge(
            DEFAULT_PROGRESSION, data.get("progression", {})
        )
        self._sanitize()

    def save(self) -> None:
        try:
            SAVES_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "settings": self.settings,
                "progression": self.progression,
            }
            temp_file = SAVE_FILE.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)

            if SAVE_FILE.exists():
                backup_file = SAVE_FILE.with_suffix(".bak")
                try:
                    import shutil

                    shutil.copy2(SAVE_FILE, backup_file)
                except OSError:
                    pass
            os.replace(temp_file, SAVE_FILE)
        except OSError as exc:
            print(f"Error saving data: {exc}")

    # -- validation ---------------------------------------------------------
    def _sanitize(self) -> None:
        for key in ("music_volume", "sfx_volume"):
            try:
                value = float(self.settings.get(key, DEFAULT_SETTINGS[key]))
            except (TypeError, ValueError):
                value = DEFAULT_SETTINGS[key]
            self.settings[key] = max(0.0, min(1.0, value))

        self.settings["muted"] = bool(self.settings.get("muted", False))
        self.settings["fullscreen"] = bool(
            self.settings.get("fullscreen", False)
        )

        for key in _NUMERIC_PROGRESSION_KEYS:
            try:
                value = int(self.progression.get(key, 0))
            except (TypeError, ValueError):
                value = 0
            self.progression[key] = max(0, value)

        achievements = self.progression.get("achievements", [])
        if not isinstance(achievements, list):
            achievements = []
        self.progression["achievements"] = sorted(
            {str(item) for item in achievements if str(item) in ACHIEVEMENTS}
        )

    def reset_progression(self) -> None:
        """Wipe persistent progression while keeping player settings."""
        self.progression = copy.deepcopy(DEFAULT_PROGRESSION)
        self.save()


config = GameConfig()
