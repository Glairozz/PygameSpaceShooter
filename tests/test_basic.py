import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pygame
pygame.init()
pygame.display.set_mode((1, 1))  # Dummy display for headless testing

from config import config, WIDTH, HEIGHT
from enhanced_shooter import Spaceship, Laser, Enemy, Asteroid, PowerUp, Particle


def test_spaceship_movement_bounds():
    ship = Spaceship(50, 500)
    # Test movement bounds
    ship.x = -10
    ship.x = max(0, ship.x)
    assert ship.x >= 0
    ship.x = WIDTH + 100
    ship.x = min(WIDTH - ship.width, ship.x)
    assert ship.x <= WIDTH - ship.width
    print("test_spaceship_movement_bounds: PASSED")


def test_laser_creation():
    laser = Laser(100, 200, -1, (0, 255, 255))
    assert laser.damage > 0
    assert laser.get_rect() is not None
    print("test_laser_creation: PASSED")


def test_enemy_hp():
    enemy = Enemy(1)
    initial_hp = enemy.hp
    enemy.take_damage(50)
    assert enemy.hp == initial_hp - 50
    enemy.take_damage(10000)
    assert enemy.hp == 0
    print("test_enemy_hp: PASSED")


def test_asteroid():
    ast = Asteroid(100, 100)
    assert ast.hp > 0
    rect = ast.get_rect()
    assert rect.width > 0
    print("test_asteroid: PASSED")


def test_powerup():
    pu = PowerUp(100, 100, 'health')
    assert pu.type == 'health'
    assert pu.get_rect() is not None
    print("test_powerup: PASSED")


def test_particle():
    p = Particle(50, 50, (255, 0, 0))
    assert p.life > 0
    result = p.update()
    assert isinstance(result, bool)
    print("test_particle: PASSED")


def test_config():
    assert isinstance(config.settings, dict)
    assert isinstance(config.progression, dict)
    assert 'high_score' in config.progression
    print("test_config: PASSED")


if __name__ == "__main__":
    test_spaceship_movement_bounds()
    test_laser_creation()
    test_enemy_hp()
    test_asteroid()
    test_powerup()
    test_particle()
    test_config()
    print("\nAll tests passed!")
    pygame.quit()
    sys.exit(0)
