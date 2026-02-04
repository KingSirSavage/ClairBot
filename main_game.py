class Enemy(pygame.sprite.Sprite):
    def __init__(self, color, x, y, size, speed, player, world):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.player = player
        self.world = world

    def update(self):
        # Basic AI: Move towards the player
        dx, dy = 0, 0
        if self.rect.centerx < self.player.rect.centerx:
            dx = self.speed
        elif self.rect.centerx > self.player.rect.centerx:
            dx = -self.speed

        if self.rect.centery < self.player.rect.centery:
            dy = self.speed
        elif self.rect.centery > self.player.rect.centery:
            dy = -self.speed

        # Attempt to move and check for collisions with world tiles
        self.move_and_collide(dx, dy)

    def move_and_collide(self, dx, dy):
        # Move horizontally
        self.rect.x += dx
        # Check for tile collisions after horizontal movement
        collided_tile = self.world.get_tile_at_position(self.rect.centerx, self.rect.centery)
        if collided_tile and collided_tile.is_destructible and not collided_tile.is_destroyed:
            self.rect.x -= dx # Revert move if collision
        
        # Move vertically
        self.rect.y += dy
        # Check for tile collisions after vertical movement
        collided_tile = self.world.get_tile_at_position(self.rect.centerx, self.rect.centery)
        if collided_tile and collided_tile.is_destructible and not collided_tile.is_destroyed:
            self.rect.y -= dy # Revert move if collision

        # Keep enemy on screen (optional, can be handled by world boundaries too)
        screen_width = pygame.display.get_surface().get_width()
        screen_height = pygame.display.get_surface().get_height()
        self.rect.x = max(0, min(self.rect.x, screen_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, screen_height - self.rect.height))


class Grenade(pygame.sprite.Sprite):
    def __init__(self, color, x, y, size, speed, direction, world, explosion_radius, explosion_damage, detonation_timer):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.direction = direction
        self.world = world
        self.explosion_radius = explosion_radius
        self.explosion_damage = explosion_damage # Not used yet, but for future enemy damage
        self.detonation_time = pygame.time.get_ticks() + detonation_timer
        self.is_exploding = False

    def update(self):
        if not self.is_exploding:
            self.rect.x += self.direction[0] * self.speed
            self.rect.y += self.direction[1] * self.speed

            screen_width = pygame.display.get_surface().get_width()
            screen_height = pygame.display.get_surface().get_height()
            if (self.rect.right < 0 or self.rect.left > screen_width or
                self.rect.bottom < 0 or self.rect.top > screen_height):
                self.kill()
                return

            # Check for collision with tiles
            collided_tile = self.world.get_tile_at_position(self.rect.centerx, self.rect.centery)
            if collided_tile and collided_tile.is_destructible and not collided_tile.is_destroyed:
                self.is_exploding = True
                self.detonation_time = pygame.time.get_ticks() # Detonate immediately on tile hit

            if pygame.time.get_ticks() >= self.detonation_time:
                self.is_exploding = True
        else:
            self.detonate()
            self.kill() # Grenade is removed after detonation

    def detonate(self):
        # Destroy tiles within the explosion radius
        for r in range(int(self.rect.centery - self.explosion_radius), int(self.rect.centery + self.explosion_radius), self.world.tile_size):
            for c in range(int(self.rect.centerx - self.explosion_radius), int(self.rect.centerx + self.explosion_radius), self.world.tile_size):
                self.world.destroy_tile_at_position(c, r)
        # TODO: Add visual explosion effect here

class Projectile(pygame.sprite.Sprite):
    def __init__(self, color, x, y, size, speed, direction, world):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.direction = direction
        self.world = world  # Reference to the world object for collision detection
        self.spawn_time = pygame.time.get_ticks()
        self.lifespan = 1000 # Projectile disappears after 1 second (1000 milliseconds)

    def update(self):
        self.rect.x += self.direction[0] * self.speed
        self.rect.y += self.direction[1] * self.speed

        # Remove projectile if it's off-screen or its lifespan has ended
        screen_width = pygame.display.get_surface().get_width()
        screen_height = pygame.display.get_surface().get_height()
        if (self.rect.right < 0 or self.rect.left > screen_width or
            self.rect.bottom < 0 or self.rect.top > screen_height or
            pygame.time.get_ticks() - self.spawn_time > self.lifespan):
            self.kill()

        # Check for collision with tiles
        collided_tile = self.world.get_tile_at_position(self.rect.centerx, self.rect.centery)
        if collided_tile and collided_tile.is_destructible and not collided_tile.is_destroyed:
            collided_tile.destroy()
            self.kill() # Projectile is destroyed on impact

