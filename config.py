"""Game configuration and constants."""
import json
import os
from pathlib import Path

# Window settings
WIDTH, HEIGHT = 700, 1000
FPS = 60
TITLE = "Dragon Roaster - Space Battle"

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
DARK_BLUE = (0, 0, 139)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
PINK = (255, 105, 180)

# Paths
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
SAVES_DIR = BASE_DIR / "saves"
SAVE_FILE = SAVES_DIR / "save_data.json"

# Default settings
DEFAULT_SETTINGS = {
    "music_volume": 0.5,
    "sfx_volume": 0.7,
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
        "quit": ["o"]
    }
}

DEFAULT_PROGRESSION = {
    "high_score": 0,
    "total_enemies_defeated": 0,
    "bosses_defeated": 0,
    "games_played": 0,
    "achievements": []
}


class GameConfig:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.progression = DEFAULT_PROGRESSION.copy()
        self.load()
    
    def load(self):
        try:
            if SAVE_FILE.exists():
                with open(SAVE_FILE, 'r') as f:
                    data = json.load(f)
                if isinstance(data.get('settings'), dict):
                    # Merge with defaults to ensure all keys exist
                    merged = DEFAULT_SETTINGS.copy()
                    merged.update(data['settings'])
                    self.settings = merged
                if isinstance(data.get('progression'), dict):
                    merged = DEFAULT_PROGRESSION.copy()
                    merged.update(data['progression'])
                    self.progression = merged
        except Exception as e:
            print(f"Error loading save data: {e}")
            # Use defaults on error - don't overwrite
            self.settings = DEFAULT_SETTINGS.copy()
            self.progression = DEFAULT_PROGRESSION.copy()
    
    def save(self):
        try:
            SAVES_DIR.mkdir(exist_ok=True)
            data = {
                "settings": self.settings,
                "progression": self.progression
            }
            # Write safely
            temp_file = SAVE_FILE.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            if SAVE_FILE.exists():
                backup_file = SAVE_FILE.with_suffix('.bak')
                try:
                    import shutil
                    shutil.copy2(SAVE_FILE, backup_file)
                except:
                    pass
            os.replace(temp_file, SAVE_FILE)
        except Exception as e:
            print(f"Error saving data: {e}")


config = GameConfig()
