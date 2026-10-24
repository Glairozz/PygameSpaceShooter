"""Enhanced Pygame Space Shooter - Dragon Roaster"""
import pygame
import random
import math
import sys
import time
from pathlib import Path

from config import *

pygame.init()
pygame.mixer.init()

class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=30, size=None):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-6, 6)
        self.vy = vy if vy is not None else random.uniform(-6, 6)
        self.life = life
        self.max_life = life
        self.size = size if size is not None else random.randint(1, 3)
        self.gravity = 0.1
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.life -= 1
        return self.life > 0
    
    def draw(self, screen):
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(self.size * (self.life / self.max_life)))
        # Create surface with alpha
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, alpha)
        pygame.draw.circle(surf, color_with_alpha, (size, size), size)
        screen.blit(surf, (int(self.x - size), int(self.y - size)))


class Star:
    def __init__(self, layer=0):
        self.layer = layer  # Parallax layer
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.base_speed = 0.5 + layer * 0.5
        self.speed = self.base_speed
        if layer == 0:
            self.size = random.choice([1])
            self.color = random.choice([WHITE, LIGHT_BLUE])
        elif layer == 1:
            self.size = random.choice([1, 2])
            self.color = random.choice([WHITE, CYAN])
        else:
            self.size = random.choice([2])
            self.color = YELLOW
    
    def update(self, dt=1.0):
        self.y += self.speed * dt * 60 / FPS  # Normalize by FPS
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)


