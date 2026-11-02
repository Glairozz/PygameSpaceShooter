# Dragon Roaster - Enhanced Space Shooter

A polished, feature-rich arcade shooter built with Python and Pygame. Fight through 7 boss waves, build up huge combos, collect power-ups, unlock achievements, and chase a new high score.

## What's New in v3

- **Fully redesigned bosses** - 7 unique boss fighters with evolving attack patterns that get more aggressive as their HP drops
- **Procedural audio** - All sound effects are synthesised at runtime (no audio files required)
- **Combo system** - Chain hits together to build a multiplier and score big bonuses
- **Richer power-ups** - Health, shield, rapid fire, spread shot, bomb, extra life, and the new Overdrive
- **Screen shake, particles & floating text** - Big, punchy feedback on every hit and explosion
- **Achievements & stats** - Track progress (bosses defeated, power-ups, lasers fired) with toast notifications
- **Lives system** - Start with 3 lives, respawn on hit with a short grace period
- **Smarter save system** - Safe JSON saves with automatic backups and schema migration
- **Mute toggle** - Hit `M` anytime to silence/restore sound

## Features

### Gameplay
- **Responsive controls** - Smooth WASD/Arrow key movement with delta-time aware updates
- **Tight combat** - Player/enemy lasers, asteroids, and accurate collision detection
- **Progressive difficulty** - Bosses grow stronger across all 7 waves
- **Power-up drops** - Chance-based pickups keep every run different
- **Screen shake** - Impactful feedback for big hits

### UI & Menus
- **Polished main menu** - Mission briefing, high score, best combo, and achievement progress
- **Achievements screen** - Press `A` on the main menu to browse every unlock and its description
- **In-game HUD** - HP, shield, lives, active timers, boss bar, score, and combo meter
- **Pause menu** - Resume or return to menu at any time
- **Game Over/Victory screens** - Stats breakdown with "New High Score" callouts
- **Achievement toasts** - Instant feedback when you unlock something

### Progression & Persistence
- **High score tracking** - Persistent across runs
- **Statistics** - Games played, victories, bosses defeated, best combo, lasers fired, power-ups collected
- **Achievements** - 12 unlockable achievements
- **Settings** - Volume and mute preferences saved to JSON

## Installation

### Requirements
- Python 3.7 or higher
- Pygame 2.0 or higher

### Setup
```bash
# Install dependencies
pip install pygame

# Run the game
python main.py

# Run the classic prototype
python main.py --classic
```

## Controls

| Key | Action |
|---|---|
| WASD / Arrow Keys | Move spaceship |
| Space | Shoot |
| P | Pause/Resume |
| R | Restart mission |
| M | Mute/Unmute sound |
| [ / ] | Lower / raise volume |
| A | Achievements (main menu) |
| ESC | Pause / Return to menu |
| Enter | Start / Resume |
| O | Quit |
| Mouse | Click menu buttons |

## Power-Ups

| Power-Up | Effect |
|---|---|
| Green Cross (+) | Restore 40 HP |
| Cyan Shield | Add 60 shield points |
| Yellow Triangle | Rapid fire for ~12 seconds |
| Orange Spread | 5-way spread shot for ~12 seconds |
| Purple Bolt | Overdrive (+75% damage) for ~10 seconds |
| Red Bomb | Clear enemy projectiles & damage boss |
| Pink Heart | Gain an extra life |

## Tips
- Keep moving - boss bullets become dense on later waves
- Build combos by chaining hits without getting hit
- Save your shields for the most dangerous barrages
- Overdrive is devastating on low-health bosses
- Bombs are great when overwhelmed by enemy fire

## Technical Details
- **Engine**: Python + Pygame
- **Save Location**: `saves/save_data.json` (backup at `saves/save_data.json.bak`)
- **Audio**: Procedurally synthesised with `pygame.mixer`
- **Architecture**: Object-oriented design with clean separation of concerns
- **Performance**: Delta-time aware updates, efficient collision checks, object cleanup

## Testing
```bash
python -m pytest tests/test_basic.py -v
```

## Credits
Heavily enhanced with new systems, effects, and polish while keeping the core arcade spirit intact.
