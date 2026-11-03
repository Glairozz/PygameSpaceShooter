# Dragon Roaster - Enhanced Space Shooter

A polished, feature-rich arcade shooter built with Python and Pygame. Fight through 7 boss waves, build huge combos, pick permanent run upgrades, dash through bullet storms, collect power-ups, unlock achievements, and chase a new high score.

## What's New in v4

- **Between-wave upgrades** - Clear a boss, then choose 1 of 3 permanent upgrades for the rest of the run (damage, fire rate, speed, hull, shield, crit, dash, extra life)
- **Difficulty modes** - Cadet, Pilot, and Ace change boss HP, boss damage, fire rate, starting lives, and score multiplier
- **Minion swarms** - Fast escorts now spawn alongside bosses, shoot at you, and feed the combo meter
- **Dash / phase drive** - `SHIFT` or `X` bursts in your movement direction with brief invulnerability and a cooldown meter
- **5 new achievements** - Including Swarm Breaker, Dash Master, Fully Loaded, Galaxy Legend, and Ace of Aces (17 total)
- **Fullscreen + particle settings** - `F11` toggles fullscreen; `V` cycles Low / Medium / High particle quality. Both are saved
- **Career stats screen** - Press `S` on the menu to review lifetime progress
- **Performance work** - Cached nebula surfaces, reduced particle counts on lower settings, and a fixed laser-glow render bug
- **Smarter feedback** - Critical hits, combo milestone toasts, dash trails, mute button on the pause menu, and richer end-of-run stats

## Features

### Gameplay
- **Responsive controls** - Smooth WASD/Arrow movement with delta-time-aware updates
- **Dash with i-frames** - Escape tight patterns and reposition quickly
- **Three difficulties** - Cadet for a relaxed run, Pilot for the intended experience, Ace for a serious challenge
- **Tight combat** - Player and enemy lasers, asteroids, minion swarms, and accurate collision detection
- **Progressive difficulty** - Bosses grow stronger and more aggressive across all 7 waves
- **Run upgrades** - Every cleared wave offers 3 upgrade cards; stacking choices shapes each run
- **Combo system** - Chain hits to build a score multiplier and earn milestone bonuses
- **Power-up drops** - Seven pickup types keep every run different
- **Screen shake, particles, and floating text** - Punchy feedback on hits, crits, and explosions

### UI & Menus
- **Polished main menu** - Mission briefing, high score, best combo, best wave, and achievement progress
- **Difficulty selector** - Click the buttons or press `1`, `2`, `3`
- **Upgrade cards** - Choose with `1`-`3`, `ENTER`, or by clicking
- **Achievements screen** - Press `A` on the main menu to browse all 17 unlocks
- **Career stats screen** - Press `S` for lifetime statistics
- **In-game HUD** - HP, shield, lives, active timers, dash cooldown, boss bar, combo meter, score, difficulty, and upgrade count
- **Pause menu** - Resume, toggle sound, or return to menu; shows current run stats
- **Game Over/Victory screens** - Full stats breakdown with "New High Score" callouts
- **Achievement toasts** - Instant feedback when you unlock something

### Progression & Persistence
- **High score tracking** - Persistent across runs
- **Statistics** - Games played, victories, bosses defeated, minions destroyed, best combo, best wave, lasers fired, dashes, power-ups collected
- **Achievements** - 17 unlockable achievements
- **Settings** - Volume, mute, difficulty, fullscreen, particle quality, and other preferences saved to JSON
- **Safe saves** - Atomic writes with automatic `.bak` backups and schema migration

## Installation

### Requirements
- Python 3.8 or higher
- Pygame 2.1 or higher

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

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
| Shift / X / Ctrl | Dash (brief invulnerability) |
| P | Pause/Resume |
| R | Restart mission |
| M | Mute/Unmute sound |
| [ / ] | Lower / raise volume |
| F11 | Toggle fullscreen |
| V | Cycle particle quality |
| A | Achievements (main menu) |
| S | Career stats (main menu) |
| 1 / 2 / 3 | Pick difficulty, or choose an upgrade |
| Enter | Start / Resume / confirm first upgrade |
| ESC | Pause / Return to menu / close overlay |
| O | Quit |
| Mouse | Click menu buttons and upgrade cards |

