import pygame
import math


class Unit:
    def __init__(self, grid_pos, team, health, max_health, movement_speed, attack_power, attack_range, size=(1, 1), color=None, tile_size=27):
        self.grid_pos = grid_pos      # (grid_x, grid_y)
        self.team = team             # 0 or 1
        self.health = health
        self.max_health = max_health
        self.movement_speed = movement_speed
        self.attack_power = attack_power
        self.attack_range = attack_range
        self.size = size             # (width, height) in grid cells
        self.alive = True
        self.color = color if color is not None else ((200, 200, 200) if team == 0 else (200, 100, 100))
        self.pixel_pos = self.grid_to_pixel(grid_pos, tile_size)

    def grid_to_pixel(self, grid_pos, tile_size):
        x, y = grid_pos
        return ((x - 1) * tile_size, (y - 1) * tile_size)
    

    def update_rect_position(self, tile_size, x_offset, y_offset):
        if hasattr(self, 'rect'):
            self.rect.x = int(self.pixel_pos[0] + x_offset)
            self.rect.y = int(self.pixel_pos[1] + y_offset)
            self.rect.width = int(self.size[0] * tile_size)
            self.rect.height = int(self.size[1] * tile_size)

    def move_toward(self, target_pixel, target_unit=None, stop_distance=5):
        dx = target_pixel[0] - self.pixel_pos[0]
        dy = target_pixel[1] - self.pixel_pos[1]
        dist = math.hypot(dx, dy)
        # Use collider radii for stop distance if target_unit is present
        if target_unit and hasattr(self, 'collider_radius') and hasattr(target_unit, 'collider_radius'):
            stop_distance = self.collider_radius + target_unit.collider_radius
        if dist <= stop_distance:
            return
        self.pixel_pos = (
            self.pixel_pos[0] + self.movement_speed * dx / dist,
            self.pixel_pos[1] + self.movement_speed * dy / dist
        )
        # Clamp to board after moving
        # You must pass board_width and board_height when calling move_toward
        if hasattr(self, 'board_width') and hasattr(self, 'board_height'):
            self.clamp_to_board(self.board_width, self.board_height)

        

    def clamp_to_board(self, board_width, board_height):
        x, y = self.pixel_pos
        w, h = self.size
        x = max(0, min(x, board_width - w))
        y = max(0, min(y, board_height - h))
        self.pixel_pos = (x, y)

    def attack(self, target):
        if self.alive and target.alive:
            target.take_damage(self.attack_power)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False


    def draw(self, surface, tile_size, x_offset=0, y_offset=0):
        w, h = self.size
        pixel_x = int(self.pixel_pos[0] + x_offset)
        pixel_y = int(self.pixel_pos[1] + y_offset)
        rect = pygame.Rect(pixel_x, pixel_y, int(w * tile_size), int(h * tile_size))
        pygame.draw.rect(surface, self.color, rect)

    def update_sprite(self, tile_size):
        raise NotImplementedError("update_sprite must be implemented in subclasses")


