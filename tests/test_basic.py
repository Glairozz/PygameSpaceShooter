"""Tests for Dragon Roaster.

The SDL drivers are forced to dummy so the suite also works on headless CI.
Run with ``python -m pytest`` or ``python tests/test_basic.py``.
"""
import os
import sys
from collections import defaultdict
from contextlib import contextmanager
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
    DEFAULT_PROGRESSION,
    DEFAULT_SETTINGS,
    DIFFICULTIES,
    HEIGHT,
    MAX_ROUNDS,
    STARTING_LIVES,
    WIDTH,
    GameConfig,
    config,
)
from enhanced_shooter import (  # noqa: E402
    Asteroid,
    EnhancedGame,
    Enemy,
    FloatingText,
    Laser,
    Minion,
    Particle,
    PowerUp,
    Spaceship,
    UPGRADES_BY_KEY,
    UPGRADE_POOL,
)


def _keys(**pressed):
    mapping = {getattr(pygame, f"K_{name.upper()}"): True for name, value in pressed.items() if value}
    return defaultdict(bool, mapping)


@contextmanager
def fresh_game():
    """Give a test a clean, deterministic game that never touches the save file."""
    game = EnhancedGame()
    original_settings = copy.deepcopy(game.config.settings)
    original_progression = copy.deepcopy(game.config.progression)
    original_save = game.config.save
    try:
        game.config.settings.clear()
        game.config.settings.update(copy.deepcopy(DEFAULT_SETTINGS))
        game.config.progression.clear()
        game.config.progression.update(copy.deepcopy(DEFAULT_PROGRESSION))
        game.config.save = lambda: None
        game.achievements_unlocked = set()
        game.reset_run()
        game.game_state = "landing"
        yield game
    finally:
        game.config.settings = original_settings
        game.config.progression = original_progression
        game.config.save = original_save


# ---------------------------------------------------------------------------
# Player and projectiles
# ---------------------------------------------------------------------------
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


def test_upgraded_and_critical_lasers():
    ship = Spaceship(100, 500)
    ship.last_shot = -10000
    ship.damage_multiplier = 2.0
    ship.crit_chance = 1.0
    lasers = ship.shoot()
    assert lasers
    assert all(laser.crit for laser in lasers)
    assert all(laser.damage >= 52 for laser in lasers)
    assert all(laser.color == (255, 210, 70) for laser in lasers)


def test_dash_mechanic():
    ship = Spaceship(200, 600)
    keys = _keys(right=True, up=True)
    assert ship.start_dash(keys) is True
    assert ship.dash_time > 0
    assert ship.invulnerable > 0
    assert ship.dash_count == 1

    start_x = ship.x
    ship.move(keys, dt=1.0)
    assert ship.x > start_x

    # Cooldown blocks a second dash until it expires.
    assert ship.start_dash(keys) is False
    ship.dash_time = 0
    ship.dash_cooldown = 0
    assert ship.start_dash(_keys()) is True
    assert ship.dash_direction == (0.0, -1.0)


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

    # Regression: the glow rectangle used to be passed with a broken
    # signature and raised a TypeError while drawing.
    surface = pygame.Surface((WIDTH, HEIGHT))
    laser.y = 100
    laser.draw(surface)


# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
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


def test_difficulty_scales_bosses():
    cadet = Enemy(3, "cadet")
    pilot = Enemy(3, "pilot")
    ace = Enemy(3, "ace")
    assert cadet.hp < pilot.hp < ace.hp
    assert cadet.shoot_delay > pilot.shoot_delay > ace.shoot_delay
    assert cadet.damage_scale < ace.damage_scale