class World:
    def __init__(self, screen_width, screen_height, tile_size):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        self.tiles = pygame.sprite.Group()
        self.map_data = []

    def generate_map(self, density=0.5):
        # Simple grid generation with some destructible tiles
        rows = self.screen_height // self.tile_size
        cols = self.screen_width // self.tile_size
        
        for r in range(rows):
            row_data = []
            for c in range(cols):
                x = c * self.tile_size
                y = r * self.tile_size
                if (r == 0 or r == rows - 1 or c == 0 or c == cols - 1) or (random.random() < density):
                    # Border tiles and some inner tiles are destructible
                    tile = Tile((0, 128, 0), x, y, self.tile_size, is_destructible=True) # Green destructible tiles
                    row_data.append(tile)
                    self.tiles.add(tile)
                else:
                    # Non-destructible tiles (e.g., walls)
                    tile = Tile((128, 128, 128), x, y, self.tile_size, is_destructible=False) # Grey non-destructible tiles
                    row_data.append(tile)
                    self.tiles.add(tile)
            self.map_data.append(row_data)

    def draw(self, screen):
        self.tiles.draw(screen)

    def get_tile_at_position(self, x, y):
        # More accurate collision check: iterate through tiles and check rect collision
        for tile in self.tiles:
            if tile.rect.collidepoint(x, y):
                return tile
        return None

    def destroy_tile_at_position(self, x, y):
        tile = self.get_tile_at_position(x, y)
        if tile:
            tile.destroy()


# Tile class definition (already present)
class Tile(pygame.sprite.Sprite):
    def __init__(self, color, x, y, size, is_destructible=True):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.is_destructible = is_destructible
        self.is_destroyed = False

    def destroy(self):
        if self.is_destructible:
            self.is_destroyed = True
            self.kill() # Remove from all sprite groups

# Player class definition (already present)
class Player(pygame.sprite.Sprite):
    def __init__(self, color, x, y, size, speed):
        super().__init__()
        self.image = pygame.Surface([size, size])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.last_shot_time = 0
        self.fire_rate = 250 # milliseconds

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

        # Keep player on screen
        self.rect.x = max(0, min(self.rect.x, pygame.display.get_surface().get_width() - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, pygame.display.get_surface().get_height() - self.rect.height))

def main():
    pygame.init()
    import random # Import random for map generation

    # Game window dimensions
    screen_width = 800
    screen_height = 600
    tile_size = 40 # Size of each tile
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Explosive Fun Game")

    # Initialize World
    world = World(screen_width, screen_height, tile_size)
    world.generate_map(density=0.6) # Generate map with 60% destructible tiles

    # Initialize player
    player = Player((255, 0, 0), screen_width // 2, screen_height // 2, 50, 5) # Red player, center of screen, size 50, speed 5
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    projectiles = pygame.sprite.Group() # Group for projectiles
    grenades = pygame.sprite.Group() # Group for grenades

    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle mouse click to fire projectile
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    mouse_pos = event.pos
                    # Calculate direction from player center to mouse position
                    player_center_x = player.rect.centerx
                    player_center_y = player.rect.centery
                    
                    direction_x = mouse_pos[0] - player_center_x
                    direction_y = mouse_pos[1] - player_center_y
                    
                    # Normalize direction vector
                    magnitude = (direction_x**2 + direction_y**2)**0.5
                    if magnitude > 0:
                        direction_x /= magnitude
                        direction_y /= magnitude
                        
                        # Create projectile
                        projectile_size = 10
                        projectile_speed = 10
                        new_projectile = Projectile((255, 255, 0), player.rect.centerx, player.rect.centery, projectile_size, projectile_speed, (direction_x, direction_y), world)
                        projectiles.add(new_projectile)
                        all_sprites.add(new_projectile) # Add projectile to all_sprites for drawing
            
            # Handle input and update player
            keys = pygame.key.get_pressed()
            player.update(keys)

        # Update projectiles
        projectiles.update(world) # Pass world to projectile update for collision checking

        # Game logic and rendering will go here

        # Fill the background with a color
        screen.fill((30, 30, 30)) # Dark grey background

        # Draw world tiles
        world.draw(screen)

        # Draw all sprites (player and projectiles)
        all_sprites.draw(screen)

        # Update the display
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()


