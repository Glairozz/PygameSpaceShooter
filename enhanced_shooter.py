"""Enhanced Pygame Space Shooter - Dragon Roaster (v2)"""
import pygame
import random
import math
import sys
import time
from pathlib import Path

from config import *

pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    SOUND_ENABLED = True
except:
    SOUND_ENABLED = False

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = None
        if SOUND_ENABLED:
            try:
                # Create simple synthetic sounds using pygame
                pass
            except:
                pass
    
    def play_shoot(self):
        pass
    
    def play_explosion(self):
        pass
    
    def play_hit(self):
        pass


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=40, size=None, shape='circle'):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-8, 8)
        self.vy = vy if vy is not None else random.uniform(-8, 8)
        self.life = life
        self.max_life = life
        self.size = size if size is not None else random.randint(1, 4)
        self.gravity = 0.15
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
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(self.size * (self.life / self.max_life)))
        surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        color_with_alpha = (*self.color, alpha)
        if self.shape == 'circle':
            pygame.draw.circle(surf, color_with_alpha, (size * 2, size * 2), size)
        elif self.shape == 'rect':
            pygame.draw.rect(surf, color_with_alpha, (size, size, size*2, size*2))
        screen.blit(surf, (int(self.x - size*2), int(self.y - size*2)))


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
            self.twinkle = random.random()
        elif layer == 1:
            self.size = random.choice([1, 2])
            self.color = CYAN
            self.twinkle = random.random()
        else:
            self.size = 2
            self.color = YELLOW
            self.twinkle = random.random()
    
    def update(self, dt=1.0):
        self.y += self.speed * dt * 60 / FPS
        self.twinkle += 0.05
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)
    
    def draw(self, screen):
        brightness = 0.7 + 0.3 * math.sin(self.twinkle)
        color = tuple(int(c * brightness) for c in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)