def test_enemy_shoots_every_wave():
    for round_number in range(1, MAX_ROUNDS + 1):
        enemy = Enemy(round_number)
        enemy.last_shot = -10000
        lasers = enemy.shoot(target_x=WIDTH // 2, target_y=HEIGHT - 200)
        assert lasers, f"wave {round_number} produced no shots"
        assert all(laser.direction == 1 for laser in lasers)


def test_minion_behavior():
    minion = Minion(4)
    assert minion.hp > 0
    assert minion.get_rect().width > 0

    start_y = minion.y
    minion.move()
    assert minion.y > start_y

    minion.last_shot = -10000
    shots = minion.shoot()
    assert shots
    assert shots[0].direction == 1
    assert shots[0].damage > 0

    minion.take_damage(100000)
    assert minion.hp == 0


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


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def test_config_has_defaults():
    assert isinstance(config.settings, dict)
    assert isinstance(config.progression, dict)
    assert config.progression["high_score"] >= 0
    assert "muted" in config.settings
    assert "victory" in ACHIEVEMENTS
    assert config.settings["difficulty"] in DIFFICULTIES
    assert len(ACHIEVEMENTS) >= 16


def test_config_sanitizes_invalid_settings():
    game_config = GameConfig()
    game_config.settings["difficulty"] = "impossible"
    game_config.settings["particle_quality"] = "ultra"
    game_config.settings["sfx_volume"] = 12
    game_config._sanitize()
    assert game_config.settings["difficulty"] == "pilot"
    assert game_config.settings["particle_quality"] == "high"
    assert game_config.settings["sfx_volume"] == 1.0


# ---------------------------------------------------------------------------
# Full game
# ---------------------------------------------------------------------------
def test_game_start_life_loss_and_game_over():
    with fresh_game() as game:
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


def test_difficulty_selection_and_lives():
    with fresh_game() as game:
        assert game.set_difficulty("ace") is True
        assert game.config.settings["difficulty"] == "ace"
        assert game.difficulty_key == "ace"

        game.start_game()
        assert game.spaceship.lives == DIFFICULTIES["ace"]["lives"]
        assert game.enemy.difficulty == "ace"
        assert game.score_scale == DIFFICULTIES["ace"]["score"]

        assert game.set_difficulty("nope") is False

        game.game_state = "landing"
        game._handle_key(pygame.K_1)
        assert game.difficulty_key == "cadet"


def test_upgrade_selection_applies():
    with fresh_game() as game:
        game.start_game()
        ship = game.spaceship

        game.game_state = "upgrade"
        game.upgrade_choices = [UPGRADES_BY_KEY["damage"]]
        before_damage = ship.damage_multiplier
        assert game.choose_upgrade(0) is True
        assert ship.damage_multiplier > before_damage
        assert game.upgrades["damage"] == 1
        assert game.run_upgrades == 1
        assert game.round == 2
        assert game.game_state == "playing"

        game.game_state = "upgrade"
        game.upgrade_choices = [UPGRADES_BY_KEY["hull"]]
        before_hp = ship.max_hp
        game.choose_upgrade(0)
        assert ship.max_hp == before_hp + 25

        game.game_state = "upgrade"
        game.upgrade_choices = [UPGRADES_BY_KEY["shield"]]
        before_shield = ship.shield_max
        game.choose_upgrade(0)
        assert ship.shield_max == before_shield + 40

        game.game_state = "upgrade"
        game.upgrade_choices = [UPGRADES_BY_KEY["life"]]
        before_lives = ship.lives
        game.choose_upgrade(0)
        assert ship.lives == before_lives + 1

        # Invalid selections are rejected.
        assert game.choose_upgrade(0) is False


def test_upgrade_pool_exhaustion_gives_repair():
    with fresh_game() as game:
        game.upgrades = {
            upgrade["key"]: upgrade["max_level"] for upgrade in UPGRADE_POOL
        }
        choices = game.generate_upgrades()
        assert len(choices) == 1
        assert choices[0]["key"] == "repair"


def test_minion_defeat_scoring():
    with fresh_game() as game:
        game.start_game()
        minion = Minion(2)
        game.minions = [minion]
        before_score = game.score
        before_combo = game.combo

        game.on_minion_defeated(minion)
        assert minion not in game.minions
        assert game.run_minions == 1
        assert game.score > before_score
        assert game.combo > before_combo
        assert game.config.progression["total_minions_defeated"] == 1


def test_dash_key_and_counter():
    with fresh_game() as game:
        game.start_game()
        before = game.config.progression["total_dashes"]
        assert game._handle_key(pygame.K_x) is True
        assert game.run_dashes == 1
        assert game.config.progression["total_dashes"] == before + 1
        assert game.spaceship.dash_cooldown > 0


def test_particle_quality_scaling():
    with fresh_game() as game:
        game.config.settings["particle_quality"] = "low"
        game.particles.clear()
        game.add_particles(10, 10, (255, 0, 0), 100)
        low_count = len(game.particles)

        game.config.settings["particle_quality"] = "high"
        game.particles.clear()
        game.add_particles(10, 10, (255, 0, 0), 100)
        high_count = len(game.particles)

        assert 0 < low_count < high_count


def test_new_achievement_conditions():
    with fresh_game() as game:
        game.config.settings["difficulty"] = "ace"
        game.start_game()
        game.config.progression["total_minions_defeated"] = 50
        game.config.progression["total_dashes"] = 25
        game.run_upgrades = 5
        game.game_state = "victory"
        game.check_achievements()

        for key in (
            "swarm_breaker",
            "dash_master",
            "fully_loaded",
            "ace_victory",
        ):
            assert key in game.achievements_unlocked


def test_full_campaign_reaches_victory():
    with fresh_game() as game:
        game.start_game()
        for expected_round in range(1, MAX_ROUNDS + 1):
            assert game.round == expected_round
            assert game.game_state == "playing"
            game.enemy.hp = 0
            game.update()

            if expected_round < MAX_ROUNDS:
                assert game.game_state == "upgrade"
                assert game.upgrade_choices
                assert game.choose_upgrade(0) is True
                assert game.game_state == "playing"

        assert game.game_state == "victory"
        assert "victory" in game.achievements_unlocked


def test_game_smoke_render_and_update():
    with fresh_game() as game:
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
        game.minions.append(Minion(3))
        game.minions.append(Minion(5))

        for _ in range(90):
            game.update()
            game.draw()

        # Upgrade overlay
        game.game_state = "upgrade"
        game.upgrade_choices = game.generate_upgrades()
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
        game.show_achievements = False
        game.show_stats = True
        game.draw()
        game.show_stats = False


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