class PowerUp:
    def __init__(self, x, y, power_type=None):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.speed = 2
        if power_type is None:
            self.type = random.choice(['health', 'shield', 'rapid', 'spread', 'bomb'])
        else:
            self.type = power_type
        self.timer = 0
        self.active = True
        
    def update(self):
        self.y += self.speed
        self.timer += 1
        return self.y < HEIGHT + 50
    
    def draw(self, screen):
        # Pulsing effect
        pulse = abs(math.sin(self.timer * 0.1)) * 3 + 25
        rect = pygame.Rect(self.x - (pulse - 25)//2, self.y - (pulse - 25)//2, pulse, pulse)
        
        if self.type == 'health':
            color = GREEN
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
            # Plus sign
            pygame.draw.line(screen, BLACK, (self.x + 12, self.y + 5), (self.x + 12, self.y + 20), 4)
            pygame.draw.line(screen, BLACK, (self.x + 5, self.y + 12), (self.x + 20, self.y + 12), 4)
        elif self.type == 'shield':
            color = CYAN
            pygame.draw.circle(screen, color, (self.x + 12, self.y + 12), 12, 3)
            pygame.draw.circle(screen, LIGHT_BLUE, (self.x + 12, self.y + 12), 8)
        elif self.type == 'rapid':
            color = YELLOW
            pygame.draw.polygon(screen, color, [(self.x+12, self.y), (self.x+20, self.y+20), (self.x+12, self.y+15), (self.x+4, self.y+20)])
        elif self.type == 'spread':
            color = ORANGE
            pygame.draw.polygon(screen, color, [(self.x+12, self.y), (self.x+5, self.y+18), (self.x+12, self.y+12), (self.x+19, self.y+18)])
        elif self.type == 'bomb':
            color = RED
            pygame.draw.circle(screen, color, (self.x + 12, self.y + 12), 10)
            pygame.draw.circle(screen, WHITE, (self.x + 12, self.y + 8), 2)
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Spaceship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 40
        self.speed = 6
        self.hp = 100
        self.max_hp = 100
        self.last_shot = 0
        self.shoot_delay = 200  # Faster shooting
        self.shield = 0
        self.shield_max = 100
        self.rapid_fire = 0  # Timer
        self.spread_shot = 0
        self.invulnerable = 0
        self.lives = 3
        
    def move(self, keys, dt=1.0):
        speed = self.speed * dt * 60 / FPS
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(0, self.x - speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(WIDTH - self.width, self.x + speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(HEIGHT // 3, self.y - speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(HEIGHT - self.height - 30, self.y + speed)
    
    def shoot(self):
        current_time = pygame.time.get_ticks()
        delay = self.shoot_delay // 2 if self.rapid_fire > 0 else self.shoot_delay
        if current_time - self.last_shot > delay:
            self.last_shot = current_time
            lasers = []
            if self.spread_shot > 0:
                # Spread shot
                lasers.append(Laser(self.x + self.width // 2, self.y, -1, CYAN))
                lasers.append(Laser(self.x + self.width // 2 - 15, self.y + 5, -1, CYAN, angle=-5))
                lasers.append(Laser(self.x + self.width // 2 + 15, self.y + 5, -1, CYAN, angle=5))
            else:
                lasers.append(Laser(self.x + self.width // 2, self.y, -1, CYAN))
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
        if self.invulnerable > 0 and (self.invulnerable // 5) % 2 == 0:
            return  # Flicker when invulnerable
        
        # Shield effect
        if self.shield > 0:
            shield_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            alpha = int(100 * (self.shield / self.shield_max))
            pygame.draw.circle(shield_surf, (*CYAN, alpha), (self.width//2 + 10, self.height//2 + 10), 40, 3)
            screen.blit(shield_surf, (self.x - 10, self.y - 10))
        
        # Main spaceship body
        pygame.draw.polygon(screen, BLUE, [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width // 2, self.y + self.height - 10),
            (self.x + self.width, self.y + self.height)
        ])
        # Cockpit
        pygame.draw.ellipse(screen, CYAN, (self.x + self.width // 2 - 7, self.y + 5, 15, 10))
        # Engine glow
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 - 5, self.y + self.height - 5), 3)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 + 5, self.y + self.height - 5), 3)
        # Wings
        pygame.draw.polygon(screen, DARK_BLUE, [
            (self.x, self.y + 10),
            (self.x - 10, self.y + 10),
            (self.x + 10, self.y + self.height - 10)
        ])
        pygame.draw.polygon(screen, DARK_BLUE, [
            (self.x + self.width, self.y + 10),
            (self.x + self.width + 10, self.y + 10),
            (self.x + self.width - 10, self.y + self.height - 10)
        ])
    
    def take_damage(self, damage):
        if self.invulnerable > 0:
            return False
        if self.shield > 0:
            self.shield -= damage
            if self.shield < 0:
                self.hp += self.shield  # Damage overflow
                self.shield = 0
        else:
            self.hp -= damage
        if self.hp < 0:
            self.hp = 0
        self.invulnerable = 60  # 1 second invulnerability
        return True
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Laser:
    def __init__(self, x, y, direction, color, angle=0):
        self.x = x
        self.y = y
        self.width = 4
        self.height = 22
        self.speed = 12
        self.direction = direction
        self.color = color
        self.angle = angle
        self.damage = 25 if direction == -1 else 15
        self.trail = []
        
    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.y += self.speed * self.direction
        self.x += math.sin(math.radians(self.angle)) * 3
    
    def draw(self, screen):
        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            trail_surf = pygame.Surface((3, 3), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color, alpha), (1, 1), 1)
            screen.blit(trail_surf, (int(pos[0]), int(pos[1])))
        
        if self.direction == -1:
            # Player laser with glow
            pygame.draw.rect(screen, self.color, (self.x - 2, self.y, self.width, self.height))
            for i in range(1, 3):
                glow_surf = pygame.Surface((self.width + i*4, self.height + i*2), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*WHITE, 30 - i*10), (i, i), self.width + i*2, self.height)
                screen.blit(glow_surf, (self.x - 2 - i, self.y - i))
        else:
            pygame.draw.rect(screen, self.color, (self.x - 2, self.y, self.width, self.height))
    
    def get_rect(self):
        return pygame.Rect(self.x - 2, self.y, self.width, self.height)
    
    def is_off_screen(self):
        return self.y < -60 or self.y > HEIGHT + 60 or self.x < -50 or self.x > WIDTH + 50


class Enemy:
    def __init__(self, round_number):
        self.x = random.randint(100, WIDTH - 180)
        self.y = 60
        self.width = 80
        self.height = 60
        self.hp = 250 + round_number * 50
        self.max_hp = self.hp
        self.last_shot = 0
        self.shoot_delay = max(800, 2000 - round_number * 150)
        self.move_direction = random.choice([-1, 1])
        self.move_timer = 0
        self.round_number = round_number
        self.pattern_timer = 0
        self.attack_pattern = 0
        
    def move(self):
        self.move_timer += 1
        self.pattern_timer += 1
        
        if self.move_timer > 90:
            self.move_timer = 0
            self.move_direction *= -1
        
        # Vary movement based on pattern
        if self.pattern_timer < 200:
            self.x += self.move_direction * (3 + self.round_number * 0.3)
        elif self.pattern_timer < 400:
            self.x += math.sin(self.pattern_timer * 0.05) * 4
        else:
            if self.pattern_timer > 600:
                self.pattern_timer = 0
            self.x += self.move_direction * 2
        
        self.x = max(30, min(WIDTH - self.width - 30, self.x))
    
    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            lasers = []
            # Triple shot on higher rounds
            if self.round_number >= 3:
                lasers.append(Laser(self.x + self.width // 2, self.y + self.height, 1, RED))
                lasers.append(Laser(self.x + self.width // 4, self.y + self.height - 5, 1, RED, angle=-10))
                lasers.append(Laser(self.x + 3*self.width // 4, self.y + self.height - 5, 1, RED, angle=10))
            else:
                lasers.append(Laser(self.x + self.width // 2, self.y + self.height, 1, RED))
            return lasers
        return []
    
    def draw(self, screen):
        color_intensity = min(255, 120 + self.round_number * 25)
        enemy_color = (color_intensity, 30, 30)
        
        pygame.draw.polygon(screen, enemy_color, [
            (self.x + self.width // 2, self.y + self.height),
            (self.x, self.y),
            (self.x + self.width // 2, self.y + 10),
            (self.x + self.width, self.y)
        ])
        pygame.draw.ellipse(screen, PURPLE, (self.x + self.width // 2 - 8, self.y + self.height - 16, 16, 12))
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 - 6, self.y + 12), 4)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 + 6, self.y + 12), 4)
        
        pygame.draw.polygon(screen, (80, 0, 0), [
            (self.x, self.y + 10),
            (self.x - 12, self.y + 10),
            (self.x + 10, self.y + self.height - 10)
        ])
        pygame.draw.polygon(screen, (80, 0, 0), [
            (self.x + self.width, self.y + 10),
            (self.x + self.width + 12, self.y + 10),
            (self.x + self.width - 10, self.y + self.height - 10)
        ])
        
        # Warning lights that flash
        if (pygame.time.get_ticks() // 200) % 2 == 0:
            pygame.draw.circle(screen, RED, (self.x + 12, self.y + self.height // 2), 3)
            pygame.draw.circle(screen, RED, (self.x + self.width - 12, self.y + self.height // 2), 3)
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Asteroid:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(25, 40)
        self.width = self.size
        self.height = self.size
        self.hp = 70
        self.max_hp = 70
        self.speed = random.uniform(1.5, 3)
        self.rotation = 0
        self.rot_speed = random.uniform(-2, 2)
        
    def move(self):
        self.y += self.speed
        self.rotation += self.rot_speed
    
    def draw(self, screen):
        # Draw rotated asteroid
        points = []
        for i in range(8):
            angle = math.radians(self.rotation + i * 45)
            radius = self.size // 2 + random.randint(-2, 2)
            px = self.x + self.size // 2 + math.cos(angle) * radius
            py = self.y + self.size // 2 + math.sin(angle) * radius
            points.append((px, py))
        if len(points) >= 3:
            pygame.draw.polygon(screen, GRAY, points)
            # Craters
            pygame.draw.circle(screen, (60, 60, 60), (int(self.x + 8), int(self.y + 10)), 3)
            pygame.draw.circle(screen, (60, 60, 60), (int(self.x + self.size - 10), int(self.y + 15)), 2)
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def is_off_screen(self):
        return self.y > HEIGHT + 60


class EnhancedGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 28)
        self.tiny_font = pygame.font.Font(None, 22)
        self.reset_game()
        self.config = config
        self.stars = [Star(i % 3) for i in range(150)]
        print("Enhanced Dragon Roaster initialized!")
    
    def reset_game(self):
        self.spaceship = Spaceship(WIDTH // 2 - 30, HEIGHT - 180)
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
        self.powerup_spawn_timer = 300
        self.screen_shake = 0
        self.shake_offset = (0, 0)
        self.bomb_cooldown = 0
    
    def spawn_asteroid(self):
        if self.asteroid_spawn_timer <= 0:
            x = random.randint(30, WIDTH - 70)
            self.asteroids.append(Asteroid(x, -50))
            self.asteroid_spawn_timer = random.randint(80, 180)
        else:
            self.asteroid_spawn_timer -= 1
    
    def spawn_powerup(self):
        if self.powerup_spawn_timer <= 0:
            if random.random() < 0.15:  # 15% chance
                x = random.randint(40, WIDTH - 70)
                self.powerups.append(PowerUp(x, -30))
            self.powerup_spawn_timer = random.randint(400, 700)
        else:
            self.powerup_spawn_timer -= 1
    
    def add_particles(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
    
    def add_screen_shake(self, intensity=10):
        self.screen_shake = intensity
    
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
            return
        
        dt = self.clock.get_time() / 1000.0
        keys = pygame.key.get_pressed()
        self.spaceship.move(keys, dt)
        self.spaceship.update()
        
        for star in self.stars:
            star.update()
        
        self.spawn_asteroid()
        self.spawn_powerup()
        
        # Update lasers
        for laser in self.player_lasers[:]:
            laser.move()
            if laser.is_off_screen():
                self.player_lasers.remove(laser)
        for laser in self.enemy_lasers[:]:
            laser.move()
            if laser.is_off_screen():
                self.enemy_lasers.remove(laser)
        
        # Update asteroids
        for asteroid in self.asteroids[:]:
            asteroid.move()
            if asteroid.is_off_screen():
                self.asteroids.remove(asteroid)
        
        # Update powerups
        for powerup in self.powerups[:]:
            if not powerup.update():
                self.powerups.remove(powerup)
        
        # Update particles
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)
        
        # Enemy
        if self.enemy:
            self.enemy.move()
            enemy_lasers = self.enemy.shoot()
            for laser in enemy_lasers:
                self.enemy_lasers.append(laser)
        
        # Collisions
        self.handle_collisions()
        
        # Win/lose
        if self.spaceship.hp <= 0 and self.spaceship.lives <= 0:
            if self.game_state != "game_over":
                self.game_state = "game_over"
                self.config.progression['games_played'] += 1
                if self.score > self.config.progression['high_score']:
                    self.config.progression['high_score'] = self.score
                self.config.save()
        elif self.enemy and self.enemy.hp <= 0:
            self.score += 150 * self.round
            self.add_particles(self.enemy.x + self.enemy.width // 2,
                             self.enemy.y + self.enemy.height // 2, RED, 30)
            self.add_screen_shake(15)
            self.config.progression['bosses_defeated'] += 1
            self.next_round()
    
    def handle_collisions(self):
        # Player lasers vs enemy
        for laser in self.player_lasers[:]:
            if self.enemy and laser.get_rect().colliderect(self.enemy.get_rect()):
                self.enemy.take_damage(laser.damage)
                self.add_particles(laser.x, laser.y, CYAN, 8)
                try:
                    self.player_lasers.remove(laser)
                except ValueError:
                    pass
                continue
        
        # Player lasers vs asteroids
        for laser in self.player_lasers[:]:
            for asteroid in self.asteroids[:]:
                if laser.get_rect().colliderect(asteroid.get_rect()):
                    asteroid.take_damage(laser.damage)
                    self.add_particles(laser.x, laser.y, GRAY, 5)
                    try:
                        self.player_lasers.remove(laser)
                    except ValueError:
                        pass
                    if asteroid.hp <= 0:
                        try:
                            self.asteroids.remove(asteroid)
                        except ValueError:
                            pass
                        self.score += 30
                        self.add_particles(asteroid.x + asteroid.width // 2,
                                         asteroid.y + asteroid.height // 2, GRAY, 12)
                    break
        
        # Enemy lasers vs player
        for laser in self.enemy_lasers[:]:
            if laser.get_rect().colliderect(self.spaceship.get_rect()) and self.spaceship.invulnerable == 0:
                if self.spaceship.take_damage(laser.damage):
                    self.add_particles(laser.x, laser.y, RED, 10)
                    self.add_screen_shake(5)
                try:
                    self.enemy_lasers.remove(laser)
                except ValueError:
                    pass
        
        # Player vs asteroids
        for asteroid in self.asteroids[:]:
            if self.spaceship.get_rect().colliderect(asteroid.get_rect()) and self.spaceship.invulnerable == 0:
                if self.spaceship.take_damage(15):
                    self.add_particles(asteroid.x + asteroid.width // 2,
                                     asteroid.y + asteroid.height // 2, RED, 15)
                    self.add_screen_shake(8)
                try:
                    self.asteroids.remove(asteroid)
                except ValueError:
                    pass
        
        # Player vs powerups
        for powerup in self.powerups[:]:
            if self.spaceship.get_rect().colliderect(powerup.get_rect()):
                self.apply_powerup(powerup.type)
                try:
                    self.powerups.remove(powerup)
                except ValueError:
                    pass
    
    def apply_powerup(self, power_type):
        if power_type == 'health':
            self.spaceship.hp = min(self.spaceship.max_hp, self.spaceship.hp + 30)
        elif power_type == 'shield':
            self.spaceship.shield = min(self.spaceship.shield_max, self.spaceship.shield + 50)
        elif power_type == 'rapid':
            self.spaceship.rapid_fire = 600  # 10 seconds
        elif power_type == 'spread':
            self.spaceship.spread_shot = 600
        elif power_type == 'bomb':
            # Clear enemy lasers
            self.enemy_lasers.clear()
            self.add_particles(WIDTH // 2, HEIGHT // 2, YELLOW, 40)
            self.add_screen_shake(20)
    
    def next_round(self):
        self.round += 1
        if self.round > 6:
            self.game_state = "victory"
            if self.score > self.config.progression['high_score']:
                self.config.progression['high_score'] = self.score
            self.config.save()
        else:
            self.enemy = Enemy(self.round)
            self.player_lasers.clear()
            self.enemy_lasers.clear()
            self.asteroids.clear()
            self.powerups.clear()
    
    def draw(self):
        # Apply screen shake
        offset_x, offset_y = self.shake_offset
        self.screen.fill(BLACK)
        
        # Draw stars
        for star in self.stars:
            star.draw(self.screen)
        
        if self.game_state == "landing":
            self.draw_landing()
        elif self.game_state == "playing" or self.game_state == "paused":
            # Draw game elements
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
            if self.enemy:
                self.enemy.draw(self.screen)
            self.spaceship.draw(self.screen)
            self.draw_hud()
            if self.game_state == "paused":
                self.draw_pause()
        elif self.game_state in ["game_over", "victory"]:
            self.draw_end_screen()
        
        pygame.display.flip()
    
    def draw_landing(self):
        title = self.font_large.render("DRAGON ROASTER", True, YELLOW)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 5))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font.render("Enhanced Space Battle", True, CYAN)
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 5 + 80))
        self.screen.blit(subtitle, subtitle_rect)
        
        # High score
        hs_text = self.small_font.render(f"High Score: {self.config.progression['high_score']}", True, WHITE)
        hs_rect = hs_text.get_rect(center=(WIDTH // 2, HEIGHT // 5 + 130))
        self.screen.blit(hs_text, hs_rect)
        
        # Instructions
        box_rect = pygame.Rect(WIDTH // 2 - 250, HEIGHT // 2 - 100, 500, 280)
        pygame.draw.rect(self.screen, DARK_BLUE, box_rect, 3)
        pygame.draw.rect(self.screen, BLUE, box_rect, 1)
        
        instructions = [
            "CONTROLS:",
            "WASD/Arrow Keys - Move",
            "SPACE - Shoot",
            "P - Pause",
            "R - Restart | O - Quit",
            "",
            "POWER-UPS:",
            "Green + = Health  Red Circle = Bomb",
            "Cyan Shield    Yellow Triangle = Rapid Fire",
            "Orange Spread",
            "",
            f"Defeat {6} boss rounds to win!"
        ]
        
        y = HEIGHT // 2 - 80
        for i, line in enumerate(instructions):
            if line == "":
                y += 5
                continue
            if i == 0 or line in ["POWER-UPS:", "CONTROLS:"]:
                text = self.small_font.render(line, True, YELLOW)
            else:
                text = self.tiny_font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 24 if (i == 0 or line in ["POWER-UPS:", "CONTROLS:"]) else 20
        
        # Start button
        button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 150, 240, 70)
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, LIGHT_BLUE, button_rect)
        else:
            pygame.draw.rect(self.screen, GREEN, button_rect)
        pygame.draw.rect(self.screen, WHITE, button_rect, 3)
        start_text = self.font.render("START GAME", True, BLACK)
        start_rect = start_text.get_rect(center=button_rect.center)
        self.screen.blit(start_text, start_rect)
        self.start_button = button_rect
    
    def draw_hud(self):
        # HP Bar
        bar_width = 220
        pygame.draw.rect(self.screen, RED, (15, HEIGHT - 75, bar_width, 28))
        hp_width = bar_width * (self.spaceship.hp / self.spaceship.max_hp)
        pygame.draw.rect(self.screen, GREEN, (15, HEIGHT - 75, hp_width, 28))
        pygame.draw.rect(self.screen, WHITE, (15, HEIGHT - 75, bar_width, 28), 2)
        hp_text = self.tiny_font.render(f"HP: {int(self.spaceship.hp)}/{self.spaceship.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (20, HEIGHT - 71))
        
        # Shield
        if self.spaceship.shield > 0:
            pygame.draw.rect(self.screen, (50, 50, 50), (15, HEIGHT - 110, bar_width, 28))
            shield_width = bar_width * (self.spaceship.shield / self.spaceship.shield_max)
            pygame.draw.rect(self.screen, CYAN, (15, HEIGHT - 110, shield_width, 28))
            pygame.draw.rect(self.screen, WHITE, (15, HEIGHT - 110, bar_width, 28), 2)
            shield_text = self.tiny_font.render(f"SHIELD: {int(self.spaceship.shield)}", True, WHITE)
            self.screen.blit(shield_text, (20, HEIGHT - 106))
        
        # Enemy HP
        if self.enemy and self.enemy.hp > 0:
            bar_x = WIDTH // 2 - 150
            pygame.draw.rect(self.screen, RED, (bar_x, 20, 300, 32))
            enemy_hp_width = 300 * (self.enemy.hp / self.enemy.max_hp)
            pygame.draw.rect(self.screen, ORANGE, (bar_x, 20, enemy_hp_width, 32))
            pygame.draw.rect(self.screen, WHITE, (bar_x, 20, 300, 32), 2)
            boss_text = self.small_font.render(f"BOSS - Round {self.round}", True, WHITE)
            boss_rect = boss_text.get_rect(center=(WIDTH // 2, 36))
            self.screen.blit(boss_text, boss_rect)
        
        # Score and Round
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH - 180, 20))
        round_text = self.small_font.render(f"Round: {self.round}/6", True, WHITE)
        self.screen.blit(round_text, (WIDTH - 180, 55))
        
        # Power-up indicators
        y_off = HEIGHT - 150
        if self.spaceship.rapid_fire > 0:
            rapid_text = self.tiny_font.render(f"RAPID: {self.spaceship.rapid_fire // 60 + 1}s", True, YELLOW)
            self.screen.blit(rapid_text, (15, y_off))
            y_off -= 25
        if self.spaceship.spread_shot > 0:
            spread_text = self.tiny_font.render(f"SPREAD: {self.spaceship.spread_shot // 60 + 1}s", True, ORANGE)
            self.screen.blit(spread_text, (15, y_off))
    
    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        pause_text = self.font_large.render("PAUSED", True, CYAN)
        pause_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(pause_text, pause_rect)
        cont_text = self.font.render("Press P to Resume", True, WHITE)
        cont_rect = cont_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        self.screen.blit(cont_text, cont_rect)
        menu_text = self.small_font.render("R: Restart | O: Quit", True, WHITE)
        menu_rect = menu_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90))
        self.screen.blit(menu_text, menu_rect)
    
    def draw_end_screen(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if self.game_state == "victory":
            text = self.font_large.render("VICTORY!", True, YELLOW)
            subtext = self.font.render("All Bosses Defeated!", True, WHITE)
        else:
            text = self.font_large.render("GAME OVER", True, RED)
            subtext = self.font.render("Try Again!", True, WHITE)
        
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
        subtext_rect = subtext.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text, text_rect)
        self.screen.blit(subtext, subtext_rect)
        
        score_text = self.font.render(f"Final Score: {self.score}", True, CYAN)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(score_text, score_rect)
        
        hs_text = self.small_font.render(f"High Score: {self.config.progression['high_score']}", True, WHITE)
        hs_rect = hs_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110))
        self.screen.blit(hs_text, hs_rect)
        
        restart_text = self.small_font.render("Press R to Restart or O to Quit", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 170))
        self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
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
