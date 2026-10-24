# Dragon Roaster - Enhanced Space Shooter

A polished, feature-rich 2D space shooter built with Python and Pygame. Fight through waves of enemies and bosses, collect power-ups, and aim for the high score!

## Features

### Gameplay
- **Smooth Controls**: Responsive WASD/Arrow key movement with proper screen boundaries
- **Dynamic Combat**: Player and enemy lasers with collision detection
- **Multiple Enemy Types**: Progressively challenging bosses across 6 rounds
- **Power-Up System**: Health, shields, rapid fire, spread shot, and bomb power-ups
- **Particle Effects**: Explosions, hits, and visual feedback
- **Screen Shake**: Impact feedback for powerful hits
- **Parallax Starfield**: Multi-layer animated background

### UI & Menus
- **Polished Main Menu**: Clean space-themed interface
- **In-Game HUD**: Health, shield, score, round, and active power-up timers
- **Boss Health Bar**: Clear indicator during boss fights
- **Pause Menu**: Resume, restart, or quit
- **Game Over/Victory Screens**: Score display with high score tracking

### Progression & Persistence
- **High Score System**: Persistent high scores saved locally
- **Settings System**: Configurable volumes and preferences (saved to JSON)
- **Statistics Tracking**: Games played, bosses defeated, etc.

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
# or
python enhanced_shooter.py
```

## Controls

| Key | Action |
|---|---|
| WASD / Arrow Keys | Move spaceship |
| Space | Shoot |
| P | Pause/Resume |
| R | Restart game |
| O | Quit game |
| Mouse | Navigate menus |

## Power-Ups

| Power-Up | Effect |
|---|---|
| Green Cross (+) | Restore 30 HP |
| Cyan Shield | Add shield protection |
| Yellow Triangle | Rapid fire for 10 seconds |
| Orange Spread | Spread shot for 10 seconds |
| Red Bomb | Clear all enemy projectiles |

## Tips
- Stay mobile to avoid enemy fire
- Collect power-ups to gain advantages
- Use spread shot for groups of threats
- Shields absorb damage before health
- Bosses get harder with each round

## Technical Details

- **Engine**: Python + Pygame
- **Save Location**: `saves/save_data.json`
- **Architecture**: Object-oriented design with classes for game entities
- **Performance**: Delta-time aware movement, object pooling patterns, efficient collision detection
- **Code Style**: Follows PEP 8 conventions

## Troubleshooting

If you encounter audio issues, the game will run without sound. For display issues, try running in windowed mode.

## Credits
Original concept enhanced and polished for better gameplay experience.
