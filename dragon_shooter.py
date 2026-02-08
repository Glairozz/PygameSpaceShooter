import pygame
import random
import math
import sys

pygame.init()

WIDTH, HEIGHT = 700, 1000
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
DARK_BLUE = (0, 0, 139)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)

class Spaceship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 40
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.last_shot = 0
        self.shoot_delay = 250
        
    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(0, self.x - self.speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(WIDTH - self.width, self.x + self.speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(HEIGHT // 2, self.y - self.speed)  # Can't go too high
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(HEIGHT - self.height - 20, self.y + self.speed)  # Can't go too low
    
    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            return Laser(self.x + self.width // 2, self.y, -1, CYAN)  # Shoot upwards
        return None
    
    def draw(self, screen):
        # Main spaceship body (pointing upwards)
        pygame.draw.polygon(screen, BLUE, [
            (self.x + self.width // 2, self.y),  # Tip (top)
            (self.x, self.y + self.height),  # Bottom left
            (self.x + self.width // 2, self.y + self.height - 10),  # Middle bottom
            (self.x + self.width, self.y + self.height)  # Bottom right
        ])
        # Cockpit (top)
        pygame.draw.ellipse(screen, CYAN, (self.x + self.width // 2 - 7, self.y + 5, 15, 10))
        # Engine glow (bottom)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 - 5, self.y + self.height - 5), 3)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 + 5, self.y + self.height - 5), 3)
        # Wings (side)
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
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Laser:
    def __init__(self, x, y, direction, color):
        self.x = x
        self.y = y
        self.width = 3
        self.height = 20
        self.speed = 10
        self.direction = direction  # -1 for up, 1 for down
        self.color = color
        self.damage = 20 if direction == -1 else 10  # Player damage for up, enemy damage for down
        
    def move(self):
        self.y += self.speed * self.direction
        
    def draw(self, screen):
        # Laser beam
        if self.direction == -1:  # Upward laser (player)
            pygame.draw.rect(screen, self.color, (self.x - 1, self.y, self.width, self.height))
            # Laser glow (simplified)
            for i in range(1, 3):
                glow_width = self.width + i * 2
                glow_height = self.height + i * 2
                glow_rect = (self.x - 1 - i, self.y - i, glow_width, glow_height)
                if i == 1:
                    pygame.draw.rect(screen, WHITE, glow_rect, 1)
        else:  # Downward laser (enemy)
            pygame.draw.rect(screen, self.color, (self.x - 1, self.y, self.width, self.height))
            # Laser glow (simplified)
            for i in range(1, 3):
                glow_width = self.width + i * 2
                glow_height = self.height + i * 2
                glow_rect = (self.x - 1 - i, self.y - i, glow_width, glow_height)
                if i == 1:
                    pygame.draw.rect(screen, WHITE, glow_rect, 1)
            
    def get_rect(self):
        return pygame.Rect(self.x - 1, self.y, self.width, self.height)
    
    def is_off_screen(self):
        return self.y < -50 or self.y > HEIGHT + 50

class Enemy:
    def __init__(self, round_number):
        self.x = WIDTH // 2 - 40
        self.y = 50
        self.width = 80
        self.height = 60
        self.hp = 200 * round_number
        self.max_hp = self.hp
        self.last_shot = 0
        self.shoot_delay = 2000 - (round_number * 200)  # Faster shooting in higher rounds
        self.move_direction = 1
        self.move_timer = 0
        self.round_number = round_number
        
    def move(self):
        self.move_timer += 1
        if self.move_timer > 60:
            self.move_timer = 0
            self.move_direction *= -1
            
        self.x += self.move_direction * 3
        self.x = max(50, min(WIDTH - self.width - 50, self.x))
        
    def shoot(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot > self.shoot_delay:
            self.last_shot = current_time
            return Laser(self.x + self.width // 2, self.y + self.height, 1, RED)  # Shoot downwards
        return None
    
    def draw(self, screen):
        # Enemy spaceship body (facing down)
        color_intensity = min(255, 100 + self.round_number * 30)
        enemy_color = (color_intensity, 0, 0)
        
        pygame.draw.polygon(screen, enemy_color, [
            (self.x + self.width // 2, self.y + self.height),  # Tip (bottom)
            (self.x, self.y),  # Top left
            (self.x + self.width // 2, self.y + 10),  # Middle top
            (self.x + self.width, self.y)  # Top right
        ])
        # Enemy cockpit
        pygame.draw.ellipse(screen, PURPLE, (self.x + self.width // 2 - 7, self.y + self.height - 15, 15, 10))
        # Enemy engine glow (top)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 - 5, self.y + 10), 3)
        pygame.draw.circle(screen, YELLOW, (self.x + self.width // 2 + 5, self.y + 10), 3)
        # Enemy wings
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
        # Warning lights
        pygame.draw.circle(screen, RED, (self.x + 10, self.y + self.height // 2), 2)
        pygame.draw.circle(screen, RED, (self.x + self.width - 10, self.y + self.height // 2), 2)
        
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
        self.width = 30
        self.height = 30
        self.hp = 60
        self.max_hp = 60
        self.speed = 2
        
    def move(self):
        self.y += self.speed  # Fall downwards
        
    def draw(self, screen):
        # Draw as space asteroid/debris
        pygame.draw.circle(screen, GRAY, (self.x + self.width // 2, self.y + self.height // 2), 
                         self.width // 2)
        # Asteroid craters
        pygame.draw.circle(screen, BLACK, (self.x + 8, self.y + 8), 3)
        pygame.draw.circle(screen, BLACK, (self.x + 20, self.y + 15), 2)
        pygame.draw.circle(screen, BLACK, (self.x + 12, self.y + 22), 3)
        # Add some detail lines
        pygame.draw.line(screen, BLACK, (self.x + 5, self.y + 5), (self.x + 25, self.y + 20), 1)
        pygame.draw.line(screen, BLACK, (self.x + 10, self.y + 25), (self.x + 20, self.y + 10), 1)
        
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0
            
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def is_off_screen(self):
        return self.y > HEIGHT + 50  # Off bottom of screen

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Spaceship Shooter - Space Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.reset_game()
        print("Spaceship Shooter initialized successfully!")
        print("Controls: WASD/Arrows to move, Space to shoot, P to pause, R to restart, O to quit")
        
    def reset_game(self):
        self.spaceship = Spaceship(50, HEIGHT - 150)
        self.player_lasers = []
        self.enemy_lasers = []
        self.asteroids = []
        self.round = 1
        self.enemy = Enemy(self.round)
        self.score = 0
        self.game_state = "playing"  # playing, paused, game_over, victory
        self.asteroid_spawn_timer = 0
        self.particles = []
        
    def spawn_asteroid(self):
        if self.asteroid_spawn_timer <= 0:
            x = random.randint(50, WIDTH - 50)
            self.asteroids.append(Asteroid(x, -30))  # Spawn from top
            self.asteroid_spawn_timer = random.randint(120, 240)
        else:
            self.asteroid_spawn_timer -= 1
            
    def create_particles(self, x, y, color, count=10):
        for _ in range(count):
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'life': 30,
                'color': color
            }
            self.particles.append(particle)
            
    def update_particles(self):
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.particles.remove(particle)
                
    def draw_particles(self):
        for particle in self.particles:
            size = max(1, particle['life'] // 10)
            pygame.draw.circle(self.screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), size)
    
    def handle_collisions(self):
        # Player lasers vs Enemy
        for laser in self.player_lasers[:]:
            if laser.get_rect().colliderect(self.enemy.get_rect()):
                self.enemy.take_damage(laser.damage)
                self.create_particles(laser.x, laser.y, CYAN, 5)
                self.player_lasers.remove(laser)
                
        # Player lasers vs Asteroids
        for laser in self.player_lasers[:]:
            for asteroid in self.asteroids[:]:
                if laser.get_rect().colliderect(asteroid.get_rect()):
                    asteroid.take_damage(laser.damage)
                    self.create_particles(laser.x, laser.y, GRAY, 3)
                    self.player_lasers.remove(laser)
                    if asteroid.hp <= 0:
                        self.asteroids.remove(asteroid)
                        self.score += 50
                        self.create_particles(asteroid.x + asteroid.width // 2, 
                                           asteroid.y + asteroid.height // 2, GRAY, 10)
                    break
                    
        # Enemy lasers vs Player
        for laser in self.enemy_lasers[:]:
            if laser.get_rect().colliderect(self.spaceship.get_rect()):
                self.spaceship.take_damage(laser.damage)
                self.create_particles(laser.x, laser.y, RED, 5)
                self.enemy_lasers.remove(laser)
                
        # Spaceship vs Asteroids
        for asteroid in self.asteroids[:]:
            if self.spaceship.get_rect().colliderect(asteroid.get_rect()):
                self.spaceship.take_damage(10)
                self.create_particles(asteroid.x + asteroid.width // 2, 
                                   asteroid.y + asteroid.height // 2, RED, 8)
                self.asteroids.remove(asteroid)
                
    def next_round(self):
        self.round += 1
        if self.round > 5:
            self.game_state = "victory"
        else:
            self.enemy = Enemy(self.round)
            self.player_lasers.clear()
            self.enemy_lasers.clear()
            self.asteroids.clear()
            
    def draw_ui(self):
        # HP bars
        # Spaceship HP (bottom left)
        pygame.draw.rect(self.screen, RED, (10, HEIGHT - 60, 200, 25))
        pygame.draw.rect(self.screen, GREEN, 
                        (10, HEIGHT - 60, 200 * (self.spaceship.hp / self.spaceship.max_hp), 25))
        hp_text = self.small_font.render(f"Ship HP: {self.spaceship.hp}/{self.spaceship.max_hp}", 
                                        True, WHITE)
        self.screen.blit(hp_text, (15, HEIGHT - 57))
        
        # Enemy HP (top)
        if self.enemy:
            pygame.draw.rect(self.screen, RED, (WIDTH // 2 - 100, 30, 200, 25))
            pygame.draw.rect(self.screen, RED, 
                           (WIDTH // 2 - 100, 30, 200 * (self.enemy.hp / self.enemy.max_hp), 25))
            enemy_hp_text = self.small_font.render(
                f"Boss HP: {self.enemy.hp}/{self.enemy.max_hp}", True, WHITE)
            self.screen.blit(enemy_hp_text, (WIDTH // 2 - 95, 33))
            
        # Round and Score (top)
        round_text = self.font.render(f"Round: {self.round}/5", True, WHITE)
        self.screen.blit(round_text, (WIDTH // 2 - 60, 70))
        
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (WIDTH // 2 - 40, 100))
        
        # Controls (bottom right)
        controls = [
            "WASD: Move",
            "Space: Fire",
            "P: Pause",
            "R: Restart",
            "O: Quit"
        ]
        x_offset = WIDTH - 150
        y_offset = HEIGHT - 120
        for control in controls:
            text = self.small_font.render(control, True, WHITE)
            self.screen.blit(text, (x_offset, y_offset))
            y_offset += 22
            
    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if self.game_state == "victory":
            text = self.font.render("VICTORY! You defeated all bosses!", True, YELLOW)
            subtext = self.small_font.render(f"Final Score: {self.score}", True, WHITE)
        else:
            text = self.font.render("GAME OVER", True, RED)
            subtext = self.small_font.render(f"Final Score: {self.score}", True, WHITE)
            
        restart_text = self.small_font.render("Press R to Restart or O to Quit", True, WHITE)
        
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        subtext_rect = subtext.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        
        self.screen.blit(text, text_rect)
        self.screen.blit(subtext, subtext_rect)
        self.screen.blit(restart_text, restart_rect)
        
    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        text = self.font.render("PAUSED", True, CYAN)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text, text_rect)
        
        subtext = self.small_font.render("Press P to continue", True, WHITE)
        subtext_rect = subtext.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
        self.screen.blit(subtext, subtext_rect)
        
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
                        running = False
                    elif event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_p:
                        if self.game_state == "playing":
                            self.game_state = "paused"
                        elif self.game_state == "paused":
                            self.game_state = "playing"
                    elif event.key == pygame.K_SPACE and self.game_state == "playing":
                        laser = self.spaceship.shoot()
                        if laser:
                            self.player_lasers.append(laser)
                            
            if self.game_state == "playing":
                keys = pygame.key.get_pressed()
                self.spaceship.move(keys)
                
                # Spawn asteroids
                self.spawn_asteroid()
                
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
                        
                # Enemy shooting
                if self.enemy:
                    self.enemy.move()
                    enemy_laser = self.enemy.shoot()
                    if enemy_laser:
                        self.enemy_lasers.append(enemy_laser)
                        
                # Handle collisions
                self.handle_collisions()
                
                # Update particles
                self.update_particles()
                
                # Check win/lose conditions
                if self.spaceship.hp <= 0:
                    self.game_state = "game_over"
                elif self.enemy.hp <= 0:
                    self.score += 100 * self.round
                    self.create_particles(self.enemy.x + self.enemy.width // 2,
                                        self.enemy.y + self.enemy.height // 2, RED, 20)
                    self.next_round()
                    
            # Drawing
            self.screen.fill(BLACK)
            
            # Draw background stars
            random.seed(42)  # Fixed seed for consistent stars
            for _ in range(100):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                size = random.choice([1, 1, 2])  # Mix of star sizes
                brightness = random.choice([WHITE, LIGHT_BLUE, WHITE])
                pygame.draw.circle(self.screen, brightness, (x, y), size)
            random.seed()  # Reset seed
            
            if self.game_state != "game_over" and self.game_state != "victory":
                self.spaceship.draw(self.screen)
                if self.enemy:
                    self.enemy.draw(self.screen)
                    
                for laser in self.player_lasers:
                    laser.draw(self.screen)
                for laser in self.enemy_lasers:
                    laser.draw(self.screen)
                    
                for asteroid in self.asteroids:
                    asteroid.draw(self.screen)
                    
            self.draw_particles()
            self.draw_ui()
            
            if self.game_state == "paused":
                self.draw_pause()
            elif self.game_state in ["game_over", "victory"]:
                self.draw_game_over()
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()