class Nebula:
    def __init__(self):
        self.x = random.randint(-200, WIDTH)
        self.y = random.randint(-300, HEIGHT - 300)
        self.size = random.randint(150, 300)
        self.color = random.choice([(80, 0, 120), (0, 50, 100), (100, 0, 80)])
        self.speed = 0.2
        self.alpha = random.randint(20, 40)
    
    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = -self.size
            self.x = random.randint(-200, WIDTH)
    
    def draw(self, screen):
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(surf, color_with_alpha, (self.size // 2, self.size // 2), self.size // 2)
        screen.blit(surf, (int(self.x), int(self.y)))


class PowerUp:
    def __init__(self, x, y, power_type=None):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = 2.5
        if power_type is None:
            self.type = random.choices(
                ['health', 'shield', 'rapid', 'spread', 'bomb', 'life'],
                weights=[20, 15, 15, 15, 10, 5]
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
        pulse = abs(math.sin(self.timer * 0.12)) * 4 + 32
        # Glow
        glow_surf = pygame.Surface((pulse, pulse), pygame.SRCALPHA)
        glow_colors = {
            'health': GREEN, 'shield': CYAN, 'rapid': YELLOW,
            'spread': ORANGE, 'bomb': RED, 'life': PINK
        }
        glow_color = (*glow_colors.get(self.type, WHITE), 40)
        pygame.draw.circle(glow_surf, glow_color, (pulse//2, pulse//2), pulse//2)
        screen.blit(glow_surf, (self.x + 15 - pulse//2, y_pos + 15 - pulse//2))
        
        if self.type == 'health':
            pygame.draw.rect(screen, GREEN, (self.x, y_pos, self.width, self.height), border_radius=3)
            pygame.draw.line(screen, WHITE, (self.x + 15, y_pos + 6), (self.x + 15, y_pos + 24), 5)
            pygame.draw.line(screen, WHITE, (self.x + 6, y_pos + 15), (self.x + 24, y_pos + 15), 5)
        elif self.type == 'shield':
            pygame.draw.circle(screen, CYAN, (self.x + 15, int(y_pos) + 15), 14, 4)
            pygame.draw.circle(screen, LIGHT_BLUE, (self.x + 15, int(y_pos) + 15), 8)
        elif self.type == 'rapid':
            points = [(self.x+15, y_pos), (self.x+25, y_pos+20), (self.x+15, y_pos+14), (self.x+5, y_pos+20)]
            pygame.draw.polygon(screen, YELLOW, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        elif self.type == 'spread':
            points = [(self.x+15, y_pos), (self.x+8, y_pos+22), (self.x+15, y_pos+16), (self.x+22, y_pos+22)]
            pygame.draw.polygon(screen, ORANGE, points)
            pygame.draw.polygon(screen, WHITE, points, 2)
        elif self.type == 'bomb':
            pygame.draw.circle(screen, RED, (self.x + 15, int(y_pos) + 15), 13)
            pygame.draw.circle(screen, WHITE, (self.x + 15, int(y_pos) + 10), 3)
            pygame.draw.line(screen, WHITE, (self.x + 15, y_pos + 12), (self.x + 15, y_pos + 18), 2)
        elif self.type == 'life':
            pygame.draw.ellipse(screen, PINK, (self.x + 5, y_pos + 8, 20, 16))
            pygame.draw.polygon(screen, PINK, [(self.x + 15, y_pos + 5), (self.x + 10, y_pos + 10), (self.x + 20, y_pos + 10)])
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


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
        self.shoot_delay = 180
        self.shield = 0
        self.shield_max = 150
        self.rapid_fire = 0
        self.spread_shot = 0
        self.invulnerable = 0
        self.lives = 3
        self.thruster_frame = 0
        
    def move(self, keys, dt=1.0):
        speed = self.speed * dt * 60 / FPS
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(0, self.x - speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(WIDTH - self.width, self.x + speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(HEIGHT // 4, self.y - speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(HEIGHT - self.height - 35, self.y + speed)
        self.thruster_frame += 1
    
    def shoot(self):
        current_time = pygame.time.get_ticks()
        delay = self.shoot_delay // 3 if self.rapid_fire > 0 else self.shoot_delay
        if current_time - self.last_shot > delay:
            self.last_shot = current_time
            lasers = []
            if self.spread_shot > 0:
                lasers.append(Laser(self.x + self.width // 2, self.y, -1, CYAN))
                lasers.append(Laser(self.x + self.width // 2 - 18, self.y + 8, -1, CYAN, angle=-8))
                lasers.append(Laser(self.x + self.width // 2 + 18, self.y + 8, -1, CYAN, angle=8))
                lasers.append(Laser(self.x + 15, self.y + 12, -1, (100, 255, 255), angle=-4))
                lasers.append(Laser(self.x + self.width - 15, self.y + 12, -1, (100, 255, 255), angle=4))
            else:
                lasers.append(Laser(self.x + self.width // 2, self.y, -1, CYAN))
                if self.rapid_fire > 0:
                    lasers.append(Laser(self.x + 12, self.y + 5, -1, (150, 255, 255)))
                    lasers.append(Laser(self.x + self.width - 12, self.y + 5, -1, (150, 255, 255)))
            return lasers
        return []
    
    def update(self):
        if self.rapid_fire > 0:
            self.rapid_fire -= 1
        if self.spread_shot > 0:
            self.spread_shot -= 1
        if self.invulnerable > 0:
            self.invulnerable -= 1
    
    def draw(self, screen):
        if self.invulnerable > 0 and (self.invulnerable // 4) % 2 == 0:
            return
        
        if self.shield > 0:
            shield_surf = pygame.Surface((self.width + 30, self.height + 30), pygame.SRCALPHA)
            alpha = int(120 * (self.shield / self.shield_max))
            pulse_shield = math.sin(pygame.time.get_ticks() * 0.01) * 2
            pygame.draw.circle(shield_surf, (*CYAN, alpha), (self.width//2 + 15, self.height//2 + 15), int(38 + pulse_shield), 3)
            screen.blit(shield_surf, (self.x - 15, self.y - 15))
        
        # Thruster particles
        if (self.thruster_frame // 3) % 2 == 0:
            pygame.draw.circle(screen, ORANGE, (int(self.x + self.width//2 - 8), int(self.y + self.height - 2)), 4)
            pygame.draw.circle(screen, YELLOW, (int(self.x + self.width//2 - 8), int(self.y + self.height - 2)), 2)
            pygame.draw.circle(screen, ORANGE, (int(self.x + self.width//2 + 8), int(self.y + self.height - 2)), 4)
            pygame.draw.circle(screen, YELLOW, (int(self.x + self.width//2 + 8), int(self.y + self.height - 2)), 2)
        
        pygame.draw.polygon(screen, (50, 100, 255), [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width // 2, self.y + self.height - 12),
            (self.x + self.width, self.y + self.height)
        ])
        pygame.draw.ellipse(screen, CYAN, (self.x + self.width // 2 - 9, self.y + 6, 18, 12))
        pygame.draw.ellipse(screen, (200, 255, 255), (self.x + self.width // 2 - 6, self.y + 9, 12, 6))
        pygame.draw.polygon(screen, (30, 60, 180), [
            (self.x, self.y + 12), (self.x - 12, self.y + 15), (self.x + 12, self.y + self.height - 12)
        ])
        pygame.draw.polygon(screen, (30, 60, 180), [
            (self.x + self.width, self.y + 12), (self.x + self.width + 12, self.y + 15), (self.x + self.width - 12, self.y + self.height - 12)
        ])
    
    def take_damage(self, damage):
        if self.invulnerable > 0:
            return False
        if self.shield > 0:
            self.shield -= damage
            if self.shield < 0:
                self.hp += self.shield
                self.shield = 0
        else:
            self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        self.invulnerable = 70
        return True
    
    def get_rect(self):
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)


class Laser:
    def __init__(self, x, y, direction, color, angle=0):
        self.x = x
        self.y = y
        self.width = 5
        self.height = 24
        self.speed = 14
        self.direction = direction
        self.color = color
        self.angle = angle
        self.damage = 30 if direction == -1 else 18
        self.trail = []
        
    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 6:
            self.trail.pop(0)
        self.y += self.speed * self.direction
        self.x += math.sin(math.radians(self.angle)) * 4
    
    def draw(self, screen):
        for i, pos in enumerate(self.trail):
            alpha = int(200 * (i / len(self.trail)))
            trail_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color, alpha), (2, 2), 2)
            screen.blit(trail_surf, (int(pos[0] - 2), int(pos[1] - 2)))
        if self.direction == -1:
            pygame.draw.rect(screen, self.color, (self.x - 2, self.y, self.width, self.height), border_radius=2)
            glow_surf = pygame.Surface((self.width + 10, self.height + 4), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*WHITE, 40), (3, 2), self.width + 4, self.height)
            screen.blit(glow_surf, (self.x - 5, self.y - 2))
        else:
            pygame.draw.rect(screen, self.color, (self.x - 2, self.y, self.width, self.height), border_radius=2)
            for i in range(2):
                pygame.draw.circle(screen, (255, 100, 100), (int(self.x + (i-0.5)*3), int(self.y + self.height + i*2)), 2)
    
    def get_rect(self):
        return pygame.Rect(self.x - 2, self.y, self.width, self.height)
    
    def is_off_screen(self):
        return self.y < -80 or self.y > HEIGHT + 80 or self.x < -60 or self.x > WIDTH + 60


class Enemy:
    def __init__(self, round_number):
        self.x = random.randint(80, WIDTH - 200)
        self.y = 50
        self.width = 90
        self.height = 70
        self.hp = 300 + round_number * 80
        self.max_hp = self.hp
        self.last_shot = 0
        self.shoot_delay = max(600, 2200 - round_number * 180)
        self.move_direction = random.choice([-1, 1])
        self.move_timer = 0
        self.round_number = round_number
        self.pattern_timer = 0
        self.phase = 0
        
    def move(self):
        self.move_timer += 1
        self.pattern_timer += 1
        
        if self.pattern_timer < 150:
            self.x += self.move_direction * (4 + self.round_number * 0.4)
            if self.move_timer > 80:
                self.move_timer = 0
                self.move_direction *= -1
        elif self.pattern_timer < 350:
            self.x += math.sin(self.pattern_timer * 0.06) * 6
        elif self.pattern_timer < 500:
            self.x += self.move_direction * 5
        else:
            if self.pattern_timer > 650:
                self.pattern_timer = 0
            self.x += math.cos(self.pattern_timer * 0.04) * 4
        
        self.x = max(20, min(WIDTH - self.width - 20, self.x))
        # Slight vertical movement on higher rounds
        if self.round_number >= 4:
            self.y = 50 + math.sin(self.pattern_timer * 0.03) * 15
    
    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            lasers = []
            if self.round_number >= 2:
                lasers.append(Laser(self.x + self.width // 2, self.y + self.height, 1, RED))
                lasers.append(Laser(self.x + self.width // 3, self.y + self.height - 3, 1, RED, angle=-12))
                lasers.append(Laser(self.x + 2*self.width // 3, self.y + self.height - 3, 1, RED, angle=12))
            if self.round_number >= 4:
                lasers.append(Laser(self.x + self.width // 4, self.y + self.height - 6, 1, ORANGE, angle=-20))
                lasers.append(Laser(self.x + 3*self.width // 4, self.y + self.height - 6, 1, ORANGE, angle=20))
            if self.round_number >= 5:
                # Spiral pattern
                for i in range(5):
                    angle = (i - 2) * 15
                    lasers.append(Laser(self.x + self.width // 2, self.y + self.height, 1, PURPLE, angle=angle))
            if len(lasers) == 0:
                lasers.append(Laser(self.x + self.width // 2, self.y + self.height, 1, RED))
            return lasers
        return []
    
    def draw(self, screen):
        color_intensity = min(255, 140 + self.round_number * 20)
        enemy_color = (color_intensity, 40, 40)
        accent = (255, 60, 60)
        
        pygame.draw.polygon(screen, enemy_color, [
            (self.x + self.width // 2, self.y + self.height),
            (self.x, self.y),
            (self.x + self.width // 2, self.y + 12),
            (self.x + self.width, self.y)
        ])
        pygame.draw.ellipse(screen, PURPLE, (self.x + self.width // 2 - 10, self.y + self.height - 18, 20, 14))
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 - 7, self.y + 14), 5)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 + 7, self.y + 14), 5)
        pygame.draw.circle(screen, (255, 200, 0), (self.x + self.width // 2 - 7, self.y + 14), 2)
        pygame.draw.circle(screen, (255, 200, 0), (self.x + self.width // 2 + 7, self.y + 14), 2)
        
        pygame.draw.polygon(screen, (100, 20, 20), [
            (self.x, self.y + 12), (self.x - 14, self.y + 15), (self.x + 12, self.y + self.height - 12)
        ])
        pygame.draw.polygon(screen, (100, 20, 20), [
            (self.x + self.width, self.y + 12), (self.x + self.width + 14, self.y + 15), (self.x + self.width - 12, self.y + self.height - 12)
        ])
        
        if (pygame.time.get_ticks() // 150) % 2 == 0:
            pygame.draw.circle(screen, RED, (self.x + 14, self.y + self.height // 2), 4)
            pygame.draw.circle(screen, RED, (self.x + self.width - 14, self.y + self.height // 2), 4)
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def get_rect(self):
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 15)


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
        self.rotation = 0
        self.rot_speed = random.uniform(-3, 3)
        
    def move(self):
        self.y += self.speed
        self.rotation += self.rot_speed
    
    def draw(self, screen):
        points = []
        for i in range(10):
            angle = math.radians(self.rotation + i * 36)
            radius = self.size // 2 + random.randint(-3, 3)
            px = self.x + self.size // 2 + math.cos(angle) * radius
            py = self.y + self.size // 2 + math.sin(angle) * radius
            points.append((px, py))
        if len(points) >= 3:
            pygame.draw.polygon(screen, (90, 90, 90), points)
            pygame.draw.polygon(screen, (60, 60, 60), points, 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + 10), int(self.y + 12)), 4)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.size - 12), int(self.y + 18)), 3)
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def get_rect(self):
        return pygame.Rect(self.x + 3, self.y + 3, self.width - 6, self.height - 6)
    
    def is_off_screen(self):
        return self.y > HEIGHT + 70


class EnhancedGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE + " - v2")
        self.clock = pygame.time.Clock()
        self.font_huge = pygame.font.Font(None, 82)
        self.font_large = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 30)
        self.tiny_font = pygame.font.Font(None, 24)
        self.micro_font = pygame.font.Font(None, 18)
        self.reset_game()
        self.config = config
        self.stars = [Star(i % 3) for i in range(180)]
        self.nebulas = [Nebula() for _ in range(3)]
        self.achievements_unlocked = set(self.config.progression.get('achievements', []))
        print("Enhanced Dragon Roaster v2 initialized!")
    
    def reset_game(self):
        self.spaceship = Spaceship(WIDTH // 2 - 32, HEIGHT - 190)
        self.player_lasers = []
        self.enemy_lasers = []
        self.asteroids = []
        self.powerups = []
        self.particles = []
        self.round = 1
        self.enemy = Enemy(self.round)
        self.score = 0
        self.game_state = "landing"
        self.asteroid_spawn_timer = 0
        self.powerup_spawn_timer = 250
        self.screen_shake = 0
        self.shake_offset = (0, 0)
        self.combo = 0
        self.combo_timer = 0
    
    def spawn_asteroid(self):
        if self.asteroid_spawn_timer <= 0:
            x = random.randint(20, WIDTH - 80)
            self.asteroids.append(Asteroid(x, -70))
            self.asteroid_spawn_timer = random.randint(60, 150)
        else:
            self.asteroid_spawn_timer -= 1
    
    def spawn_powerup(self):
        if self.powerup_spawn_timer <= 0:
            if random.random() < 0.18:
                x = random.randint(35, WIDTH - 75)
                self.powerups.append(PowerUp(x, -40))
            self.powerup_spawn_timer = random.randint(350, 650)
        else:
            self.powerup_spawn_timer -= 1
    
    def add_particles(self, x, y, color, count=20, shape='circle'):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, shape=shape))
    
    def add_screen_shake(self, intensity=12):
        self.screen_shake = max(self.screen_shake, intensity)
    
    def check_achievements(self):
        new_ach = []
        if self.score >= 1000 and 'score_1000' not in self.achievements_unlocked:
            new_ach.append('score_1000')
        if self.score >= 5000 and 'score_5000' not in self.achievements_unlocked:
            new_ach.append('score_5000')
        if self.config.progression.get('bosses_defeated', 0) >= 10 and 'boss_hunter' not in self.achievements_unlocked:
            new_ach.append('boss_hunter')
        for ach in new_ach:
            self.achievements_unlocked.add(ach)
            self.config.progression['achievements'] = list(self.achievements_unlocked)
        if new_ach:
            self.config.save()
    
    def update(self):
        if self.screen_shake > 0:
            self.shake_offset = (random.randint(-self.screen_shake, self.screen_shake),
                               random.randint(-self.screen_shake, self.screen_shake))
            self.screen_shake -= 1
        else:
            self.shake_offset = (0, 0)
        
        if self.game_state != "playing":
            for star in self.stars:
                star.update()
            for nebula in self.nebulas:
                nebula.update()
            return
        
        dt = self.clock.get_time() / 1000.0
        keys = pygame.key.get_pressed()
        self.spaceship.move(keys, dt)
        self.spaceship.update()
        
        for star in self.stars:
            star.update()
        for nebula in self.nebulas:
            nebula.update()
        
        self.spawn_asteroid()
        self.spawn_powerup()
        
        for laser in self.player_lasers[:]:
            laser.move()
            if laser.is_off_screen():
                self.player_lasers.remove(laser)
        for laser in self.enemy_lasers[:]:
            laser.move()
            if laser.is_off_screen():
                self.enemy_lasers.remove(laser)
        for asteroid in self.asteroids[:]:
            asteroid.move()
            if asteroid.is_off_screen():
                self.asteroids.remove(asteroid)
        for powerup in self.powerups[:]:
            if not powerup.update():
                self.powerups.remove(powerup)
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)
        
        if self.enemy:
            self.enemy.move()
            enemy_lasers = self.enemy.shoot()
            for laser in enemy_lasers:
                self.enemy_lasers.append(laser)
        
        self.handle_collisions()
        
        if self.spaceship.hp <= 0 and self.spaceship.lives <= 0:
            if self.game_state != "game_over":
                self.game_state = "game_over"
                self.config.progression['games_played'] = self.config.progression.get('games_played', 0) + 1
                self.check_achievements()
                if self.score > self.config.progression.get('high_score', 0):
                    self.config.progression['high_score'] = self.score
                self.config.save()
        elif self.enemy and self.enemy.hp <= 0:
            self.score += 200 * self.round
            self.add_particles(self.enemy.x + self.enemy.width // 2,
                             self.enemy.y + self.enemy.height // 2, RED, 40)
            self.add_screen_shake(18)
            self.config.progression['bosses_defeated'] = self.config.progression.get('bosses_defeated', 0) + 1
            self.check_achievements()
            self.next_round()
    
    def handle_collisions(self):
        for laser in self.player_lasers[:]:
            if self.enemy and laser.get_rect().colliderect(self.enemy.get_rect()):
                self.enemy.take_damage(laser.damage)
                self.add_particles(laser.x, laser.y, CYAN, 10)
                self.combo += 1
                self.combo_timer = 60
                try:
                    self.player_lasers.remove(laser)
                except ValueError:
                    pass
                continue
        
        for laser in self.player_lasers[:]:
            for asteroid in self.asteroids[:]:
                if laser.get_rect().colliderect(asteroid.get_rect()):
                    asteroid.take_damage(laser.damage)
                    self.add_particles(laser.x, laser.y, (150, 150, 150), 6)
                    try:
                        self.player_lasers.remove(laser)
                    except ValueError:
                        pass
                    if asteroid.hp <= 0:
                        try:
                            self.asteroids.remove(asteroid)
                        except ValueError:
                            pass
                        self.score += 40
                        self.add_particles(asteroid.x + asteroid.width // 2,
                                         asteroid.y + asteroid.height // 2, (120, 120, 120), 16)
                    break
        
        for laser in self.enemy_lasers[:]:
            if laser.get_rect().colliderect(self.spaceship.get_rect()) and self.spaceship.invulnerable == 0:
                if self.spaceship.take_damage(laser.damage):
                    self.add_particles(laser.x, laser.y, RED, 12)
                    self.add_screen_shake(7)
                    self.combo = 0
                try:
                    self.enemy_lasers.remove(laser)
                except ValueError:
                    pass
        
        for asteroid in self.asteroids[:]:
            if self.spaceship.get_rect().colliderect(asteroid.get_rect()) and self.spaceship.invulnerable == 0:
                if self.spaceship.take_damage(18):
                    self.add_particles(asteroid.x + asteroid.width // 2,
                                     asteroid.y + asteroid.height // 2, ORANGE, 18)
                    self.add_screen_shake(10)
                    self.combo = 0
                try:
                    self.asteroids.remove(asteroid)
                except ValueError:
                    pass
        
        for powerup in self.powerups[:]:
            if self.spaceship.get_rect().colliderect(powerup.get_rect()):
                self.apply_powerup(powerup.type)
                self.add_particles(powerup.x + 15, powerup.y + 15, WHITE, 8)
                try:
                    self.powerups.remove(powerup)
                except ValueError:
                    pass
    
    def apply_powerup(self, power_type):
        if power_type == 'health':
            self.spaceship.hp = min(self.spaceship.max_hp, self.spaceship.hp + 40)
        elif power_type == 'shield':
            self.spaceship.shield = min(self.spaceship.shield_max, self.spaceship.shield + 60)
        elif power_type == 'rapid':
            self.spaceship.rapid_fire = 700
        elif power_type == 'spread':
            self.spaceship.spread_shot = 700
        elif power_type == 'bomb':
            self.enemy_lasers.clear()
            for _ in range(50):
                self.add_particles(random.randint(0, WIDTH), random.randint(0, HEIGHT), YELLOW, 1)
            self.add_screen_shake(25)
            self.score += 50
        elif power_type == 'life':
            self.spaceship.lives += 1
    
    def next_round(self):
        self.round += 1
        if self.round > 7:
            self.game_state = "victory"
            self.check_achievements()
            if self.score > self.config.progression.get('high_score', 0):
                self.config.progression['high_score'] = self.score
            self.config.save()
        else:
            self.enemy = Enemy(self.round)
            self.player_lasers.clear()
            self.enemy_lasers.clear()
            self.asteroids.clear()
            self.powerups.clear()
            if self.round % 2 == 0:
                for i in range(3):
                    self.powerups.append(PowerUp(random.randint(50, WIDTH-80), -40, random.choice(['health', 'shield'])))
    
    def draw(self):
        offset_x, offset_y = self.shake_offset
        self.screen.fill(BLACK)
        
        for nebula in self.nebulas:
            nebula.draw(self.screen)
        for star in self.stars:
            star.draw(self.screen)
        
        if self.game_state == "landing":
            self.draw_landing()
        elif self.game_state == "playing" or self.game_state == "paused":
            for powerup in self.powerups:
                powerup.draw(self.screen)
            for asteroid in self.asteroids:
                asteroid.draw(self.screen)
            for laser in self.player_lasers:
                laser.draw(self.screen)
            for laser in self.enemy_lasers:
                laser.draw(self.screen)
            for particle in self.particles:
                particle.draw(self.screen)
            if self.enemy and self.enemy.hp > 0:
                self.enemy.draw(self.screen)
            self.spaceship.draw(self.screen)
            self.draw_hud()
            if self.combo > 2 and self.game_state == "playing":
                combo_text = self.small_font.render(f"COMBO x{self.combo}", True, YELLOW)
                combo_rect = combo_text.get_rect(center=(WIDTH // 2, 150))
                self.screen.blit(combo_text, combo_rect)
            if self.game_state == "paused":
                self.draw_pause()
        elif self.game_state in ["game_over", "victory"]:
            self.draw_end_screen()
        
        pygame.display.flip()
    
    def draw_landing(self):
        title = self.font_huge.render("DRAGON ROASTER", True, YELLOW)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        # Glow effect
        title_glow = self.font_huge.render("DRAGON ROASTER", True, ORANGE)
        glow_rect = title_glow.get_rect(center=(WIDTH // 2 + 2, HEIGHT // 6 + 2))
        self.screen.blit(title_glow, glow_rect)
        self.screen.blit(title, title_rect)
        
        subtitle = self.font.render("Enhanced Space Battle v2", True, CYAN)
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 6 + 90))
        self.screen.blit(subtitle, subtitle_rect)
        
        hs_text = self.small_font.render(f"High Score: {self.config.progression.get('high_score', 0)}", True, WHITE)
        hs_rect = hs_text.get_rect(center=(WIDTH // 2, HEIGHT // 6 + 140))
        self.screen.blit(hs_text, hs_rect)
        bosses_text = self.tiny_font.render(f"Bosses Defeated: {self.config.progression.get('bosses_defeated', 0)}", True, LIGHT_BLUE)
        bosses_rect = bosses_text.get_rect(center=(WIDTH // 2, HEIGHT // 6 + 175))
        self.screen.blit(bosses_text, bosses_rect)
        
        box_rect = pygame.Rect(WIDTH // 2 - 280, HEIGHT // 2 - 120, 560, 320)
        pygame.draw.rect(self.screen, (0, 0, 80), box_rect)
        pygame.draw.rect(self.screen, CYAN, box_rect, 3)
        
        instructions = [
            "CONTROLS:",
            "WASD/Arrows - Move  |  SPACE - Shoot  |  P - Pause",
            "R - Restart         |  O - Quit",
            "",
            "POWER-UPS:",
            "+ Health    Shield(Cyan)    >>> Rapid Fire(Yellow)",
            ">>> Spread(Orange)    * Bomb(Red)    <3 Extra Life(Pink)",
            "",
            "Tips: Collect power-ups • Use combo for style",
            f"Survive {7} boss rounds to achieve VICTORY!"
        ]
        
        y = HEIGHT // 2 - 100
        for i, line in enumerate(instructions):
            if line == "":
                y += 8
                continue
            if line in ["CONTROLS:", "POWER-UPS:"]:
                text = self.small_font.render(line, True, YELLOW)
            elif i >= len(instructions)-2:
                text = self.tiny_font.render(line, True, LIGHT_BLUE)
            else:
                text = self.micro_font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 28 if line in ["CONTROLS:", "POWER-UPS:"] else 22
        
        button_rect = pygame.Rect(WIDTH // 2 - 140, HEIGHT - 130, 280, 75)
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, (100, 255, 100), button_rect, border_radius=10)
        else:
            pygame.draw.rect(self.screen, GREEN, button_rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, button_rect, 4, border_radius=10)
        start_text = self.font.render("START MISSION", True, BLACK)
        start_rect = start_text.get_rect(center=button_rect.center)
        self.screen.blit(start_text, start_rect)
        self.start_button = button_rect
    
    def draw_hud(self):
        bar_width = 240
        pygame.draw.rect(self.screen, (60, 0, 0), (18, HEIGHT - 80, bar_width, 32))
        hp_width = bar_width * (self.spaceship.hp / self.spaceship.max_hp)
        pygame.draw.rect(self.screen, GREEN, (18, HEIGHT - 80, hp_width, 32))
        pygame.draw.rect(self.screen, WHITE, (18, HEIGHT - 80, bar_width, 32), 2)
        hp_text = self.tiny_font.render(f"HP {int(self.spaceship.hp)}", True, WHITE)
        self.screen.blit(hp_text, (25, HEIGHT - 75))
        
        if self.spaceship.shield > 0:
            pygame.draw.rect(self.screen, (0, 40, 60), (18, HEIGHT - 120, bar_width, 32))
            shield_width = bar_width * (self.spaceship.shield / self.spaceship.shield_max)
            pygame.draw.rect(self.screen, CYAN, (18, HEIGHT - 120, shield_width, 32))
            pygame.draw.rect(self.screen, WHITE, (18, HEIGHT - 120, bar_width, 32), 2)
            shield_text = self.tiny_font.render(f"SHIELD {int(self.spaceship.shield)}", True, WHITE)
            self.screen.blit(shield_text, (25, HEIGHT - 115))
        
        lives_text = self.small_font.render(f"LIVES: {self.spaceship.lives}", True, PINK)
        self.screen.blit(lives_text, (18, HEIGHT - 160))
        
        if self.enemy and self.enemy.hp > 0:
            bar_x = WIDTH // 2 - 170
            pygame.draw.rect(self.screen, (80, 0, 0), (bar_x, 15, 340, 36))
            enemy_hp_width = 340 * (self.enemy.hp / self.enemy.max_hp)
            pygame.draw.rect(self.screen, (255, 60, 0), (bar_x, 15, enemy_hp_width, 36))
            pygame.draw.rect(self.screen, WHITE, (bar_x, 15, 340, 36), 3)
            boss_text = self.small_font.render(f"BOSS | ROUND {self.round}", True, WHITE)
            boss_rect = boss_text.get_rect(center=(WIDTH // 2, 33))
            self.screen.blit(boss_text, boss_rect)
        
        score_text = self.small_font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - 200, 18))
        round_text = self.small_font.render(f"WAVE {self.round}/7", True, WHITE)
        self.screen.blit(round_text, (WIDTH - 200, 55))
        
        y_off = HEIGHT - 200
        if self.spaceship.rapid_fire > 0:
            rapid_text = self.tiny_font.render(f"RAPID {self.spaceship.rapid_fire // 60 + 1}s", True, YELLOW)
            self.screen.blit(rapid_text, (18, y_off))
            y_off -= 28
        if self.spaceship.spread_shot > 0:
            spread_text = self.tiny_font.render(f"SPREAD {self.spaceship.spread_shot // 60 + 1}s", True, ORANGE)
            self.screen.blit(spread_text, (18, y_off))
    
    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        pause_text = self.font_huge.render("PAUSED", True, CYAN)
        pause_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        self.screen.blit(pause_text, pause_rect)
        cont_text = self.font.render("[P] RESUME", True, WHITE)
        cont_rect = cont_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        self.screen.blit(cont_text, cont_rect)
        menu_text = self.small_font.render("[R] RESTART   |   [O] QUIT", True, LIGHT_BLUE)
        menu_rect = menu_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 85))
        self.screen.blit(menu_text, menu_rect)
    
    def draw_end_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if self.game_state == "victory":
            text = self.font_huge.render("VICTORY!", True, YELLOW)
            subtext = self.font.render("ALL BOSSES DEFEATED!", True, WHITE)
        else:
            text = self.font_huge.render("GAME OVER", True, RED)
            subtext = self.font.render("MISSION FAILED", True, WHITE)
        
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        subtext_rect = subtext.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(text, text_rect)
        self.screen.blit(subtext, subtext_rect)
        
        score_text = self.font.render(f"FINAL SCORE: {self.score}", True, CYAN)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        self.screen.blit(score_text, score_rect)
        
        hs_text = self.small_font.render(f"HIGH SCORE: {self.config.progression.get('high_score', 0)}", True, WHITE)
        hs_rect = hs_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 95))
        self.screen.blit(hs_text, hs_rect)
        
        bosses_text = self.tiny_font.render(f"BOSSES DEFEATED: {self.config.progression.get('bosses_defeated', 0)}", True, LIGHT_BLUE)
        bosses_rect = bosses_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 135))
        self.screen.blit(bosses_text, bosses_rect)
        
        restart_text = self.small_font.render("[R] RESTART   |   [O] QUIT TO MENU", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 190))
        self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
                        if self.game_state in ["game_over", "victory", "paused"]:
                            self.game_state = "landing"
                            self.reset_game()
                        else:
                            running = False
                    elif event.key == pygame.K_r:
                        self.config.save()
                        self.reset_game()
                        self.game_state = "playing"
                    elif event.key == pygame.K_p:
                        if self.game_state == "playing":
                            self.game_state = "paused"
                        elif self.game_state == "paused":
                            self.game_state = "playing"
                    elif event.key == pygame.K_SPACE and self.game_state == "playing":
                        lasers = self.spaceship.shoot()
                        for laser in lasers:
                            self.player_lasers.append(laser)
                elif event.type == pygame.MOUSEBUTTONDOWN and self.game_state == "landing":
                    mouse_pos = pygame.mouse.get_pos()
                    if hasattr(self, 'start_button') and self.start_button.collidepoint(mouse_pos):
                        self.game_state = "playing"
                        self.reset_game()
                        self.game_state = "playing"
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        self.config.save()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = EnhancedGame()
    game.run()