class Building(Unit, pygame.sprite.Sprite):
    def __init__(self, grid_pos, team, health=200, max_health=200, color=None):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed=0, attack_power=0, attack_range=0, size=(2, 2), color=color if color is not None else ((100, 100, 255) if team == 0 else (255, 100, 100)))
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((self.size[0]*32, self.size[1]*32), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        self.rect = self.image.get_rect()
        self.update_rect_position(tile_size=32, x_offset=0, y_offset=0)

    def draw(self, surface, tile_size, x_offset=0, y_offset=0):
        # Draw a 2x2 square for the building, using 1-based grid position and board offset
        x, y = self.grid_pos
        w, h = self.size
        pixel_x = int((x - 1) * tile_size + x_offset)
        pixel_y = int((y - 1) * tile_size + y_offset)
        rect = pygame.Rect(pixel_x, pixel_y, int(w * tile_size), int(h * tile_size))
        pygame.draw.rect(surface, self.color, rect)
        
    def update_sprite(self, tile_size):
        pass


class Marksman(Unit, pygame.sprite.Sprite):
    def __init__(self, grid_pos, team, health=100, max_health=100, movement_speed=2, attack_power=20, attack_range=5, size=(2, 2), color=(200, 200, 50), tile_size=32):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed, attack_power, attack_range, size=size, color=color)
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0  # Degrees

        self.tile_size = tile_size
        
        # Create a circular sprite with an arrow
        diameter = max(size) * tile_size
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = diameter // 2 + 2
        radius = diameter // 2 - 2
        
        # Draw circle
        pygame.draw.circle(self.image, self.color, (center, center), radius)
        
        # Draw arrow (triangle) pointing up (forward)
        arrow_color = (30, 30, 30)
        arrow_height = int(radius * 0.7)
        arrow_width = int(radius * 0.5)
        point = (center, center - arrow_height)
        left = (center - arrow_width // 2, center + arrow_height // 2)
        right = (center + arrow_width // 2, center + arrow_height // 2)
        pygame.draw.polygon(self.image, arrow_color, [point, left, right])
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.update_rect_position(tile_size=32, x_offset=0, y_offset=0)
        
        # For circle collider
        self.collider_center = (self.rect.x + center, self.rect.y + center)
        self.collider_radius = radius

    def rotate(self, angle):
        self.angle = angle % 360
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def move_forward(self, tile_size, x_offset=0, y_offset=0):
        # Move in the direction of self.angle
        import math
        dx = math.cos(math.radians(self.angle)) * self.movement_speed
        dy = -math.sin(math.radians(self.angle)) * self.movement_speed
        # Convert to grid position
        pixel_x = (self.rect.x + dx)
        pixel_y = (self.rect.y + dy)
        grid_x = int((pixel_x - x_offset) / tile_size) + 1
        grid_y = int((pixel_y - y_offset) / tile_size) + 1
        self.grid_pos = (grid_x, grid_y)
        self.update_rect_position(tile_size, x_offset, y_offset)

    def update(self, tile_size, x_offset=0, y_offset=0):
        self.update_rect_position(tile_size, x_offset, y_offset)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def check_collision(self, other_sprite):
        # Circle collider collision
        if hasattr(other_sprite, 'collider_center') and hasattr(other_sprite, 'collider_radius'):
            dx = self.collider_center[0] - other_sprite.collider_center[0]
            dy = self.collider_center[1] - other_sprite.collider_center[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            return distance < (self.collider_radius + other_sprite.collider_radius)
        else:
            # Fallback to rect collision
            return self.rect.colliderect(other_sprite.rect)


class Arclight(Unit, pygame.sprite.Sprite):
    
    def __init__(self, grid_pos, team, health=100, max_health=100, movement_speed=2, attack_power=20, attack_range=5, size=(2, 2), color=(200, 200, 200), tile_size=32):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed, attack_power, attack_range, size=size, color=color)
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0  # Degrees
        self.tile_size = tile_size
        self.update_sprite(tile_size)

    def update_sprite(self, tile_size):
        self.tile_size = tile_size
        diameter = max(self.size) * tile_size
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = diameter // 2
        radius = diameter // 2 - 2
        
        # Draw main body circle
        pygame.draw.circle(self.image, self.color, (center, center), radius)
        
        # Draw small filled circle at top interior
        small_radius = int(radius * 0.3)
        small_center = (center, center - int(radius * 0.6))
        pygame.draw.circle(self.image, (0, 0, 0), small_center, small_radius)
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.update_rect_position(tile_size, 0, 0)
        self.collider_center = (self.rect.x + center, self.rect.y + center)
        self.collider_radius = radius

    def update_rect_position(self, tile_size, x_offset, y_offset):
        if hasattr(self, 'rect'):
            self.rect.x = int(self.pixel_pos[0] + x_offset)
            self.rect.y = int(self.pixel_pos[1] + y_offset)
            self.rect.width = int(self.size[0] * tile_size)
            self.rect.height = int(self.size[1] * tile_size)

    def rotate(self, angle):
        self.angle = angle % 360
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, tile_size, x_offset=0, y_offset=0):
        self.update_rect_position(tile_size, x_offset, y_offset)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def check_collision(self, other_sprite):
        if hasattr(other_sprite, 'collider_center') and hasattr(other_sprite, 'collider_radius'):
            dx = self.collider_center[0] - other_sprite.collider_center[0]
            dy = self.collider_center[1] - other_sprite.collider_center[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            return distance < (self.collider_radius + other_sprite.collider_radius)
        else:
            return self.rect.colliderect(other_sprite.rect)

      
class Crawler(Unit, pygame.sprite.Sprite):
    def __init__(self, grid_pos, team, health=20, max_health=20, movement_speed=4, attack_power=5, attack_range=1, color=(100, 200, 100), tile_size=32):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed, attack_power, attack_range, size=(1, 1), color=color)
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0
        self.tile_size = tile_size
        self.update_sprite(tile_size)

    def update_sprite(self, tile_size):
        self.tile_size = tile_size
        diameter = int(tile_size * 0.7)
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = diameter // 2
        radius = diameter // 2 - 2
        # Draw main body circle
        pygame.draw.circle(self.image, self.color, (center, center), radius)
        # Draw arrow (triangle) pointing up (forward)
        arrow_color = (30, 30, 30)
        arrow_height = int(radius * 0.7)
        arrow_width = int(radius * 0.6)
        point = (center, center - arrow_height)
        left = (center - arrow_width // 2, center + arrow_height // 2)
        right = (center + arrow_width // 2, center + arrow_height // 2)
        pygame.draw.polygon(self.image, arrow_color, [point, left, right])
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.update_rect_position(tile_size, 0, 0)
        self.collider_center = (self.rect.x + center, self.rect.y + center)
        self.collider_radius = radius

    def rotate(self, angle):
        self.angle = angle % 360
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self, tile_size, x_offset=0, y_offset=0):
        self.update_rect_position(tile_size, x_offset, y_offset)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
    
    def update_rect_position(self, tile_size, x_offset, y_offset):
        offset_x = x_offset
        offset_y = y_offset
        if hasattr(self, "pixel_offset"):
            offset_x += self.pixel_offset[0]
            offset_y += self.pixel_offset[1]
        if hasattr(self, 'rect'):
            self.rect.x = int(self.pixel_pos[0] + offset_x)
            self.rect.y = int(self.pixel_pos[1] + offset_y)
            self.rect.width = int(self.size[0] * tile_size)
            self.rect.height = int(self.size[1] * tile_size)

    def check_collision(self, other_sprite):
        if hasattr(other_sprite, 'collider_center') and hasattr(other_sprite, 'collider_radius'):
            dx = self.collider_center[0] - other_sprite.collider_center[0]
            dy = self.collider_center[1] - other_sprite.collider_center[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            return distance < (self.collider_radius + other_sprite.collider_radius)
        else:
            return self.rect.colliderect(other_sprite.rect)


def spawn_crawlers(start_grid_pos, team, tile_size=32, color=(100, 200, 100)):
    crawlers = []
    # 2 rows (y), 5 columns (x), 2 crawlers per tile (top-left and bottom-right)
    for dy in range(2):
        for dx in range(5):
            grid_x = start_grid_pos[0] + dx
            grid_y = start_grid_pos[1] + dy
            # Top-left position
            crawler_topleft = Crawler(
                grid_pos=(grid_x, grid_y),
                team=team,
                color=color,
                tile_size=tile_size
            )
            crawler_topleft.pixel_offset = (0, 0)
            crawlers.append(crawler_topleft)
            # Bottom-right position
            crawler_bottomright = Crawler(
                grid_pos=(grid_x, grid_y),
                team=team,
                color=color,
                tile_size=tile_size
            )
            crawler_bottomright.pixel_offset = (tile_size // 2, tile_size // 2)
            crawlers.append(crawler_bottomright)
    return crawlers