## Difficulty Modes

| Mode | Lives | Boss HP | Boss Damage | Boss Fire Rate | Score |
|---|---|---|---|---|---|
| Cadet | 4 | 75% | 70% | Slower | 0.8x |
| Pilot | 3 | 100% | 100% | Normal | 1.0x |
| Ace | 2 | 130% | 135% | Faster | 1.6x |

## Upgrades

After each of the first six bosses, choose one of three cards. Upgrades last for the current run only.

| Upgrade | Effect | Max Level |
|---|---|---|
| Plasma Coils | +15% laser damage | 5 |
| Overclocked Core | -12% fire delay | 4 |
| Ion Thrusters | +10% move speed | 4 |
| Reinforced Hull | +25 max HP and heal | 4 |
| Aegis Matrix | +40 shield capacity | 3 |
| Targeting AI | +8% critical chance | 3 |
| Phase Drive | -20% dash cooldown | 2 |
| Spare Hull | +1 extra life | 1 |

## Power-Ups

| Power-Up | Effect |
|---|---|
| Green Cross (+) | Restore 40 HP |
| Cyan Shield | Add 60 shield points |
| Yellow Triangle | Rapid fire for ~12 seconds |
| Orange Spread | 5-way spread shot for ~12 seconds |
| Purple Bolt | Overdrive (+75% damage) for ~10 seconds |
| Red Bomb | Clear enemy projectiles, damage the boss and nearby minions |
| Pink Heart | Gain an extra life |

## Achievements

| Achievement | Requirement |
|---|---|
| First Blood | Defeat your first boss |
| Rookie Pilot | Reach a score of 1,000 |
| Ace Pilot | Reach a score of 5,000 |
| Living Legend | Reach a score of 10,000 |
| Galaxy Legend | Reach a score of 25,000 |
| Combo Starter | Reach a 10x combo |
| Chain Reaction | Reach a 25x combo |
| Boss Hunter | Defeat 10 bosses across all runs |
| Swarm Breaker | Destroy 50 minions across all runs |
| Dash Master | Perform 25 dashes across all runs |
| Fully Loaded | Take 5 upgrades in a single run |
| Survivor | Reach wave 3 |
| Dragon Slayer | Complete all 7 waves |
| Untouchable | Win without losing a life |
| Ace of Aces | Complete all 7 waves on Ace difficulty |
| Collector | Collect 25 power-ups across all runs |
| Sharpshooter | Fire 500 lasers across all runs |

## Tips
- Keep moving - boss bullets become dense on later waves
- Dash gives brief invulnerability; use it to cut through a barrage instead of fleeing
- Build combos by chaining hits without getting hit
- Save shields for the most dangerous barrages
- Target minions early so their bullets do not pile up
- Overdrive is devastating on low-health bosses
- Bombs are great when overwhelmed by enemy fire
- Crit stacking plus Plasma Coils melts bosses quickly

## Technical Details
- **Engine**: Python + Pygame
- **Save location**: `saves/save_data.json` (backup at `saves/save_data.json.bak`)
- **Audio**: Procedurally synthesised with `pygame.mixer` (no audio assets needed)
- **Architecture**: Object-oriented design with clean separation of concerns
- **Performance**: Delta-time updates, cached nebula surfaces, quality-scaled particles, efficient collision checks, object cleanup

## Project Structure

```
main.py               Entry point (--classic for the original prototype)
enhanced_shooter.py   v4 game: player, enemies, upgrades, HUD, menus
dragon_shooter.py     Original prototype
config.py             Constants, difficulty table, achievements, save system
audio.py              Procedural sound synthesis and playback
tests/test_basic.py   Headless test suite
```

## Testing
```bash
python -m pytest tests/test_basic.py -v
```

The suite forces SDL's dummy drivers, so it runs without a display or audio device.

## Credits
Heavily enhanced with new systems, effects, and polish while keeping the core arcade spirit intact.
