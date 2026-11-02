"""Tests for Dragon Roaster.

The SDL drivers are forced to dummy so the suite also works on headless CI.
Run with ``python -m pytest`` or ``python tests/test_basic.py``.
"""
import os
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).parent.parent))

import copy

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from config import (  # noqa: E402
    ACHIEVEMENTS,
    HEIGHT,
    MAX_ROUNDS,
    STARTING_LIVES,
    WIDTH,
    config,
)
from enhanced_shooter import (  # noqa: E402
    Asteroid,
    EnhancedGame,
    Enemy,
    FloatingText,
    Laser,
    Particle,
    PowerUp,
    Spaceship,
)


def _keys(**pressed):
    mapping = {getattr(pygame, f"K_{name.upper()}"): True for name, value in pressed.items() if value}
    return defaultdict(bool, mapping)


def test_spaceship_movement_bounds():
    ship = Spaceship(0, HEIGHT // 4)
    ship.move(_keys(left=True), dt=1.0)
    assert ship.x >= 0

    ship.x = WIDTH - ship.width
    ship.move(_keys(right=True), dt=1.0)
    assert ship.x <= WIDTH - ship.width

    ship.y = HEIGHT // 4
    ship.move(_keys(up=True), dt=1.0)
    assert ship.y >= HEIGHT // 4

    ship.y = HEIGHT - ship.height - 35
    ship.move(_keys(down=True), dt=1.0)
    assert ship.y <= HEIGHT - ship.height - 35


def test_spaceship_shoot_and_damage():
    ship = Spaceship(100, 500)
    ship.last_shot = -10000
    lasers = ship.shoot()
    assert lasers
    assert all(laser.damage > 0 for laser in lasers)

    ship.invulnerable = 0
    ship.shield = 50
    assert ship.take_damage(30) is True
    assert ship.shield == 20
    assert ship.hp == 100

    ship.invulnerable = 0
    assert ship.take_damage(30) is True
    assert ship.shield == 0
    assert ship.hp == 90

    assert ship.take_damage(10) is False  # invulnerability window


def test_respawn_restores_ship():
    ship = Spaceship(100, 500)
    ship.hp = 0
    ship.lives = 1
    ship.respawn()
    assert ship.hp == ship.max_hp
    assert ship.shield == 0
    assert ship.invulnerable > 0


def test_laser_creation_and_bounds():
    laser = Laser(100, 200, -1, (0, 255, 255))
    assert laser.damage > 0
    assert laser.get_rect().width > 0
    assert not laser.is_off_screen()
    laser.y = -1000
    assert laser.is_off_screen()


def test_enemy_scaling_and_damage():
    first = Enemy(1)
    last = Enemy(MAX_ROUNDS)
    assert last.hp > first.hp
    assert last.name
    initial_hp = first.hp
    first.take_damage(50)
    assert first.hp == initial_hp - 50
    assert first.take_damage(100000) is True
    assert first.hp == 0


def test_enemy_shoots_every_wave():
    for round_number in range(1, MAX_ROUNDS + 1):
        enemy = Enemy(round_number)
        enemy.last_shot = -10000
        lasers = enemy.shoot(target_x=WIDTH // 2, target_y=HEIGHT - 200)
        assert lasers, f"wave {round_number} produced no shots"
        assert all(laser.direction == 1 for laser in lasers)


def test_asteroid():
    asteroid = Asteroid(100, 100)
    assert asteroid.hp > 0
    assert asteroid.get_rect().width > 0
    asteroid.take_damage(asteroid.hp)
    assert asteroid.hp == 0


def test_powerups():
    for power_type in (
        "health",
        "shield",
        "rapid",
        "spread",
        "bomb",
        "life",
        "overdrive",
    ):
        powerup = PowerUp(100, 100, power_type)
        assert powerup.type == power_type
        assert powerup.get_rect().width > 0


def test_particle_and_floating_text():
    particle = Particle(50, 50, (255, 0, 0))
    assert particle.life > 0
    assert isinstance(particle.update(), bool)

    text = FloatingText(10, 10, "+100")
    assert text.update() is True


def test_config_has_defaults():
    assert isinstance(config.settings, dict)
    assert isinstance(config.progression, dict)
    assert config.progression["high_score"] >= 0
    assert "muted" in config.settings
    assert "victory" in ACHIEVEMENTS


def test_game_start_life_loss_and_game_over():
    game = EnhancedGame()
    config_snapshot = copy.deepcopy(game.config.progression)
    game.config.save = lambda: None
    try:
        game.start_game()
        assert game.game_state == "playing"
        assert game.spaceship.lives == STARTING_LIVES
        assert game.round == 1

        game.spaceship.invulnerable = 0
        game.spaceship.hp = 0
        game.spaceship.lives = 2
        game.handle_player_death()
        assert game.game_state == "playing"
        assert game.spaceship.lives == 1
        assert game.spaceship.hp == game.spaceship.max_hp

        game.spaceship.invulnerable = 0
        game.spaceship.hp = 0
        game.handle_player_death()
        assert game.spaceship.lives == 0
        assert game.game_state == "game_over"
    finally:
        game.config.progression = config_snapshot
        try:
            del game.config.save
        except AttributeError:
            pass


def test_full_campaign_reaches_victory():
    game = EnhancedGame()
    config_snapshot = copy.deepcopy(game.config.progression)
    game.config.save = lambda: None
    try:
        game.start_game()
        for expected_round in range(1, MAX_ROUNDS + 1):
            assert game.round == expected_round
            assert game.game_state == "playing"
            game.enemy.hp = 0
            game.update()
        assert game.game_state == "victory"
        assert "victory" in game.achievements_unlocked
    finally:
        game.config.progression = config_snapshot
        try:
            del game.config.save
        except AttributeError:
            pass


def test_game_smoke_render_and_update():
    game = EnhancedGame()
    config_snapshot = copy.deepcopy(game.config.progression)
    game.config.save = lambda: None
    try:
        game.start_game()
        for power_type in (
            "health",
            "shield",
            "rapid",
            "spread",
            "bomb",
            "life",
            "overdrive",
        ):
            game.apply_powerup(power_type)
        game.add_toast("TEST TOAST", (255, 255, 0), 30)
        game.show_banner("TEST", "BANNER", 30)

        for _ in range(90):
            game.update()
            game.draw()

        game.game_state = "paused"
        game.draw()
        game.game_state = "game_over"
        game.game_over_reason = "Test"
        game.draw()
        game.game_state = "victory"
        game.draw()
        game.game_state = "landing"
        game.draw()
        game.show_achievements = True
        game.draw()
    finally:
        game.config.progression = config_snapshot
        try:
            del game.config.save
        except AttributeError:
            pass


if __name__ == "__main__":
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"{test.__name__}: PASSED")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"{test.__name__}: FAILED - {exc}")
    pygame.quit()
    if failures:
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed!")
    sys.exit(0)
