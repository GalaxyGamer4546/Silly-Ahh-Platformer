import pygame
import asyncio  # Required for browser/pygbag
import sys

# --- Configuration & Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Physics
GRAVITY = 0.8
WALK_SPEED = 5
JUMP_FORCE = -16
DASH_SPEED = 20
DASH_DURATION = 10 
DASH_COOLDOWN = 60 

# Colors
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (0, 255, 128)
COLOR_PLAYER_COOLDOWN = (100, 100, 100)
COLOR_PLATFORM = (120, 120, 120)
COLOR_ENEMY = (255, 50, 50)

# --- Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 48))
        self.image.fill(COLOR_PLAYER)
        self.rect = self.image.get_rect(midbottom=(100, 500))
        
        self.velocity = pygame.math.Vector2(0, 0)
        self.is_on_ground = False
        self.can_double_jump = False
        
        # Dash logic
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_direction = 1

    def get_input(self):
        keys = pygame.key.get_pressed()
        if not self.dashing:
            if keys[pygame.K_LEFT]:
                self.velocity.x = -WALK_SPEED
                self.dash_direction = -1
            elif keys[pygame.K_RIGHT]:
                self.velocity.x = WALK_SPEED
                self.dash_direction = 1
            else:
                self.velocity.x = 0

    def jump(self):
        if self.is_on_ground:
            self.velocity.y = JUMP_FORCE
            self.is_on_ground = False
            self.can_double_jump = True
        elif self.can_double_jump:
            self.velocity.y = JUMP_FORCE
            self.can_double_jump = False

    def handle_dash(self):
        keys = pygame.key.get_pressed()
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1
            self.image.fill(COLOR_PLAYER_COOLDOWN)
        else:
            self.image.fill(COLOR_PLAYER)

        if keys[pygame.K_LSHIFT] and not self.dashing and self.dash_cooldown_timer == 0:
            self.dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN

        if self.dashing:
            self.velocity.x = self.dash_direction * DASH_SPEED
            self.velocity.y = 0
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False

    def apply_gravity(self):
        if not self.dashing:
            self.velocity.y += GRAVITY
            self.rect.y += self.velocity.y

    def check_collisions(self, platforms, direction):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if direction == 'horizontal':
            for wall in hits:
                if self.velocity.x > 0: self.rect.right = wall.rect.left
                if self.velocity.x < 0: self.rect.left = wall.rect.right
        
        if direction == 'vertical':
            for plat in hits:
                if self.velocity.y > 0:
                    self.rect.bottom = plat.rect.top
                    self.velocity.y = 0
                    self.is_on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = plat.rect.bottom
                    self.velocity.y = 0

    def reset(self):
        self.rect.midbottom = (100, 500)
        self.velocity = pygame.math.Vector2(0, 0)

    def update(self, platforms):
        self.get_input()
        self.handle_dash()
        self.rect.x += self.velocity.x
        self.check_collisions(platforms, 'horizontal')
        self.apply_gravity()
        self.is_on_ground = False 
        self.check_collisions(platforms, 'vertical')

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, distance):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill(COLOR_ENEMY)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.distance = distance
        self.speed = 3
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction
        if abs(self.rect.x - self.start_x) >= self.distance:
            self.direction *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(COLOR_PLATFORM)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Main Async Loop ---

async def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Browser Platformer")
    clock = pygame.time.Clock()

    # Create Groups
    player = Player()
    player_group = pygame.sprite.GroupSingle(player)
    
    platforms = pygame.sprite.Group()
    platforms.add(Platform(0, 550, 800, 50))
    platforms.add(Platform(200, 420, 150, 20))
    platforms.add(Platform(450, 320, 200, 20))
    platforms.add(Platform(100, 200, 100, 20))

    enemies = pygame.sprite.Group()
    enemies.add(Enemy(450, 288, 150))

    while True:
        # Handle Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()

        # Update
        player_group.update(platforms)
        enemies.update()

        # Collision with Enemy
        if pygame.sprite.spritecollide(player, enemies, False):
            player.reset()

        # Draw
        screen.fill(COLOR_BG)
        platforms.draw(screen)
        enemies.draw(screen)
        player_group.draw(screen)

        pygame.display.flip()
        
        # --- Browser Compatibility Specifics ---
        clock.tick(FPS)
        await asyncio.sleep(0) # Yield control back to the browser

# Execute
if __name__ == "__main__":
    asyncio.run(main())