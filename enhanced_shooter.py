"""Enhanced Pygame space shooter - Dragon Roaster v3.

A single-file arcade shooter with procedural audio, boss waves, combos,
power-ups, achievements and persistent progression.
"""
from __future__ import annotations

import math
import random

import pygame

from audio import SoundManager
from config import *

pygame.init()

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
POWERUP_TYPES = ("health", "shield", "rapid", "spread", "bomb", "life", "overdrive")
POWERUP_COLORS = {
    "health": GREEN,
    "shield": CYAN,
    "rapid": YELLOW,
    "spread": ORANGE,
    "bomb": RED,
    "life": PINK,
    "overdrive": PURPLE,
}
POWERUP_LABELS = {
    "health": "+40 HP",
    "shield": "+60 SHIELD",
    "rapid": "RAPID FIRE",
    "spread": "SPREAD SHOT",
    "bomb": "BOMB!",
    "life": "EXTRA LIFE",
    "overdrive": "OVERDRIVE",
}

BOSS_DATA = (
    {
        "name": "Crimson Scout",
        "color": (235, 70, 70),
        "accent": (255, 200, 90),
        "width": 90,
        "height": 70,
        "speed": 4.4,
    },
    {
        "name": "Ember Interceptor",
        "color": (245, 115, 45),
        "accent": (255, 235, 120),
        "width": 96,
        "height": 72,
        "speed": 4.8,
    },
    {
        "name": "Violet Destroyer",
        "color": (155, 80, 225),
        "accent": (230, 170, 255),
        "width": 104,
        "height": 76,
        "speed": 4.2,
    },
    {
        "name": "Iron Dreadnought",
        "color": (85, 125, 210),
        "accent": (160, 220, 255),
        "width": 112,
        "height": 82,
        "speed": 3.8,
    },
    {
        "name": "Phantom Wraith",
        "color": (0, 195, 175),
        "accent": (180, 255, 240),
        "width": 108,
        "height": 80,
        "speed": 4.6,
    },
    {
        "name": "Magma Titan",
        "color": (220, 65, 120),
        "accent": (255, 180, 80),
        "width": 124,
        "height": 90,
        "speed": 3.6,
    },
    {
        "name": "Dragon Lord",
        "color": (255, 175, 40),
        "accent": (255, 70, 50),
        "width": 132,
        "height": 96,
        "speed": 3.4,
    },
)

# ---------------------------------------------------------------------------
# Between-wave upgrades (roguelite style)
# ---------------------------------------------------------------------------
UPGRADE_POOL = (
    {
        "key": "damage",
        "name": "PLASMA COILS",
        "desc": "+15% laser damage",
        "color": CYAN,
        "max_level": 5,
    },
    {
        "key": "firerate",
        "name": "OVERCLOCKED CORE",
        "desc": "-12% fire delay",
        "color": YELLOW,
        "max_level": 4,
    },
    {
        "key": "speed",
        "name": "ION THRUSTERS",
        "desc": "+10% move speed",
        "color": LIGHT_BLUE,
        "max_level": 4,
    },
    {
        "key": "hull",
        "name": "REINFORCED HULL",
        "desc": "+25 max HP and heal",
        "color": GREEN,
        "max_level": 4,
    },
    {
        "key": "shield",
        "name": "AEGIS MATRIX",
        "desc": "+40 shield capacity",
        "color": TEAL,
        "max_level": 3,
    },
    {
        "key": "crit",
        "name": "TARGETING AI",
        "desc": "+8% critical chance",
        "color": GOLD,
        "max_level": 3,
    },
    {
        "key": "dash",
        "name": "PHASE DRIVE",
        "desc": "-20% dash cooldown",
        "color": MAGENTA,
        "max_level": 2,
    },
    {
        "key": "life",
        "name": "SPARE HULL",
        "desc": "+1 extra life",
        "color": PINK,
        "max_level": 1,
    },
)
UPGRADES_BY_KEY = {upgrade["key"]: upgrade for upgrade in UPGRADE_POOL}

PARTICLE_QUALITY_SCALE = {"low": 0.35, "medium": 0.65, "high": 1.0}

COMBO_MILESTONES = (10, 25, 50, 100)



def clamp(value, low, high):
    return max(low, min(high, value))


def lerp_color(first, second, amount):
    amount = clamp(amount, 0.0, 1.0)
    return tuple(
        int(first[index] + (second[index] - first[index]) * amount)
        for index in range(3)
    )


# ---------------------------------------------------------------------------
# Background and effects
# ---------------------------------------------------------------------------
class Particle:
    def __init__(
        self,
        x,
        y,
        color,
        vx=None,
        vy=None,
        life=40,
        size=None,
        shape="circle",
        gravity=0.15,
    ):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-8, 8)
        self.vy = vy if vy is not None else random.uniform(-8, 8)
        self.life = life
        self.max_life = max(1, life)
        self.size = size if size is not None else random.randint(1, 4)
        self.gravity = gravity
        self.shape = shape

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.98
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        if self.life <= 0:
            return
        ratio = self.life / self.max_life
        alpha = int(255 * ratio)
        size = max(1, int(self.size * ratio))
        surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        color = (*self.color, alpha)
        if self.shape == "rect":
            pygame.draw.rect(
                surface, color, (size, size, size * 2, size * 2), border_radius=1
            )
        else:
            pygame.draw.circle(surface, color, (size * 2, size * 2), size)
        screen.blit(surface, (int(self.x - size * 2), int(self.y - size * 2)))


class FloatingText:
    """Short-lived score / status text that drifts upward."""

    def __init__(self, x, y, text, color=GOLD, life=55, size="tiny"):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = life
        self.max_life = max(1, life)
        self.size = size

    def update(self):
        self.y -= 0.9
        self.life -= 1
        return self.life > 0

    def draw(self, screen, fonts):
        if self.life <= 0:
            return
        font = fonts.get(self.size, fonts["tiny"])
        surface = font.render(self.text, True, self.color)
        surface.set_alpha(int(255 * (self.life / self.max_life)))
        rect = surface.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(surface, rect)


class Star:
    def __init__(self, layer=0):
        self.layer = layer
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.base_speed = 0.3 + layer * 0.7
        self.speed = self.base_speed
        if layer == 0:
            self.size = 1
            self.color = random.choice([WHITE, LIGHT_BLUE])
        elif layer == 1:
            self.size = random.choice([1, 2])
            self.color = CYAN
        else:
            self.size = 2
            self.color = YELLOW
        self.twinkle = random.random() * math.tau

    def update(self, dt=1.0 / FPS):
        self.y += self.speed * dt * 60
        self.twinkle += dt * 3.0
        if self.y > HEIGHT:
            self.y = -2
            self.x = random.randint(0, WIDTH)

    def draw(self, screen):
        brightness = 0.7 + 0.3 * math.sin(self.twinkle)
        color = tuple(int(channel * brightness) for channel in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)


class Nebula:
    def __init__(self):
        self.x = random.randint(-200, WIDTH)
        self.y = random.randint(-300, HEIGHT - 300)
        self.size = random.randint(150, 300)
        self.color = random.choice([(80, 0, 120), (0, 50, 100), (100, 0, 80)])
        self.speed = random.uniform(0.15, 0.35)
        self.alpha = random.randint(20, 40)
        self._surface = None
        self._cache = None

    def _respawn(self):
        self.x = random.randint(-200, WIDTH)
        self.size = random.randint(150, 300)
        self.color = random.choice([(80, 0, 120), (0, 50, 100), (100, 0, 80)])
        self.alpha = random.randint(20, 40)
        self._surface = None
        self._cache = None

    def update(self, dt=1.0 / FPS):
        self.y += self.speed * dt * 60
        if self.y > HEIGHT:
            self._respawn()
            self.y = -self.size

    def draw(self, screen):
        # Rebuild the soft nebula surface only when its look changes.  This
        # removes three large per-frame surface allocations from the hot path.
        cache = (self.size, self.color, self.alpha)
        if self._surface is None or self._cache != cache:
            self._surface = pygame.Surface(
                (self.size, self.size), pygame.SRCALPHA
            )
            pygame.draw.circle(
                self._surface,
                (*self.color, self.alpha),
                (self.size // 2, self.size // 2),
                self.size // 2,
            )
            self._cache = cache
        screen.blit(self._surface, (int(self.x), int(self.y)))


# ---------------------------------------------------------------------------
# Pickups
# ---------------------------------------------------------------------------
class PowerUp:
    def __init__(self, x, y, power_type=None):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.speed = 2.4
        if power_type is None:
            self.type = random.choices(
                POWERUP_TYPES,
                weights=[18, 15, 15, 15, 9, 4, 10],
            )[0]
        else:
            self.type = power_type
        self.timer = 0
        self.bob = 0

    def update(self):
        self.y += self.speed
        self.timer += 1
        self.bob = math.sin(self.timer * 0.15) * 3
        return self.y < HEIGHT + 60

    def draw(self, screen):
        y_pos = self.y + self.bob
        pulse = abs(math.sin(self.timer * 0.12)) * 5 + 34
        glow = pygame.Surface((pulse, pulse), pygame.SRCALPHA)
        glow_color = (*POWERUP_COLORS.get(self.type, WHITE), 42)
        pygame.draw.circle(glow, glow_color, (pulse // 2, pulse // 2), pulse // 2)
        screen.blit(glow, (self.x + 16 - pulse // 2, y_pos + 16 - pulse // 2))

        color = POWERUP_COLORS.get(self.type, WHITE)
        if self.type == "health":
            pygame.draw.rect(
                screen, color, (self.x, y_pos, self.width, self.height), border_radius=4
            )
            pygame.draw.line(
                screen, WHITE, (self.x + 16, y_pos + 7), (self.x + 16, y_pos + 25), 5
            )
            pygame.draw.line(
                screen, WHITE, (self.x + 7, y_pos + 16), (self.x + 25, y_pos + 16), 5
            )
        elif self.type == "shield":
            pygame.draw.circle(
                screen, color, (self.x + 16, int(y_pos) + 16), 15, 4
            )
            pygame.draw.circle(
                screen, LIGHT_BLUE, (self.x + 16, int(y_pos) + 16), 8
            )
        elif self.type == "rapid":
            points = [
                (self.x + 17, y_pos),
                (self.x + 27, y_pos + 20),
                (self.x + 17, y_pos + 14),
                (self.x + 5, y_pos + 22),
            ]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        elif self.type == "spread":
            points = [
                (self.x + 16, y_pos),
                (self.x + 7, y_pos + 24),
                (self.x + 16, y_pos + 17),
                (self.x + 25, y_pos + 24),
            ]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        elif self.type == "bomb":
            pygame.draw.circle(screen, color, (self.x + 16, int(y_pos) + 17), 14)
            pygame.draw.circle(screen, WHITE, (self.x + 16, int(y_pos) + 11), 3)
            pygame.draw.line(
                screen, WHITE, (self.x + 16, y_pos + 13), (self.x + 16, y_pos + 19), 2
            )
        elif self.type == "life":
            heart_y = int(y_pos)
            pygame.draw.circle(screen, color, (self.x + 10, heart_y + 13), 7)
            pygame.draw.circle(screen, color, (self.x + 22, heart_y + 13), 7)
            pygame.draw.polygon(
                screen,
                color,
                [
                    (self.x + 3, heart_y + 15),
                    (self.x + 16, heart_y + 30),
                    (self.x + 29, heart_y + 15),
                ],
            )
            pygame.draw.line(
                screen,
                WHITE,
                (self.x + 16, heart_y + 8),
                (self.x + 16, heart_y + 18),
                2,
            )
        elif self.type == "overdrive":
            points = [
                (self.x + 19, y_pos + 2),
                (self.x + 8, y_pos + 17),
                (self.x + 15, y_pos + 17),
                (self.x + 11, y_pos + 30),
                (self.x + 26, y_pos + 12),
                (self.x + 18, y_pos + 12),
            ]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, WHITE, points, 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class Spaceship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 64
        self.height = 44
        self.speed = 7
        self.hp = 100
        self.max_hp = 100
        self.last_shot = 0
        self.shoot_delay = 170
        self.shield = 0
        self.shield_max = 150
        self.rapid_fire = 0
        self.spread_shot = 0
        self.overdrive = 0
        self.invulnerable = 90
        self.lives = STARTING_LIVES
        self.thruster_frame = 0
        self.hit_flash = 0

        # Run upgrades
        self.damage_multiplier = 1.0
        self.crit_chance = 0.0

        # Dash / phase drive
        self.dash_time = 0
        self.dash_cooldown = 0
        self.dash_cooldown_max = 105
        self.dash_direction = (0.0, -1.0)
        self.dash_count = 0

    def move(self, keys, dt=1.0):
        speed = self.speed * dt * 60

        if self.dash_time > 0:
            dx, dy = self.dash_direction
            self.x = max(
                0, min(WIDTH - self.width, self.x + dx * speed * 2.8)
            )
            self.y = max(
                HEIGHT // 4,
                min(HEIGHT - self.height - 35, self.y + dy * speed * 2.8),
            )
            self.thruster_frame += 1
            return

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(0, self.x - speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(WIDTH - self.width, self.x + speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(HEIGHT // 4, self.y - speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(HEIGHT - self.height - 35, self.y + speed)
        self.thruster_frame += 1

    def start_dash(self, keys):
        """Begin a short invulnerable burst. Returns True when it activates."""
        if self.dash_cooldown > 0 or self.dash_time > 0:
            return False

        dx = 0
        dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        if dx == 0 and dy == 0:
            dy = -1

        length = math.hypot(dx, dy) or 1.0
        self.dash_direction = (dx / length, dy / length)
        self.dash_time = 11
        self.dash_cooldown = self.dash_cooldown_max
        self.invulnerable = max(self.invulnerable, 15)
        self.dash_count += 1
        return True

    def _make_laser(self, x, y, color, angle=0, base_damage=26):
        damage = int(base_damage * self.damage_multiplier)
        critical = random.random() < self.crit_chance
        if critical:
            damage = int(damage * 2)
        laser = Laser(
            x,
            y,
            -1,
            GOLD if critical else color,
            angle=angle,
            damage=damage,
        )
        laser.crit = critical
        return laser

    def shoot(self):
        current_time = pygame.time.get_ticks()
        delay = self.shoot_delay // 2 if self.rapid_fire > 0 else self.shoot_delay
        if current_time - self.last_shot <= delay:
            return []
        self.last_shot = current_time
        lasers = []
        center_x = self.x + self.width // 2
        if self.spread_shot > 0:
            lasers.extend(
                [
                    self._make_laser(center_x, self.y, CYAN, base_damage=24),
                    self._make_laser(
                        center_x - 18, self.y + 8, CYAN, angle=-8, base_damage=24
                    ),
                    self._make_laser(
                        center_x + 18, self.y + 8, CYAN, angle=8, base_damage=24
                    ),
                    self._make_laser(
                        self.x + 15,
                        self.y + 12,
                        (100, 255, 255),
                        angle=-4,
                        base_damage=24,
                    ),
                    self._make_laser(
                        self.x + self.width - 15,
                        self.y + 12,
                        (100, 255, 255),
                        angle=4,
                        base_damage=24,
                    ),
                ]
            )
        else:
            lasers.append(self._make_laser(center_x, self.y, CYAN))
            if self.rapid_fire > 0:
                lasers.append(
                    self._make_laser(
                        self.x + 12,
                        self.y + 5,
                        (150, 255, 255),
                        base_damage=20,
                    )
                )
                lasers.append(
                    self._make_laser(
                        self.x + self.width - 12,
                        self.y + 5,
                        (150, 255, 255),
                        base_damage=20,
                    )
                )
        if self.overdrive > 0:
            for laser in lasers:
                laser.damage = int(laser.damage * 1.75)
                if not laser.crit:
                    laser.color = MAGENTA
        return lasers

    def update(self):
        if self.rapid_fire > 0:
            self.rapid_fire -= 1
        if self.spread_shot > 0:
            self.spread_shot -= 1
        if self.overdrive > 0:
            self.overdrive -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.dash_time > 0:
            self.dash_time -= 1
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

    def take_damage(self, damage):
        if self.invulnerable > 0:
            return False
        self.hit_flash = 8
        if self.shield > 0:
            self.shield -= damage
            if self.shield < 0:
                self.hp += self.shield
                self.shield = 0
        else:
            self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        self.invulnerable = 60
        return True

    def respawn(self):
        self.hp = self.max_hp
        self.shield = 0
        self.rapid_fire = 0
        self.spread_shot = 0
        self.overdrive = 0
        self.invulnerable = 170
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 190

    def draw(self, screen):
        if (
            self.invulnerable > 0
            and (self.invulnerable // 4) % 2 == 0
            and self.dash_time <= 0
        ):
            return

        if self.dash_time > 0:
            for index in range(1, 4):
                ghost_x = self.x - self.dash_direction[0] * index * 16
                ghost_y = self.y - self.dash_direction[1] * index * 16
                ghost = pygame.Surface(
                    (self.width, self.height), pygame.SRCALPHA
                )
                pygame.draw.polygon(
                    ghost,
                    (*CYAN, max(25, 110 - index * 28)),
                    [
                        (self.width // 2, 0),
                        (0, self.height),
                        (self.width // 2, self.height - 12),
                        (self.width, self.height),
                    ],
                )
                screen.blit(ghost, (ghost_x, ghost_y))

        if self.shield > 0:
            shield_surface = pygame.Surface(
                (self.width + 34, self.height + 34), pygame.SRCALPHA
            )
            alpha = int(120 * (self.shield / self.shield_max))
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 2
            pygame.draw.circle(
                shield_surface,
                (*CYAN, alpha),
                (self.width // 2 + 17, self.height // 2 + 17),
                int(39 + pulse),
                3,
            )
            screen.blit(shield_surface, (self.x - 17, self.y - 17))

        if (self.thruster_frame // 3) % 2 == 0:
            for offset in (-8, 8):
                center = (int(self.x + self.width // 2 + offset), int(self.y + self.height - 2))
                pygame.draw.circle(screen, ORANGE, center, 4)
                pygame.draw.circle(screen, YELLOW, center, 2)

        body = WHITE if self.hit_flash > 0 else (50, 100, 255)
        pygame.draw.polygon(
            screen,
            body,
            [
                (self.x + self.width // 2, self.y),
                (self.x, self.y + self.height),
                (self.x + self.width // 2, self.y + self.height - 12),
                (self.x + self.width, self.y + self.height),
            ],
        )
        pygame.draw.ellipse(
            screen, CYAN, (self.x + self.width // 2 - 9, self.y + 6, 18, 12)
        )
        pygame.draw.ellipse(
            screen, (200, 255, 255), (self.x + self.width // 2 - 6, self.y + 9, 12, 6)
        )
        pygame.draw.polygon(
            screen,
            (30, 60, 180),
            [
                (self.x, self.y + 12),
                (self.x - 12, self.y + 15),
                (self.x + 12, self.y + self.height - 12),
            ],
        )
        pygame.draw.polygon(
            screen,
            (30, 60, 180),
            [
                (self.x + self.width, self.y + 12),
                (self.x + self.width + 12, self.y + 15),
                (self.x + self.width - 12, self.y + self.height - 12),
            ],
        )

    def get_rect(self):
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------
class Laser:
    def __init__(self, x, y, direction, color, angle=0, damage=None):
        self.x = x
        self.y = y
        self.width = 5
        self.height = 24
        self.speed = 14
        self.direction = direction
        self.color = color
        self.angle = angle
        self.damage = damage if damage is not None else (26 if direction == -1 else 18)
        self.trail = []
        self.crit = False

    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.y += self.speed * self.direction
        self.x += math.sin(math.radians(self.angle)) * 4

    def draw(self, screen):
        for index, position in enumerate(self.trail):
            alpha = int(200 * (index / max(1, len(self.trail))))
            trail_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.color, alpha), (2, 2), 2)
            screen.blit(trail_surface, (int(position[0] - 2), int(position[1] - 2)))

        pygame.draw.rect(
            screen,
            self.color,
            (self.x - 2, self.y, self.width, self.height),
            border_radius=2,
        )
        if self.direction == -1:
            glow = pygame.Surface((self.width + 10, self.height + 4), pygame.SRCALPHA)
            pygame.draw.rect(
                glow,
                (*WHITE, 40),
                (3, 2, self.width + 4, self.height),
                border_radius=2,
            )
            screen.blit(glow, (self.x - 5, self.y - 2))
        else:
            for index in range(2):
                pygame.draw.circle(
                    screen,
                    (255, 100, 100),
                    (int(self.x + (index - 0.5) * 3), int(self.y + self.height + index * 2)),
                    2,
                )

    def get_rect(self):
        return pygame.Rect(self.x - 2, self.y, self.width, self.height)

    def is_off_screen(self):
        return (
            self.y < -80
            or self.y > HEIGHT + 80
            or self.x < -60
            or self.x > WIDTH + 60
        )


# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
class Enemy:
    def __init__(self, round_number, difficulty="pilot"):
        data = BOSS_DATA[(round_number - 1) % len(BOSS_DATA)]
        profile = DIFFICULTIES.get(difficulty, DIFFICULTIES["pilot"])
        self.difficulty = difficulty
        self.damage_scale = profile["boss_damage"]
        self.round_number = round_number
        self.name = data["name"]
        self.color = data["color"]
        self.accent = data["accent"]
        self.width = data["width"]
        self.height = data["height"]
        self.speed = data["speed"]
        self.x = random.randint(40, WIDTH - self.width - 40)
        self.y = 55
        self.hp = int((850 + round_number * 300) * profile["boss_hp"])
        self.max_hp = self.hp
        self.last_shot = 0
        base_delay = max(400, 1050 - round_number * 70)
        self.shoot_delay = max(280, int(base_delay * profile["boss_delay"]))
        self.move_direction = random.choice([-1, 1])
        self.move_timer = 0
        self.pattern_timer = random.randint(0, 120)
        self.flash = 0

    @property
    def health_ratio(self):
        return 0.0 if self.max_hp <= 0 else max(0.0, self.hp / self.max_hp)

    def move(self):
        self.move_timer += 1
        self.pattern_timer += 1
        aggression = 1.0 + (1.0 - self.health_ratio) * 0.45
        speed = self.speed * aggression

        self.x += math.sin(self.pattern_timer * 0.024) * (2.0 + self.round_number * 0.3)
        self.x += self.move_direction * speed * 0.35
        if self.x < 20:
            self.x = 20
            self.move_direction = 1
        elif self.x > WIDTH - self.width - 20:
            self.x = WIDTH - self.width - 20
            self.move_direction = -1

        hover = 55 + math.sin(self.pattern_timer * 0.025) * 12
        self.y += (hover - self.y) * 0.05
        if self.flash > 0:
            self.flash -= 1

    def _aim_angle(self, target_x, target_y):
        if target_x is None:
            return 0
        center_x = self.x + self.width // 2
        bottom = self.y + self.height
        dy = max(60, (target_y if target_y is not None else HEIGHT - 200) - bottom)
        angle = math.degrees(math.atan2(target_x - center_x, dy)) * 0.55
        return clamp(angle, -28, 28)

    def shoot(self, target_x=None, target_y=None):
        current_time = pygame.time.get_ticks()
        delay = self.shoot_delay
        if self.health_ratio < 0.35:
            delay = int(delay * 0.68)
        if current_time - self.last_shot <= delay:
            return []

        self.last_shot = current_time
        lasers = []
        center_x = self.x + self.width // 2
        bottom = self.y + self.height
        damage = int((12 + self.round_number * 2) * self.damage_scale)
        aimed = self._aim_angle(target_x, target_y)
        round_number = self.round_number

        if round_number == 1:
            lasers.append(Laser(center_x, bottom, 1, RED, damage=damage))
            if self.health_ratio < 0.65:
                lasers.append(Laser(center_x - 20, bottom, 1, ORANGE, angle=-10, damage=damage))
                lasers.append(Laser(center_x + 20, bottom, 1, ORANGE, angle=10, damage=damage))
        elif round_number == 2:
            for angle in (-16, 0, 16):
                lasers.append(Laser(center_x, bottom, 1, RED, angle=angle, damage=damage))
            if self.health_ratio < 0.5:
                lasers.append(Laser(center_x, bottom, 1, ORANGE, angle=aimed, damage=damage))
        elif round_number == 3:
            for angle in (-22, -11, 0, 11, 22):
                lasers.append(Laser(center_x, bottom, 1, RED, angle=angle, damage=damage))
            lasers.append(Laser(center_x, bottom, 1, PURPLE, angle=aimed, damage=damage))
        elif round_number == 4:
            sweep = math.sin(self.pattern_timer * 0.12) * 12
            for angle in (-18, -6, 6, 18):
                lasers.append(
                    Laser(center_x, bottom, 1, RED, angle=angle + sweep, damage=damage)
                )
            lasers.append(Laser(center_x, bottom, 1, ORANGE, angle=aimed, damage=damage))
        elif round_number == 5:
            for angle in (-24, -12, 0, 12, 24):
                lasers.append(Laser(center_x, bottom, 1, RED, angle=angle, damage=damage))
            lasers.append(Laser(center_x - 28, bottom, 1, PURPLE, angle=aimed - 8, damage=damage))
            lasers.append(Laser(center_x + 28, bottom, 1, PURPLE, angle=aimed + 8, damage=damage))
        elif round_number == 6:
            for index in range(4):
                angle = math.sin(self.pattern_timer * 0.09 + index * 1.7) * 26
                lasers.append(Laser(center_x, bottom, 1, RED, angle=angle, damage=damage))
            lasers.append(Laser(center_x, bottom, 1, PURPLE, angle=aimed, damage=damage))
        else:
            for angle in (-24, -12, 0, 12, 24):
                lasers.append(Laser(center_x, bottom, 1, ORANGE, angle=angle, damage=damage))
            lasers.append(Laser(center_x - 30, bottom, 1, RED, angle=aimed - 10, damage=damage))
            lasers.append(Laser(center_x + 30, bottom, 1, RED, angle=aimed + 10, damage=damage))
            lasers.append(Laser(center_x, bottom, 1, MAGENTA, angle=aimed, damage=damage))

        return lasers

    def take_damage(self, damage):
        self.hp -= max(0, damage)
        if self.hp < 0:
            self.hp = 0
        self.flash = 5
        return self.hp <= 0

    def draw(self, screen):
        body = WHITE if self.flash > 0 else self.color
        center_x = self.x + self.width // 2
        top = self.y
        bottom = self.y + self.height
        width = self.width
        height = self.height

        pygame.draw.polygon(
            screen,
            body,
            [
                (center_x, bottom),
                (self.x, top + height * 0.14),
                (self.x + width * 0.22, top),
                (center_x, top + height * 0.28),
                (self.x + width * 0.78, top),
                (self.x + width, top + height * 0.14),
            ],
        )
        pygame.draw.polygon(
            screen,
            (max(20, self.color[0] // 2), max(20, self.color[1] // 2), max(20, self.color[2] // 2)),
            [
                (self.x, top + height * 0.18),
                (self.x - 16, top + height * 0.24),
                (self.x + width * 0.2, bottom - height * 0.16),
            ],
        )
        pygame.draw.polygon(
            screen,
            (max(20, self.color[0] // 2), max(20, self.color[1] // 2), max(20, self.color[2] // 2)),
            [
                (self.x + width, top + height * 0.18),
                (self.x + width + 16, top + height * 0.24),
                (self.x + width * 0.8, bottom - height * 0.16),
            ],
        )
        pygame.draw.ellipse(
            screen,
            self.accent,
            (center_x - 12, bottom - height * 0.3, 24, height * 0.2),
        )
        pygame.draw.ellipse(
            screen,
            WHITE,
            (center_x - 6, bottom - height * 0.27, 12, height * 0.1),
        )

        eye_y = top + height * 0.23
        pygame.draw.circle(screen, self.accent, (center_x - 10, int(eye_y)), 5)
        pygame.draw.circle(screen, self.accent, (center_x + 10, int(eye_y)), 5)
        pygame.draw.circle(screen, WHITE, (center_x - 10, int(eye_y)), 2)
        pygame.draw.circle(screen, WHITE, (center_x + 10, int(eye_y)), 2)

        if self.round_number >= 4:
            pygame.draw.line(
                screen,
                self.accent,
                (center_x - width * 0.24, top + height * 0.5),
                (center_x + width * 0.24, top + height * 0.5),
                3,
            )
        if (pygame.time.get_ticks() // 160) % 2 == 0:
            pygame.draw.circle(screen, RED, (int(self.x + 12), int(top + height * 0.55)), 4)
            pygame.draw.circle(
                screen, RED, (int(self.x + width - 12), int(top + height * 0.55)), 4
            )

    def get_rect(self):
        return pygame.Rect(self.x + 6, self.y + 6, self.width - 12, self.height - 16)


class Minion:
    """Small swarm fighter that escorts the boss."""

    def __init__(self, round_number, difficulty="pilot"):
        profile = DIFFICULTIES.get(difficulty, DIFFICULTIES["pilot"])
        self.round_number = round_number
        self.damage_scale = profile["boss_damage"]
        self.width = 34
        self.height = 28
        self.x = random.randint(30, WIDTH - self.width - 30)
        self.y = -self.height
        self.hp = 24 + round_number * 9
        self.max_hp = self.hp
        self.speed = random.uniform(1.5, 2.4) + round_number * 0.1
        self.drift = random.uniform(-1.3, 1.3)
        self.timer = random.randint(0, 180)
        self.shoot_delay = random.randint(1100, 2000)
        self.last_shot = pygame.time.get_ticks() - random.randint(0, 1200)
        self.flash = 0
        self.color = random.choice(
            [(255, 120, 90), (120, 220, 255), (230, 120, 255)]
        )

    def move(self):
        self.timer += 1
        self.y += self.speed
        self.x += math.sin(self.timer * 0.05) * 0.9 + self.drift * 0.2
        self.x = max(
            8, min(WIDTH - self.width - 8, self.x)
        )
        if self.flash > 0:
            self.flash -= 1

    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot <= self.shoot_delay:
            return []
        self.last_shot = current_time
        damage = max(6, int((7 + self.round_number) * self.damage_scale))
        return [
            Laser(
                self.x + self.width // 2,
                self.y + self.height,
                1,
                self.color,
                damage=damage,
            )
        ]

    def take_damage(self, damage):
        self.hp -= max(0, damage)
        if self.hp < 0:
            self.hp = 0
        self.flash = 4
        return self.hp <= 0

    def draw(self, screen):
        body = WHITE if self.flash > 0 else self.color
        center_x = self.x + self.width // 2
        top = self.y
        bottom = self.y + self.height
        pygame.draw.polygon(
            screen,
            body,
            [
                (center_x, bottom),
                (self.x, top + self.height * 0.25),
                (center_x, top),
                (self.x + self.width, top + self.height * 0.25),
            ],
        )
        pygame.draw.polygon(
            screen,
            tuple(max(20, channel // 2) for channel in self.color),
            [
                (self.x, top + self.height * 0.34),
                (self.x - 8, top + self.height * 0.5),
                (self.x + self.width * 0.3, bottom - 4),
            ],
        )
        pygame.draw.polygon(
            screen,
            tuple(max(20, channel // 2) for channel in self.color),
            [
                (self.x + self.width, top + self.height * 0.34),
                (self.x + self.width + 8, top + self.height * 0.5),
                (self.x + self.width * 0.7, bottom - 4),
            ],
        )
        pygame.draw.circle(
            screen, WHITE, (center_x, int(top + self.height * 0.38)), 3
        )
        if (self.timer // 4) % 2 == 0:
            pygame.draw.circle(
                screen, ORANGE, (center_x, int(bottom + 2)), 3
            )

    def get_rect(self):
        return pygame.Rect(
            self.x + 5, self.y + 4, self.width - 10, self.height - 8
        )

    def is_off_screen(self):
        return self.y > HEIGHT + 50


class Asteroid:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(28, 46)
        self.width = self.size
        self.height = self.size
        self.hp = 80
        self.max_hp = 80
        self.speed = random.uniform(1.8, 3.2)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2.2, 2.2)
        self.radii = [self.size // 2 + random.randint(-4, 4) for _ in range(10)]
        self.craters = [
            (
                random.uniform(0, math.tau),
                random.uniform(0.15, 0.55) * self.size,
                random.randint(2, 4),
            )
            for _ in range(3)
        ]
        self.base_color = random.choice([(95, 95, 110), (100, 90, 85), (85, 100, 105)])

    def move(self):
        self.y += self.speed
        self.rotation += self.rot_speed

    def draw(self, screen):
        center_x = self.x + self.size // 2
        center_y = self.y + self.size // 2
        points = []
        for index in range(10):
            angle = math.radians(self.rotation + index * 36)
            radius = self.radii[index]
            points.append(
                (
                    center_x + math.cos(angle) * radius,
                    center_y + math.sin(angle) * radius,
                )
            )
        pygame.draw.polygon(screen, self.base_color, points)
        pygame.draw.polygon(
            screen,
            tuple(max(0, channel - 35) for channel in self.base_color),
            points,
            2,
        )
        for angle, distance, radius in self.craters:
            crater_angle = math.radians(self.rotation * 0.5) + angle
            pygame.draw.circle(
                screen,
                tuple(max(0, channel - 45) for channel in self.base_color),
                (
                    int(center_x + math.cos(crater_angle) * distance),
                    int(center_y + math.sin(crater_angle) * distance),
                ),
                radius,
            )

    def take_damage(self, damage):
        self.hp -= max(0, damage)
        if self.hp < 0:
            self.hp = 0
        return self.hp <= 0

    def get_rect(self):
        return pygame.Rect(self.x + 3, self.y + 3, self.width - 6, self.height - 6)

    def is_off_screen(self):
        return self.y > HEIGHT + 70


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class EnhancedGame:
    def __init__(self):
        self.config = config
        self.fullscreen = bool(self.config.settings.get("fullscreen", False))
        self.screen = self._create_screen()
        pygame.display.set_caption(f"{TITLE} - v{VERSION}")
        self._set_window_icon()
        self.clock = pygame.time.Clock()

        self.font_huge = pygame.font.Font(None, 84)
        self.font_large = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 24)
        self.micro_font = pygame.font.Font(None, 18)
        self.fonts = {
            "huge": self.font_huge,
            "large": self.font_large,
            "normal": self.font,
            "small": self.small_font,
            "tiny": self.tiny_font,
            "micro": self.micro_font,
        }

        self.world = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.audio = SoundManager(self.config.settings)
        self.achievements_unlocked = set(
            self.config.progression.get("achievements", [])
        )

        self.stars = [Star(index % 3) for index in range(170)]
        self.nebulas = [Nebula() for _ in range(3)]
        self.shake_offset = (0, 0)
        self.start_button = pygame.Rect(WIDTH // 2 - 160, 700, 320, 72)
        self.difficulty_buttons = {}
        self.pause_buttons = {}
        self.end_buttons = {}
        self.upgrade_buttons = {}
        self.show_achievements = False
        self.show_stats = False

        self.reset_run()
        self.game_state = "landing"
        print(f"Dragon Roaster v{VERSION} initialized!")

    @staticmethod
    def _create_screen(fullscreen=False):
        try:
            if fullscreen and hasattr(pygame, "SCALED"):
                return pygame.display.set_mode(
                    (WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED
                )
            if fullscreen:
                return pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        except pygame.error:
            pass
        return pygame.display.set_mode((WIDTH, HEIGHT))

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.screen = self._create_screen(self.fullscreen)
        self.world = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.config.settings["fullscreen"] = self.fullscreen
        self.config.save()
        self.add_toast(
            "FULLSCREEN ON" if self.fullscreen else "FULLSCREEN OFF",
            CYAN,
            90,
        )

    @property
    def difficulty_key(self):
        key = self.config.settings.get("difficulty", "pilot")
        return key if key in DIFFICULTIES else "pilot"

    @property
    def difficulty(self):
        return DIFFICULTIES[self.difficulty_key]

    @property
    def particle_scale(self):
        quality = self.config.settings.get("particle_quality", "high")
        return PARTICLE_QUALITY_SCALE.get(quality, 1.0)


    @staticmethod
    def _set_window_icon():
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.polygon(
            icon, (50, 100, 255), [(16, 1), (2, 29), (16, 23), (30, 29)]
        )
        pygame.draw.polygon(
            icon, (30, 60, 180), [(2, 12), (0, 20), (14, 30)]
        )
        pygame.draw.polygon(
            icon, (30, 60, 180), [(30, 12), (32, 20), (18, 30)]
        )
        pygame.draw.circle(icon, CYAN, (16, 13), 4)
        pygame.display.set_icon(icon)

    # -- lifecycle ----------------------------------------------------------
    def reset_run(self):
        self.spaceship = Spaceship(WIDTH // 2 - 32, HEIGHT - 190)
        self.spaceship.lives = self.difficulty["lives"]
        self.player_lasers = []
        self.enemy_lasers = []
        self.asteroids = []
        self.minions = []
        self.powerups = []
        self.particles = []
        self.floating_texts = []
        self.toasts = []

        self.round = 1
        self.enemy = Enemy(self.round, self.difficulty_key)
        self.score = 0
        self.score_scale = self.difficulty["score"]
        self.combo = 0
        self.combo_timer = 0
        self.max_combo = 0
        self.asteroid_spawn_timer = 70
        self.powerup_spawn_timer = 240
        self.minion_spawn_timer = 150
        self.screen_shake = 0
        self.shake_offset = (0, 0)
        self.run_powerups = 0
        self.run_lasers = 0
        self.run_minions = 0
        self.run_dashes = 0
        self.lives_lost = 0
        self.new_high_score = False
        self.game_over_reason = ""
        self.banner_title = ""
        self.banner_subtitle = ""
        self.banner_timer = 0
        self.banner_color = GOLD
        self.end_buttons = {}
        self.upgrade_buttons = {}
        self.upgrade_choices = []
        self.upgrades = {}
        self.run_upgrades = 0
        self.show_achievements = False
        self.show_stats = False

    def reset_game(self):
        self.reset_run()
        self.game_state = "landing"

    def start_game(self):
        self.reset_run()
        self.game_state = "playing"
        self.show_banner("WAVE 1", self.enemy.name)
        self.audio.play("wave")

    def return_to_menu(self):
        self.config.save()
        self.reset_run()
        self.game_state = "landing"
        self.audio.play("click")

    def set_difficulty(self, key):
        if key not in DIFFICULTIES:
            return False
        self.config.settings["difficulty"] = key
        self.config.save()
        self.spaceship.lives = self.difficulty["lives"]
        self.enemy = Enemy(self.round, self.difficulty_key)
        self.score_scale = self.difficulty["score"]
        self.audio.play("click")
        self.add_toast(f"DIFFICULTY: {self.difficulty['name']}", CYAN, 90)
        return True

    def cycle_particle_quality(self):
        order = ["low", "medium", "high"]
        current = self.config.settings.get("particle_quality", "high")
        index = order.index(current) if current in order else len(order) - 1
        quality = order[(index + 1) % len(order)]
        self.config.settings["particle_quality"] = quality
        self.config.save()
        self.audio.play("click")
        self.add_toast(f"PARTICLES: {quality.upper()}", CYAN, 90)

    def toggle_mute(self):
        muted = self.audio.toggle_mute()
        self.config.settings["muted"] = muted
        self.config.save()
        self.add_toast("SOUND OFF" if muted else "SOUND ON", CYAN, 100)
        return muted

    # -- feedback helpers ---------------------------------------------------
    def add_particles(self, x, y, color, count=20, shape="circle", speed=8):
        count = max(1, int(count * self.particle_scale))
        for _ in range(count):
            self.particles.append(
                Particle(
                    x,
                    y,
                    color,
                    vx=random.uniform(-speed, speed),
                    vy=random.uniform(-speed, speed),
                    shape=shape,
                )
            )

    def add_screen_shake(self, intensity=12):
        self.screen_shake = max(self.screen_shake, intensity)

    def show_banner(self, title, subtitle="", duration=125, color=GOLD):
        self.banner_title = title
        self.banner_subtitle = subtitle
        self.banner_timer = duration
        self.banner_color = color

    def add_toast(self, text, color=GOLD, duration=180):
        self.toasts.append({"text": text, "color": color, "timer": duration})
        self.toasts = self.toasts[-4:]

    def add_floating_text(self, x, y, text, color=GOLD, size="tiny"):
        self.floating_texts.append(FloatingText(x, y, text, color, size=size))

    @property
    def score_multiplier(self):
        return 1 + min(5, self.combo // 5)

    def register_hit(self):
        previous = self.combo
        self.combo += 1
        self.combo_timer = 90
        self.max_combo = max(self.max_combo, self.combo)
        best = self.config.progression.get("best_combo", 0)
        if self.combo > best:
            self.config.progression["best_combo"] = self.combo
        if self.combo in COMBO_MILESTONES and previous < self.combo:
            self.add_toast(f"COMBO x{self.combo}!", ORANGE, 90)
            self.audio.play("powerup")

    def add_score(self, amount, x=None, y=None, color=GOLD, show_text=True):
        gained = int(amount * self.score_multiplier * self.score_scale)
        self.score += gained
        if show_text and x is not None:
            self.add_floating_text(x, y if y is not None else 0, f"+{gained}", color)

    # -- spawning -----------------------------------------------------------
    def spawn_asteroid(self):
        if self.asteroid_spawn_timer > 0:
            self.asteroid_spawn_timer -= 1
            return
        x = random.randint(20, WIDTH - 80)
        self.asteroids.append(Asteroid(x, -70))
        base = max(42, 140 - self.round * 10)
        self.asteroid_spawn_timer = random.randint(base // 2, base)

    def spawn_powerup(self):
        if self.powerup_spawn_timer > 0:
            self.powerup_spawn_timer -= 1
            return
        x = random.randint(35, WIDTH - 75)
        self.powerups.append(PowerUp(x, -40))
        self.powerup_spawn_timer = random.randint(420, 700)

    def spawn_minion(self):
        if self.minion_spawn_timer > 0:
            self.minion_spawn_timer -= 1
            return
        if len(self.minions) < 7:
            self.minions.append(Minion(self.round, self.difficulty_key))
        base = max(95, 250 - self.round * 20)
        self.minion_spawn_timer = random.randint(int(base * 0.7), base)

    # -- update -------------------------------------------------------------
    def update(self):
        dt = min(self.clock.get_time() / 1000.0, 0.05)

        for star in self.stars:
            star.update(dt)
        for nebula in self.nebulas:
            nebula.update(dt)

        if self.screen_shake > 0:
            self.shake_offset = (
                random.randint(-self.screen_shake, self.screen_shake),
                random.randint(-self.screen_shake, self.screen_shake),
            )
            self.screen_shake -= 1
        else:
            self.shake_offset = (0, 0)

        for toast in self.toasts[:]:
            toast["timer"] -= 1
            if toast["timer"] <= 0:
                self.toasts.remove(toast)

        if self.game_state != "playing":
            return

        if self.banner_timer > 0:
            self.banner_timer -= 1

        keys = pygame.key.get_pressed()
        self.spaceship.move(keys, dt)
        self.spaceship.update()
        if self.spaceship.dash_time > 0:
            self.add_particles(
                self.spaceship.x + self.spaceship.width // 2,
                self.spaceship.y + self.spaceship.height // 2,
                CYAN,
                2,
                speed=3,
            )
        if keys[pygame.K_SPACE]:
            self.fire()

        if self.combo_timer > 0:
            self.combo_timer -= 1
        elif self.combo:
            self.combo = 0

        self.spawn_asteroid()
        self.spawn_powerup()
        self.spawn_minion()
        self.update_projectiles()
        self.update_pickups()
        self.update_effects()

        if self.enemy and self.enemy.hp > 0:
            self.enemy.move()
            target_x = self.spaceship.x + self.spaceship.width // 2
            target_y = self.spaceship.y + self.spaceship.height // 2
            enemy_lasers = self.enemy.shoot(target_x, target_y)
            if enemy_lasers:
                self.enemy_lasers.extend(enemy_lasers)
                self.audio.play("enemy_shoot")

        for minion in self.minions[:]:
            minion.move()
            shots = minion.shoot()
            if shots:
                self.enemy_lasers.extend(shots)
        self.minions = [
            minion for minion in self.minions if not minion.is_off_screen()
        ]

        self.handle_collisions()

        if self.spaceship.hp <= 0:
            self.handle_player_death()
            if self.game_state != "playing":
                return

        if self.enemy and self.enemy.hp <= 0:
            self.on_boss_defeated()
            if self.game_state != "playing":
                return

        self.check_achievements()

    def update_projectiles(self):
        for laser in self.player_lasers:
            laser.move()
        self.player_lasers = [
            laser for laser in self.player_lasers if not laser.is_off_screen()
        ]

        for laser in self.enemy_lasers:
            laser.move()
        self.enemy_lasers = [
            laser for laser in self.enemy_lasers if not laser.is_off_screen()
        ]

    def update_pickups(self):
        for asteroid in self.asteroids:
            asteroid.move()
        self.asteroids = [
            asteroid for asteroid in self.asteroids if not asteroid.is_off_screen()
        ]

        for powerup in self.powerups:
            powerup.update()
        self.powerups = [
            powerup for powerup in self.powerups if powerup.y < HEIGHT + 60
        ]

    def update_effects(self):
        for particle in self.particles:
            particle.update()
        self.particles = [
            particle for particle in self.particles if particle.life > 0
        ]

        for text in self.floating_texts:
            text.update()
        self.floating_texts = [
            text for text in self.floating_texts if text.life > 0
        ]

    def fire(self):
        lasers = self.spaceship.shoot()
        if not lasers:
            return
        self.player_lasers.extend(lasers)
        self.run_lasers += len(lasers)
        self.config.progression["total_lasers_fired"] = (
            self.config.progression.get("total_lasers_fired", 0) + len(lasers)
        )
        self.audio.play("shoot")

    # -- combat -------------------------------------------------------------
    def handle_collisions(self):
        ship_rect = self.spaceship.get_rect()

        for laser in self.player_lasers[:]:
            if (
                self.enemy
                and self.enemy.hp > 0
                and laser.get_rect().colliderect(self.enemy.get_rect())
            ):
                self.enemy.take_damage(laser.damage)
                if laser.crit:
                    self.add_particles(laser.x, laser.y, GOLD, 16)
                    self.add_floating_text(laser.x, laser.y - 8, "CRIT!", GOLD)
                else:
                    self.add_particles(laser.x, laser.y, CYAN, 8)
                self.register_hit()
                self.score += int(2 * self.score_multiplier * self.score_scale)
                self.audio.play("hit")
                try:
                    self.player_lasers.remove(laser)
                except ValueError:
                    pass
                continue

            hit_minion = None
            for minion in self.minions[:]:
                if laser.get_rect().colliderect(minion.get_rect()):
                    hit_minion = minion
                    break
            if hit_minion is not None:
                hit_minion.take_damage(laser.damage)
                self.add_particles(laser.x, laser.y, hit_minion.color, 7)
                if hit_minion.hp <= 0:
                    self.on_minion_defeated(hit_minion)
                try:
                    self.player_lasers.remove(laser)
                except ValueError:
                    pass
                continue

            for asteroid in self.asteroids[:]:
                if laser.get_rect().colliderect(asteroid.get_rect()):
                    asteroid.take_damage(laser.damage)
                    self.add_particles(laser.x, laser.y, (150, 150, 150), 6)
                    if asteroid.hp <= 0:
                        self.asteroids.remove(asteroid)
                        self.register_hit()
                        self.config.progression["total_enemies_defeated"] = (
                            self.config.progression.get("total_enemies_defeated", 0) + 1
                        )
                        self.add_score(
                            40,
                            asteroid.x + asteroid.width // 2,
                            asteroid.y + asteroid.height // 2,
                            (180, 180, 180),
                        )
                        self.add_particles(
                            asteroid.x + asteroid.width // 2,
                            asteroid.y + asteroid.height // 2,
                            (120, 120, 120),
                            18,
                        )
                        self.audio.play("explosion")
                    try:
                        self.player_lasers.remove(laser)
                    except ValueError:
                        pass
                    break

        for laser in self.enemy_lasers[:]:
            if laser.get_rect().colliderect(ship_rect):
                if self.spaceship.invulnerable == 0 and self.spaceship.take_damage(
                    laser.damage
                ):
                    self.add_particles(laser.x, laser.y, RED, 14)
                    self.add_screen_shake(8)
                    self.combo = 0
                    self.combo_timer = 0
                    self.audio.play("hit")
                try:
                    self.enemy_lasers.remove(laser)
                except ValueError:
                    pass

        for asteroid in self.asteroids[:]:
            if ship_rect.colliderect(asteroid.get_rect()):
                if self.spaceship.invulnerable == 0 and self.spaceship.take_damage(
                    18 + self.round * 2
                ):
                    self.add_particles(
                        asteroid.x + asteroid.width // 2,
                        asteroid.y + asteroid.height // 2,
                        ORANGE,
                        20,
                    )
                    self.add_screen_shake(11)
                    self.combo = 0
                    self.combo_timer = 0
                    self.audio.play("hit")
                try:
                    self.asteroids.remove(asteroid)
                except ValueError:
                    pass

        for minion in self.minions[:]:
            if ship_rect.colliderect(minion.get_rect()):
                if self.spaceship.invulnerable == 0 and self.spaceship.take_damage(
                    int((14 + self.round * 2) * self.difficulty["boss_damage"])
                ):
                    self.add_particles(
                        minion.x + minion.width // 2,
                        minion.y + minion.height // 2,
                        minion.color,
                        18,
                    )
                    self.add_screen_shake(10)
                    self.combo = 0
                    self.combo_timer = 0
                    self.audio.play("hit")
                try:
                    self.minions.remove(minion)
                except ValueError:
                    pass

        for powerup in self.powerups[:]:
            if ship_rect.colliderect(powerup.get_rect()):
                self.apply_powerup(powerup.type)
                self.add_particles(powerup.x + 16, powerup.y + 16, WHITE, 10)
                try:
                    self.powerups.remove(powerup)
                except ValueError:
                    pass

    def on_minion_defeated(self, minion):
        if minion in self.minions:
            self.minions.remove(minion)
        center_x = minion.x + minion.width // 2
        center_y = minion.y + minion.height // 2
        self.run_minions += 1
        self.config.progression["total_minions_defeated"] = (
            self.config.progression.get("total_minions_defeated", 0) + 1
        )
        self.register_hit()
        self.add_score(65 + self.round * 6, center_x, center_y, minion.color)
        self.add_particles(center_x, center_y, minion.color, 16)
        self.audio.play("minion_death")

    def apply_powerup(self, power_type):
        ship = self.spaceship
        if power_type == "health":
            ship.hp = min(ship.max_hp, ship.hp + 40)
        elif power_type == "shield":
            ship.shield = min(ship.shield_max, ship.shield + 60)
        elif power_type == "rapid":
            ship.rapid_fire = 700
        elif power_type == "spread":
            ship.spread_shot = 700
        elif power_type == "overdrive":
            ship.overdrive = 600
        elif power_type == "bomb":
            self.enemy_lasers.clear()
            if self.enemy and self.enemy.hp > 0:
                self.enemy.take_damage(150)
            for minion in self.minions[:]:
                minion.take_damage(150)
                if minion.hp <= 0:
                    self.on_minion_defeated(minion)
            for _ in range(70):
                self.add_particles(
                    random.randint(0, WIDTH),
                    random.randint(0, HEIGHT),
                    random.choice([YELLOW, ORANGE, RED]),
                    1,
                    speed=5,
                )
            self.add_screen_shake(26)
        elif power_type == "life":
            ship.lives += 1

        self.run_powerups += 1
        self.config.progression["total_powerups_collected"] = (
            self.config.progression.get("total_powerups_collected", 0) + 1
        )
        label = POWERUP_LABELS.get(power_type, power_type.upper())
        self.add_floating_text(
            ship.x + ship.width // 2,
            ship.y - 14,
            label,
            POWERUP_COLORS.get(power_type, WHITE),
        )
        self.audio.play("powerup")

    def handle_player_death(self):
        self.spaceship.lives = max(0, self.spaceship.lives - 1)
        self.lives_lost += 1
        self.add_particles(
            self.spaceship.x + self.spaceship.width // 2,
            self.spaceship.y + self.spaceship.height // 2,
            ORANGE,
            55,
        )
        self.add_screen_shake(26)
        self.combo = 0
        self.combo_timer = 0

        if self.spaceship.lives <= 0:
            self.end_run(False, "Hull destroyed")
            return

        self.spaceship.respawn()
        self.enemy_lasers.clear()
        self.show_banner(
            "LIFE LOST",
            f"{self.spaceship.lives} lives remaining",
            110,
            RED,
        )
        self.audio.play("player_death")

    def on_boss_defeated(self):
        center_x = self.enemy.x + self.enemy.width // 2
        center_y = self.enemy.y + self.enemy.height // 2
        self.config.progression["bosses_defeated"] = (
            self.config.progression.get("bosses_defeated", 0) + 1
        )
        self.config.progression["total_enemies_defeated"] = (
            self.config.progression.get("total_enemies_defeated", 0) + 1
        )
        self.register_hit()
        self.add_score(250 * self.round, center_x, center_y, ORANGE)
        self.add_particles(center_x, center_y, ORANGE, 65, speed=10)
        self.add_particles(center_x, center_y, YELLOW, 30, speed=7)
        self.add_screen_shake(24)
        self.audio.play("boss_death")
        self.check_achievements()

        if self.round >= MAX_ROUNDS:
            self.end_run(True, "All bosses defeated")
        else:
            self.begin_upgrade()

    def generate_upgrades(self):
        available = [
            upgrade
            for upgrade in UPGRADE_POOL
            if self.upgrades.get(upgrade["key"], 0) < upgrade["max_level"]
        ]
        random.shuffle(available)
        choices = available[:3]
        if not choices:
            choices = [
                {
                    "key": "repair",
                    "name": "FIELD REPAIR",
                    "desc": "Restore 40 HP",
                    "color": GREEN,
                    "max_level": 99,
                }
            ]
        return choices

    def begin_upgrade(self):
        self.game_state = "upgrade"
        self.upgrade_choices = self.generate_upgrades()
        self.upgrade_buttons = {}
        self.enemy_lasers.clear()
        self.audio.play("upgrade")

    def choose_upgrade(self, index):
        if self.game_state != "upgrade":
            return False
        if not 0 <= index < len(self.upgrade_choices):
            return False

        choice = self.upgrade_choices[index]
        key = choice["key"]
        ship = self.spaceship
        self.upgrades[key] = self.upgrades.get(key, 0) + 1

        if key == "damage":
            ship.damage_multiplier += 0.15
        elif key == "firerate":
            ship.shoot_delay = max(60, int(ship.shoot_delay * 0.88))
        elif key == "speed":
            ship.speed *= 1.10
        elif key == "hull":
            ship.max_hp += 25
            ship.hp = min(ship.max_hp, ship.hp + 25)
        elif key == "shield":
            ship.shield_max += 40
            ship.shield = min(ship.shield_max, ship.shield + 40)
        elif key == "crit":
            ship.crit_chance = min(0.75, ship.crit_chance + 0.08)
        elif key == "dash":
            ship.dash_cooldown_max = max(
                42, int(ship.dash_cooldown_max * 0.80)
            )
            ship.dash_cooldown = min(ship.dash_cooldown, ship.dash_cooldown_max)
        elif key == "life":
            ship.lives += 1
        elif key == "repair":
            ship.hp = min(ship.max_hp, ship.hp + 40)

        self.run_upgrades += 1
        self.add_toast(f"UPGRADE: {choice['name']}", choice["color"], 140)
        self.add_floating_text(
            ship.x + ship.width // 2,
            ship.y - 16,
            choice["name"],
            choice["color"],
        )
        self.audio.play("upgrade")
        self.check_achievements()
        self.upgrade_choices = []
        self.upgrade_buttons = {}
        self.game_state = "playing"
        self.next_round()
        return True

    def next_round(self):
        self.round += 1
        self.enemy = Enemy(self.round, self.difficulty_key)
        self.player_lasers.clear()
        self.enemy_lasers.clear()
        self.asteroids.clear()
        self.minions.clear()
        self.powerups.clear()
        self.spaceship.hp = min(self.spaceship.max_hp, self.spaceship.hp + 22)
        self.spaceship.shield = min(
            self.spaceship.shield_max, self.spaceship.shield + 15
        )
        self.config.progression["best_wave"] = max(
            self.config.progression.get("best_wave", 1), self.round
        )
        if self.round % 2 == 0:
            for _ in range(2):
                self.powerups.append(
                    PowerUp(
                        random.randint(50, WIDTH - 80),
                        -40,
                        random.choice(["health", "shield", "overdrive"]),
                    )
                )
        self.game_state = "playing"
        self.show_banner(f"WAVE {self.round}", self.enemy.name)
        self.audio.play("wave")
        self.check_achievements()

    def end_run(self, victory, reason=""):
        if self.game_state in ("game_over", "victory"):
            return
        self.game_state = "victory" if victory else "game_over"
        self.game_over_reason = reason
        self.config.progression["games_played"] = (
            self.config.progression.get("games_played", 0) + 1
        )
        self.config.progression["best_wave"] = max(
            self.config.progression.get("best_wave", 1), self.round
        )
        if victory:
            self.config.progression["victories"] = (
                self.config.progression.get("victories", 0) + 1
            )
        if self.score > self.config.progression.get("high_score", 0):
            self.config.progression["high_score"] = self.score
            self.new_high_score = True
        self.check_achievements()
        self.config.save()
        self.audio.play("victory" if victory else "game_over")

    # -- achievements -------------------------------------------------------
    def check_achievements(self):
        progression = self.config.progression
        score_for_checks = max(self.score, progression.get("high_score", 0))
        combo_for_checks = max(
            self.combo, self.max_combo, progression.get("best_combo", 0)
        )

        conditions = {
            "first_blood": progression.get("bosses_defeated", 0) >= 1,
            "score_1000": score_for_checks >= 1000,
            "score_5000": score_for_checks >= 5000,
            "score_10000": score_for_checks >= 10000,
            "score_25000": score_for_checks >= 25000,
            "combo_10": combo_for_checks >= 10,
            "combo_25": combo_for_checks >= 25,
            "boss_hunter": progression.get("bosses_defeated", 0) >= 10,
            "swarm_breaker": progression.get("total_minions_defeated", 0) >= 50,
            "dash_master": progression.get("total_dashes", 0) >= 25,
            "fully_loaded": self.run_upgrades >= 5,
            "wave_3": self.round >= 3,
            "victory": self.game_state == "victory",
            "untouchable": self.game_state == "victory" and self.lives_lost == 0,
            "ace_victory": self.game_state == "victory"
            and self.difficulty_key == "ace",
            "collector": progression.get("total_powerups_collected", 0) >= 25,
            "sharpshooter": progression.get("total_lasers_fired", 0) >= 500,
        }

        unlocked_now = [
            key
            for key, condition in conditions.items()
            if condition and key not in self.achievements_unlocked
        ]
        if not unlocked_now:
            return

        for key in unlocked_now:
            self.achievements_unlocked.add(key)
            info = ACHIEVEMENTS.get(key, {"name": key})
            self.add_toast(f"ACHIEVEMENT: {info['name']}", GOLD, 220)
        progression["achievements"] = sorted(self.achievements_unlocked)
        self.audio.play("achievement")
        self.config.save()

    # -- drawing ------------------------------------------------------------
    def draw(self):
        self.screen.fill(BLACK)

        if self.game_state == "landing":
            self.draw_background(self.screen)
            self.draw_landing()
            if self.show_achievements:
                self.draw_achievements_overlay()
            elif self.show_stats:
                self.draw_stats_overlay()
        else:
            self.world.fill(BLACK)
            self.draw_background(self.world)
            self.draw_world(self.world)
            self.screen.blit(self.world, self.shake_offset)
            self.draw_hud()
            self.draw_banner()
            if self.game_state == "paused":
                self.draw_pause()
            elif self.game_state == "upgrade":
                self.draw_upgrade()
            elif self.game_state in ("game_over", "victory"):
                self.draw_end_screen()

        self.draw_toasts()
        pygame.display.flip()

    def draw_background(self, target):
        for nebula in self.nebulas:
            nebula.draw(target)
        for star in self.stars:
            star.draw(target)

    def draw_world(self, target):
        for powerup in self.powerups:
            powerup.draw(target)
        for asteroid in self.asteroids:
            asteroid.draw(target)
        for minion in self.minions:
            minion.draw(target)
        for laser in self.player_lasers:
            laser.draw(target)
        for laser in self.enemy_lasers:
            laser.draw(target)
        for particle in self.particles:
            particle.draw(target)
        for text in self.floating_texts:
            text.draw(target, self.fonts)
        if self.enemy and self.enemy.hp > 0:
            self.enemy.draw(target)
        if self.spaceship.hp > 0 or self.game_state == "victory":
            self.spaceship.draw(target)

    def _draw_button(self, rect, label, base_color, hover_color, text_color=BLACK):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = hover_color if hovered else base_color
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, rect, 3, border_radius=10)
        text = self.font.render(label, True, text_color)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw_landing(self):
        self.start_button = pygame.Rect(WIDTH // 2 - 160, 700, 320, 70)

        title_glow = self.font_huge.render("DRAGON ROASTER", True, ORANGE)
        self.screen.blit(
            title_glow, title_glow.get_rect(center=(WIDTH // 2 + 3, 89))
        )
        title = self.font_huge.render("DRAGON ROASTER", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 86)))

        subtitle = self.small_font.render(
            "SPACE BATTLE  •  SURVIVE 7 BOSS WAVES", True, CYAN
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 146)))

        stats_panel = pygame.Rect(90, 172, WIDTH - 180, 88)
        pygame.draw.rect(self.screen, (0, 0, 70), stats_panel, border_radius=9)
        pygame.draw.rect(self.screen, CYAN, stats_panel, 2, border_radius=9)
        high_score = self.config.progression.get("high_score", 0)
        high_text = self.font.render(f"HIGH SCORE  {high_score}", True, GOLD)
        self.screen.blit(high_text, high_text.get_rect(center=(WIDTH // 2, 199)))
        stats = self.micro_font.render(
            "BEST COMBO {}   •   BEST WAVE {}   •   ACHIEVEMENTS {}/{}".format(
                self.config.progression.get("best_combo", 0),
                self.config.progression.get("best_wave", 1),
                len(self.achievements_unlocked),
                len(ACHIEVEMENTS),
            ),
            True,
            LIGHT_BLUE,
        )
        self.screen.blit(stats, stats.get_rect(center=(WIDTH // 2, 235)))

        box = pygame.Rect(70, 276, WIDTH - 140, 300)
        pygame.draw.rect(self.screen, (0, 0, 80), box, border_radius=12)
        pygame.draw.rect(self.screen, CYAN, box, 3, border_radius=12)

        heading = self.small_font.render("MISSION BRIEFING", True, YELLOW)
        self.screen.blit(heading, heading.get_rect(center=(WIDTH // 2, 302)))

        lines = [
            ("WASD / Arrows - Move     SHIFT / X - Dash", WHITE),
            ("SPACE - Fire     P - Pause     F11 - Fullscreen", WHITE),
            ("M - Mute   [ ] - Volume   V - Particles", WHITE),
            ("A - Achievements   S - Stats   O - Quit", WHITE),
            ("", WHITE),
            ("Chain hits for COMBO multipliers. Clear a wave to", LIGHT_BLUE),
            ("choose one of three permanent run upgrades.", LIGHT_BLUE),
            ("", WHITE),
            ("POWER-UPS", GOLD),
            ("+HP  SHIELD  RAPID  SPREAD  BOMB  LIFE  OVERDRIVE", LIGHT_BLUE),
        ]

        y = 334
        for text, color in lines:
            if not text:
                y += 8
                continue
            font = self.micro_font if text not in ("POWER-UPS",) else self.tiny_font
            surface = font.render(text, True, color)
            self.screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))
            y += 24 if text == "POWER-UPS" else 20

        difficulty_heading = self.micro_font.render(
            "DIFFICULTY", True, LIGHT_BLUE
        )
        self.screen.blit(
            difficulty_heading,
            difficulty_heading.get_rect(center=(WIDTH // 2, 595)),
        )

        palette = {"cadet": GREEN, "pilot": CYAN, "ace": ORANGE}
        self.difficulty_buttons = {}
        button_x = WIDTH // 2 - (3 * 190 + 2 * 20) // 2
        for key, profile in DIFFICULTIES.items():
            rect = pygame.Rect(button_x, 612, 190, 46)
            self.difficulty_buttons[key] = rect
            active = key == self.difficulty_key
            color = palette.get(key, WHITE)
            pygame.draw.rect(
                self.screen,
                color if active else (18, 18, 34),
                rect,
                border_radius=8,
            )
            pygame.draw.rect(self.screen, color, rect, 3, border_radius=8)
            label = self.tiny_font.render(
                profile["name"], True, BLACK if active else color
            )
            self.screen.blit(label, label.get_rect(center=rect.center))
            button_x += 210

        description = self.micro_font.render(
            self.difficulty["description"], True, LIGHT_BLUE
        )
        self.screen.blit(
            description, description.get_rect(center=(WIDTH // 2, 675))
        )

        self._draw_button(self.start_button, "START MISSION", GREEN, (120, 255, 120))

        footer = self.tiny_font.render(
            "Press ENTER or click START   •   1-3 changes difficulty", True, WHITE
        )
        self.screen.blit(footer, footer.get_rect(center=(WIDTH // 2, 800)))

        sound_state = "OFF" if self.config.settings.get("muted", False) else "ON"
        quality = str(
            self.config.settings.get("particle_quality", "high")
        ).upper()
        options = self.micro_font.render(
            f"SOUND {sound_state}   •   PARTICLES {quality}   •   "
            f"DIFFICULTY {self.difficulty['name']}",
            True,
            GRAY,
        )
        self.screen.blit(options, options.get_rect(center=(WIDTH // 2, 832)))

        version = self.micro_font.render(f"v{VERSION}", True, GRAY)
        self.screen.blit(version, version.get_rect(center=(WIDTH // 2, HEIGHT - 24)))

    def draw_achievements_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(215)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(35, 48, WIDTH - 70, 880)
        pygame.draw.rect(self.screen, (0, 0, 55), panel, border_radius=12)
        pygame.draw.rect(self.screen, GOLD, panel, 3, border_radius=12)

        title = self.font.render("ACHIEVEMENTS", True, GOLD)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 88)))
        count = self.micro_font.render(
            f"{len(self.achievements_unlocked)} / {len(ACHIEVEMENTS)} unlocked",
            True,
            LIGHT_BLUE,
        )
        self.screen.blit(count, count.get_rect(center=(WIDTH // 2, 122)))

        y = 154
        for key, info in ACHIEVEMENTS.items():
            unlocked = key in self.achievements_unlocked
            color = GOLD if unlocked else (110, 110, 120)
            marker = "X" if unlocked else "-"
            name = self.tiny_font.render(f"[{marker}] {info['name']}", True, color)
            self.screen.blit(name, (62, y))
            description = self.micro_font.render(
                info["description"], True, WHITE if unlocked else (90, 90, 100)
            )
            self.screen.blit(
                description, (WIDTH - 62 - description.get_width(), y + 4)
            )
            y += 42

        footer = self.micro_font.render(
            "Press A or ESC to close", True, LIGHT_BLUE
        )
        self.screen.blit(footer, footer.get_rect(center=(WIDTH // 2, 894)))

    def draw_stats_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(215)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(55, 80, WIDTH - 110, HEIGHT - 190)
        pygame.draw.rect(self.screen, (0, 0, 55), panel, border_radius=12)
        pygame.draw.rect(self.screen, CYAN, panel, 3, border_radius=12)

        title = self.font.render("CAREER STATS", True, CYAN)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 124)))

        progression = self.config.progression
        rows = [
            ("High score", progression.get("high_score", 0)),
            ("Best combo", progression.get("best_combo", 0)),
            ("Best wave", progression.get("best_wave", 1)),
            ("Games played", progression.get("games_played", 0)),
            ("Victories", progression.get("victories", 0)),
            ("Bosses defeated", progression.get("bosses_defeated", 0)),
            ("Minions destroyed", progression.get("total_minions_defeated", 0)),
            ("Power-ups collected", progression.get("total_powerups_collected", 0)),
            ("Lasers fired", progression.get("total_lasers_fired", 0)),
            ("Dashes performed", progression.get("total_dashes", 0)),
            (
                "Achievements",
                f"{len(self.achievements_unlocked)}/{len(ACHIEVEMENTS)}",
            ),
        ]

        y = 186
        for index, (label, value) in enumerate(rows):
            row_color = (0, 0, 85) if index % 2 == 0 else (0, 0, 65)
            pygame.draw.rect(
                self.screen, row_color, (95, y - 4, WIDTH - 190, 34),
                border_radius=5,
            )
            label_surface = self.tiny_font.render(label, True, LIGHT_BLUE)
            self.screen.blit(label_surface, (115, y))
            value_surface = self.tiny_font.render(str(value), True, WHITE)
            self.screen.blit(
                value_surface,
                (WIDTH - 115 - value_surface.get_width(), y),
            )
            y += 42

        footer = self.micro_font.render(
            "Press S or ESC to close", True, LIGHT_BLUE
        )
        self.screen.blit(footer, footer.get_rect(center=(WIDTH // 2, y + 22)))

    def draw_hud(self):
        # Health bar
        bar_width = 250
        bar_x = 20
        bar_y = HEIGHT - 62
        ratio = self.spaceship.hp / self.spaceship.max_hp
        bar_color = lerp_color((220, 40, 40), (40, 230, 90), ratio)
        pygame.draw.rect(self.screen, (55, 0, 0), (bar_x, bar_y, bar_width, 30))
        pygame.draw.rect(
            self.screen, bar_color, (bar_x, bar_y, bar_width * ratio, 30)
        )
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, 30), 2)
        hp_text = self.tiny_font.render(f"HP {int(self.spaceship.hp)}", True, WHITE)
        self.screen.blit(hp_text, (bar_x + 8, bar_y + 5))

        # Shield bar
        if self.spaceship.shield > 0:
            shield_y = HEIGHT - 102
            shield_ratio = self.spaceship.shield / self.spaceship.shield_max
            pygame.draw.rect(self.screen, (0, 40, 60), (bar_x, shield_y, bar_width, 30))
            pygame.draw.rect(
                self.screen, CYAN, (bar_x, shield_y, bar_width * shield_ratio, 30)
            )
            pygame.draw.rect(self.screen, WHITE, (bar_x, shield_y, bar_width, 30), 2)
            shield_text = self.tiny_font.render(
                f"SHIELD {int(self.spaceship.shield)}", True, WHITE
            )
            self.screen.blit(shield_text, (bar_x + 8, shield_y + 5))

        # Lives and active power-ups
        lives_text = self.small_font.render(
            f"LIVES: {self.spaceship.lives}", True, PINK
        )
        self.screen.blit(lives_text, (bar_x, HEIGHT - 145))

        # Dash cooldown
        dash_ready = self.spaceship.dash_cooldown <= 0
        dash_ratio = 1.0 - (
            self.spaceship.dash_cooldown / max(1, self.spaceship.dash_cooldown_max)
        )
        dash_color = CYAN if dash_ready else (70, 95, 125)
        pygame.draw.rect(
            self.screen, (15, 20, 40), (WIDTH - 205, HEIGHT - 62, 185, 30)
        )
        pygame.draw.rect(
            self.screen,
            dash_color,
            (WIDTH - 205, HEIGHT - 62, 185 * dash_ratio, 30),
        )
        pygame.draw.rect(
            self.screen, WHITE, (WIDTH - 205, HEIGHT - 62, 185, 30), 2
        )
        dash_text = self.tiny_font.render(
            "DASH READY" if dash_ready else "DASH CHARGING", True, WHITE
        )
        self.screen.blit(
            dash_text, dash_text.get_rect(center=(WIDTH - 112, HEIGHT - 47))
        )

        powerup_y = HEIGHT - 185
        for attribute, label, color in (
            ("rapid_fire", "RAPID", YELLOW),
            ("spread_shot", "SPREAD", ORANGE),
            ("overdrive", "OVERDRIVE", PURPLE),
        ):
            remaining = getattr(self.spaceship, attribute)
            if remaining > 0:
                text = self.tiny_font.render(
                    f"{label} {remaining // 60 + 1}s", True, color
                )
                self.screen.blit(text, (bar_x, powerup_y))
                powerup_y -= 26

        # Boss bar
        if self.enemy and self.enemy.hp > 0:
            bar_x = WIDTH // 2 - 215
            ratio = self.enemy.health_ratio
            color = lerp_color((255, 70, 20), (255, 190, 40), ratio)
            pygame.draw.rect(self.screen, (70, 0, 0), (bar_x, 14, 430, 34))
            pygame.draw.rect(self.screen, color, (bar_x, 14, 430 * ratio, 34))
            pygame.draw.rect(self.screen, WHITE, (bar_x, 14, 430, 34), 3)
            boss_text = self.tiny_font.render(
                f"{self.enemy.name.upper()}  •  WAVE {self.round}/{MAX_ROUNDS}",
                True,
                WHITE,
            )
            self.screen.blit(boss_text, boss_text.get_rect(center=(WIDTH // 2, 31)))
            if ratio < 0.35 and (pygame.time.get_ticks() // 250) % 2 == 0:
                rage = self.micro_font.render("ENRAGED", True, YELLOW)
                self.screen.blit(rage, rage.get_rect(center=(WIDTH // 2, 58)))

        # Score and wave
        score_text = self.small_font.render(f"SCORE {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - 210, 14))
        best_score = max(
            self.score, self.config.progression.get("high_score", 0)
        )
        wave_text = self.micro_font.render(f"BEST {best_score}", True, LIGHT_BLUE)
        self.screen.blit(wave_text, (WIDTH - 210, 46))
        meta_text = self.micro_font.render(
            f"{self.difficulty['name']}  •  UPGRADES {self.run_upgrades}",
            True,
            GOLD,
        )
        self.screen.blit(
            meta_text, (WIDTH - 20 - meta_text.get_width(), 66)
        )

        # Combo meter
        if self.combo >= 2:
            combo_color = GOLD if self.combo < 10 else ORANGE
            combo_text = self.small_font.render(
                f"COMBO x{self.combo}   ({self.score_multiplier}x SCORE)",
                True,
                combo_color,
            )
            self.screen.blit(
                combo_text, combo_text.get_rect(center=(WIDTH // 2, 82))
            )
            meter_width = 190
            meter_x = WIDTH // 2 - meter_width // 2
            pygame.draw.rect(self.screen, (60, 40, 0), (meter_x, 100, meter_width, 6))
            pygame.draw.rect(
                self.screen,
                combo_color,
                (meter_x, 100, meter_width * (self.combo_timer / 90), 6),
            )

        if self.config.settings.get("muted", False):
            muted = self.micro_font.render("MUTED", True, RED)
            self.screen.blit(muted, (20, HEIGHT - 218))

    def draw_banner(self):
        if self.banner_timer <= 0 or not self.banner_title:
            return
        alpha = int(clamp(self.banner_timer * 5, 0, 255))
        title_surface = self.font_large.render(
            self.banner_title, True, self.banner_color
        )
        subtitle_surface = self.small_font.render(
            self.banner_subtitle, True, WHITE
        )
        panel_width = max(title_surface.get_width(), subtitle_surface.get_width()) + 60
        panel = pygame.Surface((panel_width, 104), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, int(alpha * 0.65)), panel.get_rect(), border_radius=10)
        pygame.draw.rect(
            panel,
            (*self.banner_color, alpha),
            panel.get_rect(),
            2,
            border_radius=10,
        )
        title_surface.set_alpha(alpha)
        subtitle_surface.set_alpha(alpha)
        panel.blit(
            title_surface,
            title_surface.get_rect(center=(panel_width // 2, 38)),
        )
        panel.blit(
            subtitle_surface,
            subtitle_surface.get_rect(center=(panel_width // 2, 76)),
        )
        self.screen.blit(
            panel,
            panel.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 220)),
        )

    def draw_upgrade(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(60, 150, WIDTH - 120, 620)
        pygame.draw.rect(self.screen, (0, 0, 50), panel, border_radius=12)
        pygame.draw.rect(self.screen, GOLD, panel, 3, border_radius=12)

        title = self.font_large.render(
            f"WAVE {self.round} CLEARED", True, GOLD
        )
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 188)))
        subtitle = self.small_font.render(
            "CHOOSE ONE UPGRADE FOR THE REST OF THE RUN", True, WHITE
        )
        self.screen.blit(
            subtitle, subtitle.get_rect(center=(WIDTH // 2, 228))
        )

        self.upgrade_buttons = {}
        card_y = 254
        for index, choice in enumerate(self.upgrade_choices):
            rect = pygame.Rect(90, card_y, WIDTH - 180, 118)
            self.upgrade_buttons[index] = rect
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            fill = (28, 28, 68) if hovered else (10, 10, 40)
            pygame.draw.rect(self.screen, fill, rect, border_radius=12)
            pygame.draw.rect(
                self.screen, choice["color"], rect, 3, border_radius=12
            )

            number = self.font.render(str(index + 1), True, choice["color"])
            self.screen.blit(
                number, number.get_rect(center=(rect.x + 42, rect.centery))
            )

            name = self.small_font.render(choice["name"], True, WHITE)
            self.screen.blit(name, (rect.x + 82, rect.y + 20))
            description = self.micro_font.render(
                choice["desc"], True, LIGHT_BLUE
            )
            self.screen.blit(description, (rect.x + 82, rect.y + 54))

            level = self.upgrades.get(choice["key"], 0)
            level_text = self.micro_font.render(
                f"LEVEL {level}/{choice['max_level']}",
                True,
                choice["color"],
            )
            self.screen.blit(
                level_text,
                (rect.right - 24 - level_text.get_width(), rect.y + 20),
            )

            pips = 10
            pip_width = 12
            pip_x = rect.x + 82
            pip_y = rect.bottom - 26
            for pip in range(min(choice["max_level"], pips)):
                pip_color = choice["color"] if pip < level else (55, 55, 70)
                pygame.draw.rect(
                    self.screen,
                    pip_color,
                    (pip_x + pip * (pip_width + 4), pip_y, pip_width, 8),
                    border_radius=3,
                )

            card_y += 136

        hint = self.micro_font.render(
            "Press 1, 2 or 3 — or click a card", True, LIGHT_BLUE
        )
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 686)))
        footer = self.micro_font.render(
            "Upgrades persist until this run ends", True, GRAY
        )
        self.screen.blit(footer, footer.get_rect(center=(WIDTH // 2, 722)))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(170)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font_huge.render("PAUSED", True, CYAN)
        self.screen.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, 258)))

        panel = pygame.Rect(WIDTH // 2 - 230, 310, 460, 300)
        pygame.draw.rect(self.screen, (0, 0, 70), panel, border_radius=12)
        pygame.draw.rect(self.screen, CYAN, panel, 2, border_radius=12)

        self.pause_buttons = {
            "resume": pygame.Rect(WIDTH // 2 - 150, 338, 300, 52),
            "mute": pygame.Rect(WIDTH // 2 - 150, 404, 300, 52),
            "menu": pygame.Rect(WIDTH // 2 - 150, 470, 300, 52),
        }
        self._draw_button(
            self.pause_buttons["resume"], "RESUME  [P]", GREEN, (120, 255, 120)
        )
        muted = self.config.settings.get("muted", False)
        self._draw_button(
            self.pause_buttons["mute"],
            "SOUND: OFF  [M]" if muted else "SOUND: ON  [M]",
            ORANGE if muted else CYAN,
            (255, 220, 150) if muted else (150, 245, 255),
        )
        self._draw_button(self.pause_buttons["menu"], "MENU  [ESC]", CYAN, (150, 245, 255))

        hint = self.micro_font.render(
            "R restarts   •   F11 fullscreen   •   V particles   •   O quits",
            True,
            LIGHT_BLUE,
        )
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 552)))

        run_stats = self.micro_font.render(
            f"WAVE {self.round}/{MAX_ROUNDS}   •   SCORE {self.score}   •   "
            f"UPGRADES {self.run_upgrades}   •   {self.difficulty['name']}",
            True,
            WHITE,
        )
        self.screen.blit(run_stats, run_stats.get_rect(center=(WIDTH // 2, 582)))

    def draw_end_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(205)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        if self.game_state == "victory":
            title = self.font_huge.render("VICTORY!", True, GOLD)
            subtitle = self.font.render("ALL BOSSES DEFEATED", True, WHITE)
        else:
            title = self.font_huge.render("GAME OVER", True, RED)
            subtitle = self.font.render(
                self.game_over_reason.upper() or "MISSION FAILED", True, WHITE
            )

        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 210)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 276)))

        score_text = self.font.render(f"FINAL SCORE  {self.score}", True, CYAN)
        self.screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, 340)))

        high_text = self.small_font.render(
            f"HIGH SCORE  {self.config.progression.get('high_score', 0)}",
            True,
            WHITE,
        )
        self.screen.blit(high_text, high_text.get_rect(center=(WIDTH // 2, 386)))

        if self.new_high_score:
            new_text = self.small_font.render("NEW HIGH SCORE!", True, GOLD)
            self.screen.blit(
                new_text, new_text.get_rect(center=(WIDTH // 2, 420))
            )

        stats_y = 452
        stats = [
            f"WAVES CLEARED: {min(self.round, MAX_ROUNDS)}/{MAX_ROUNDS}",
            f"DIFFICULTY: {self.difficulty['name']}",
            f"BEST COMBO: {self.max_combo}",
            f"MINIONS: {self.run_minions}",
            f"POWER-UPS: {self.run_powerups}",
            f"UPGRADES: {self.run_upgrades}",
            f"LIVES LOST: {self.lives_lost}",
            f"DASHES: {self.run_dashes}",
        ]
        for index, text in enumerate(stats):
            row = index // 2
            column = index % 2
            surface = self.tiny_font.render(text, True, LIGHT_BLUE)
            center = (WIDTH // 2 - 120 + column * 240, stats_y + row * 28)
            self.screen.blit(surface, surface.get_rect(center=center))

        self.end_buttons = {
            "restart": pygame.Rect(WIDTH // 2 - 170, 572, 160, 58),
            "menu": pygame.Rect(WIDTH // 2 + 10, 572, 160, 58),
        }
        self._draw_button(
            self.end_buttons["restart"], "RESTART [R]", GREEN, (120, 255, 120)
        )
        self._draw_button(
            self.end_buttons["menu"], "MENU [ESC]", CYAN, (150, 245, 255)
        )

        hint = self.micro_font.render(
            "Press O to quit the game", True, WHITE
        )
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 640)))

    def draw_toasts(self):
        panels = []
        for toast in self.toasts:
            alpha = int(clamp(toast["timer"] * 4, 0, 255))
            surface = self.small_font.render(toast["text"], True, toast["color"])
            surface.set_alpha(alpha)
            panel = pygame.Surface(
                (surface.get_width() + 32, surface.get_height() + 12),
                pygame.SRCALPHA,
            )
            pygame.draw.rect(
                panel, (0, 0, 0, int(alpha * 0.65)), panel.get_rect(), border_radius=8
            )
            pygame.draw.rect(
                panel,
                (*toast["color"], alpha),
                panel.get_rect(),
                2,
                border_radius=8,
            )
            text_rect = surface.get_rect(
                center=(panel.get_width() // 2, panel.get_height() // 2)
            )
            panel.blit(surface, text_rect)
            panels.append(panel)

        if self.game_state == "landing":
            # Stack upward so menu toasts never run off the bottom edge.
            y = HEIGHT - 100
            for panel in reversed(panels):
                self.screen.blit(panel, panel.get_rect(center=(WIDTH // 2, y)))
                y -= panel.get_height() + 8
        else:
            y = 140
            for panel in panels:
                self.screen.blit(panel, panel.get_rect(center=(WIDTH // 2, y)))
                y += panel.get_height() + 8

    # -- input --------------------------------------------------------------
    def _handle_key(self, key):
        if key == pygame.K_o:
            self.config.save()
            return False

        if key == pygame.K_F11:
            self._toggle_fullscreen()
            return True

        if key == pygame.K_v:
            self.cycle_particle_quality()
            return True

        if key == pygame.K_LEFTBRACKET:
            volume = max(0.0, float(self.config.settings.get("sfx_volume", 0.65)) - 0.1)
            self.config.settings["sfx_volume"] = volume
            self.config.settings["music_volume"] = max(0.0, float(self.config.settings.get("music_volume", 0.35)) - 0.1)
            self.config.save()
            self.add_toast(f"VOLUME {int(volume * 100)}%", CYAN, 80)
            return True

        if key == pygame.K_RIGHTBRACKET:
            volume = min(1.0, float(self.config.settings.get("sfx_volume", 0.65)) + 0.1)
            self.config.settings["sfx_volume"] = volume
            self.config.settings["music_volume"] = min(1.0, float(self.config.settings.get("music_volume", 0.35)) + 0.1)
            self.config.save()
            self.add_toast(f"VOLUME {int(volume * 100)}%", CYAN, 80)
            return True

        if key == pygame.K_a and self.game_state == "landing":
            self.show_achievements = not self.show_achievements
            self.show_stats = False
            self.audio.play("click")
            return True

        if key == pygame.K_s and self.game_state == "landing":
            self.show_stats = not self.show_stats
            self.show_achievements = False
            self.audio.play("click")
            return True

        if key == pygame.K_m:
            self.toggle_mute()
            return True

        number_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_KP1: 0,
            pygame.K_KP2: 1,
            pygame.K_KP3: 2,
        }
        if key in number_keys:
            index = number_keys[key]
            if self.game_state == "upgrade":
                self.choose_upgrade(index)
                return True
            if self.game_state == "landing":
                difficulty_key = tuple(DIFFICULTIES)[index]
                self.set_difficulty(difficulty_key)
                return True

        if key == pygame.K_ESCAPE:
            if self.game_state == "playing":
                self.game_state = "paused"
                self.audio.play("click")
            elif self.game_state == "paused":
                self.return_to_menu()
            elif self.game_state == "landing":
                if self.show_achievements:
                    self.show_achievements = False
                elif self.show_stats:
                    self.show_stats = False
                else:
                    return False
            elif self.game_state == "upgrade":
                # Do not let a stray ESC skip a free upgrade.
                return True
            else:
                self.return_to_menu()
            return True

        if key == pygame.K_p:
            if self.game_state == "playing":
                self.game_state = "paused"
                self.audio.play("click")
            elif self.game_state == "paused":
                self.game_state = "playing"
                self.audio.play("click")
            return True

        if key == pygame.K_r:
            self.start_game()
            return True

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.game_state in ("landing", "game_over", "victory"):
                self.start_game()
            elif self.game_state == "paused":
                self.game_state = "playing"
            elif self.game_state == "upgrade":
                self.choose_upgrade(0)
            return True

        if (
            key
            in (
                pygame.K_LSHIFT,
                pygame.K_RSHIFT,
                pygame.K_x,
                pygame.K_LCTRL,
                pygame.K_RCTRL,
            )
            and self.game_state == "playing"
        ):
            if self.spaceship.start_dash(pygame.key.get_pressed()):
                self.run_dashes += 1
                self.config.progression["total_dashes"] = (
                    self.config.progression.get("total_dashes", 0) + 1
                )
                self.audio.play("dash")
                self.add_screen_shake(5)
                self.add_particles(
                    self.spaceship.x + self.spaceship.width // 2,
                    self.spaceship.y + self.spaceship.height // 2,
                    CYAN,
                    10,
                    speed=4,
                )
            return True

        if key == pygame.K_SPACE and self.game_state == "playing":
            self.fire()
        return True

    def _handle_click(self, position):
        if self.game_state == "landing":
            if self.show_achievements or self.show_stats:
                return True
            for difficulty_key, rect in self.difficulty_buttons.items():
                if rect.collidepoint(position):
                    self.set_difficulty(difficulty_key)
                    return True
            if self.start_button.collidepoint(position):
                self.start_game()
                return True
        elif self.game_state == "upgrade":
            for index, rect in self.upgrade_buttons.items():
                if rect.collidepoint(position):
                    self.choose_upgrade(index)
                    return True
        elif self.game_state == "paused":
            if self.pause_buttons.get("resume", pygame.Rect(0, 0, 0, 0)).collidepoint(
                position
            ):
                self.game_state = "playing"
                self.audio.play("click")
            elif self.pause_buttons.get("mute", pygame.Rect(0, 0, 0, 0)).collidepoint(
                position
            ):
                self.toggle_mute()
            elif self.pause_buttons.get("menu", pygame.Rect(0, 0, 0, 0)).collidepoint(
                position
            ):
                self.return_to_menu()
        elif self.game_state in ("game_over", "victory"):
            if self.end_buttons.get("restart", pygame.Rect(0, 0, 0, 0)).collidepoint(
                position
            ):
                self.start_game()
            elif self.end_buttons.get("menu", pygame.Rect(0, 0, 0, 0)).collidepoint(
                position
            ):
                self.return_to_menu()
        return True

    def _handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type == getattr(pygame, "WINDOWFOCUSLOST", -1):
            if self.game_state == "playing":
                self.game_state = "paused"
            return True
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event.key)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        return True

    # -- main loop ----------------------------------------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if not self._handle_event(event):
                    running = False
                    break
            if not running:
                break
            self.update()
            self.draw()
            self.clock.tick(FPS)

        self.config.save()
        pygame.quit()


if __name__ == "__main__":
    game = EnhancedGame()
    game.run()
