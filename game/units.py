import pygame
import math

class Unit:
    def __init__(self, grid_pos, team, health, max_health, movement_speed_mps, 
                 attack_power, attack_range_m, attack_splash_range_m, attack_interval=1.0, 
                 size=(1, 1), color=None, tile_size=27, tile_size_m=10, pixel_position=None):
        
        self.grid_pos = grid_pos      # (grid_x, grid_y)
        self.team = team             # 0 or 1
        self.health = health
        self.max_health = max_health
        self.attack_power = attack_power

        # Convert distances from meters/sec to pixels/sec
        self.movement_speed = (movement_speed_mps / tile_size_m) * tile_size
        self.attack_splash_range = (attack_splash_range_m / tile_size_m) * tile_size
        self.attack_range = (attack_range_m / tile_size_m) * tile_size

        self.attack_interval = attack_interval  # seconds between attacks
        self.last_attack_time = 0  # time of last attack
        self.size = size             # (width, height) in grid cells
        self.alive = True
        self.color = color if color is not None else ((200, 200, 200) if team == 0 else (200, 100, 100))
        
        if pixel_position is not None:
            self.pixel_pos = pixel_position
        else:
            self.pixel_pos = self.grid_to_pixel(grid_pos, tile_size)

        self.starting_pixel_pos = self.pixel_pos

    def grid_to_pixel(self, grid_pos, tile_size):
        x, y = grid_pos
        return ((x - 1) * tile_size, (y - 1) * tile_size)

    def get_units(self):
        return [self]
    
    def act(self, allies, enemies, tile_size, x_offset, y_offset, current_time, dt, projectiles):
        closest_enemy, enemy_pixel = self.find_closest_enemy(enemies)
        if closest_enemy:
            # Use collider_center for movement and attack checks
            target_center = getattr(closest_enemy, 'collider_center', enemy_pixel)
            self_center = getattr(self, 'collider_center', self.pixel_pos)
            self.move_toward(target_center, target_unit=closest_enemy, allies=allies, dt=dt)
            self.update_rect_position(tile_size, x_offset, y_offset)
            dist = math.hypot(self_center[0] - target_center[0], self_center[1] - target_center[1])
            if hasattr(self, 'collider_radius') and hasattr(closest_enemy, 'collider_radius'):
                melee_contact = self.collider_radius + closest_enemy.collider_radius
                if dist <= melee_contact or dist <= self.attack_range:
                    if getattr(self, 'is_ranged', False):
                        self.attack(closest_enemy, current_time, projectiles=projectiles, all_units=enemies)
                    else:
                        self.attack(closest_enemy, current_time)

    def update_rect_position(self, tile_size, x_offset, y_offset):
        if hasattr(self, 'rect'):
            self.rect.x = int(self.pixel_pos[0] + x_offset)
            self.rect.y = int(self.pixel_pos[1] + y_offset)
            self.rect.width = int(self.size[0] * tile_size)
            self.rect.height = int(self.size[1] * tile_size)
            # Set collider center and radius
            self.collider_center = (self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 2)
            self.collider_radius = min(self.rect.width, self.rect.height) // 2 - 2


    def move_toward(self, target_pixel, dt, target_unit=None, stop_distance=1, allies=None, avoidance_radius=None, avoidance_strength=1.0):
        # Use collider_center for movement
        self_center = getattr(self, 'collider_center', self.pixel_pos)
        dx = target_pixel[0] - self_center[0]
        dy = target_pixel[1] - self_center[1]
        dist = math.hypot(dx, dy)
        # Use collider radii for stop distance if target_unit is present
        if target_unit and hasattr(self, 'collider_radius') and hasattr(target_unit, 'collider_radius'):
            stop_distance = self.collider_radius + target_unit.collider_radius
        # Stop if within attack range of target_unit
        if target_unit is not None:
            if dist <= self.attack_range:
                return
        if dist <= stop_distance:
            return
        # Local avoidance force
        avoidance_dx, avoidance_dy = 0, 0
        if avoidance_radius is None:
            avoidance_radius = max(self.size) * self.movement_speed / ((self.movement_speed / self.size[0]) if self.size[0] else 1)
        if allies:
            avoidance_dx, avoidance_dy = self.compute_avoidance_force(allies, avoidance_radius, avoidance_strength)
        move_amount = self.movement_speed * dt
        total_dx = move_amount * dx / dist + avoidance_dx
        total_dy = move_amount * dy / dist + avoidance_dy
        # Move pixel_pos so that collider_center moves as intended
        self.pixel_pos = (
            self.pixel_pos[0] + total_dx,
            self.pixel_pos[1] + total_dy
        )
        if hasattr(self, 'board_width') and hasattr(self, 'board_height'):
            self.clamp_to_board(self.board_width, self.board_height)

    def compute_avoidance_force(self, allies, avoidance_radius=40, avoidance_strength=1.0):
        # Returns (dx, dy) repulsion vector from nearby allies
        force_x, force_y = 0.0, 0.0
        for ally in allies:
            if ally is self or not ally.alive:
                continue
            # Use circle collider if available
            if hasattr(self, 'collider_center') and hasattr(self, 'collider_radius') and hasattr(ally, 'collider_center') and hasattr(ally, 'collider_radius'):
                dx = self.collider_center[0] - ally.collider_center[0]
                dy = self.collider_center[1] - ally.collider_center[1]
                distance = math.hypot(dx, dy)
                min_dist = self.collider_radius + ally.collider_radius
            else:
                dx = self.pixel_pos[0] - ally.pixel_pos[0]
                dy = self.pixel_pos[1] - ally.pixel_pos[1]
                distance = math.hypot(dx, dy)
                min_dist = 0
            if distance < avoidance_radius and distance > 0:
                # Repulsion strength increases as units get closer
                repulse = avoidance_strength * (avoidance_radius - distance) / avoidance_radius
                # Prevent division by zero
                force_x += repulse * dx / distance
                force_y += repulse * dy / distance
        return force_x, force_y
    
    def find_closest_enemy(self, enemy_units):
        min_dist = float('inf')
        closest = None
        ux, uy = self.pixel_pos
        for enemy in enemy_units:
            if hasattr(enemy, 'get_positions'):
                positions = enemy.get_positions()
            else:
                positions = [enemy.grid_pos]
            for ex, ey in positions:
                if hasattr(enemy, 'pixel_pos'):
                    ex_pix, ey_pix = enemy.pixel_pos
                else:
                    ex_pix, ey_pix = ex, ey
                dist = ((ux - ex_pix) ** 2 + (uy - ey_pix) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest = enemy
        if closest:
            if hasattr(closest, 'pixel_pos'):
                return closest, closest.pixel_pos
            elif hasattr(closest, 'get_positions'):
                pos = closest.get_positions()
                if pos:
                    return closest, pos[0]
                else:
                    return closest, (0, 0)
            else:
                return closest, (closest.grid_pos[0], closest.grid_pos[1])
        return None, None

        

    def clamp_to_board(self, board_width, board_height):
        x, y = self.pixel_pos
        w, h = self.size
        x = max(0, min(x, board_width - w))
        y = max(0, min(y, board_height - h))
        self.pixel_pos = (x, y)

    def attack(self, target, current_time, projectiles=None, all_units=None):
        # Only attack if enough time has passed since last attack
        if self.alive and target.alive and (current_time - self.last_attack_time >= self.attack_interval):
            if projectiles is not None and getattr(self, 'is_ranged', False):
                # Ranged attack: spawn projectile
                start_x = self.rect.x + self.rect.width // 2
                start_y = self.rect.y + self.rect.height // 2
                projectile = Projectile(
                    start_pos=(start_x, start_y),
                    target_unit=target,
                    damage=self.attack_power,
                    speed=400,
                    splash_range=self.attack_splash_range,
                    all_units=all_units
                )
                projectiles.append(projectile)
            else:
                # Melee attack: apply damage directly
                target.take_damage(self.attack_power)
            self.last_attack_time = current_time

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False


class Building(Unit, pygame.sprite.Sprite):

    def __init__(self, grid_pos, team, health=200, max_health=200, attack_interval=1.0, tile_size=32, color=None):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed_mps=0, attack_power=0, attack_range_m=0, attack_splash_range_m=0, attack_interval=attack_interval, size=(2, 2), color=color if color is not None else ((100, 100, 255) if team == 0 else (255, 100, 100)))
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((self.size[0]*tile_size, self.size[1]*tile_size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        self.rect = self.image.get_rect()
        self.update_rect_position(tile_size=32, x_offset=0, y_offset=0)

    def draw(self, surface):
        surface.blit(self.image, self.rect)    

    def update_sprite(self):
        pass

    def update(self, tile_size, x_offset=0, y_offset=0):
        self.update_rect_position(tile_size, x_offset, y_offset)

    def move_toward(self, *args, **kwargs):
        return

    def act(self, *args, **kwargs):
        pass


class Marksman(Unit, pygame.sprite.Sprite):
    def __init__(self, grid_pos, team, health=1922, max_health=1922, movement_speed_mps=8, attack_power=2326, attack_range_m=120, attack_splash_range_m=0, attack_interval=3.1, size=(2, 2), color=(200, 200, 50), tile_size=32, tile_size_m=10):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed_mps, attack_power, attack_range_m, attack_splash_range_m, attack_interval, size=size, color=color, tile_size=tile_size, tile_size_m=tile_size_m)
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0  # Degrees
        self.is_ranged = True
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
        self.update_rect_position(tile_size, 0, 0)
        self.collider_center = (self.rect.x + center, self.rect.y + center)
        self.collider_radius = radius

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
    def __init__(self, grid_pos, team, health=4813, max_health=4813, movement_speed_mps=7, attack_power=347, attack_range_m=70, attack_interval=0.9, attack_splash_range_m=7, size=(2, 2), color=(200, 200, 200), tile_size=32, tile_size_m=10):
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed_mps, attack_power, attack_range_m, attack_splash_range_m, attack_interval, size=size, color=color, tile_size=tile_size, tile_size_m=tile_size_m)
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0  # Degrees
        self.tile_size = tile_size
        self.update_sprite(tile_size)
        self.is_ranged = True

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
            # Set collider center and radius
            self.collider_center = (self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 2)
            self.collider_radius = min(self.rect.width, self.rect.height) // 2 - 2

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
    def __init__(self, grid_pos, team, health=263, max_health=263, movement_speed_mps=16, attack_power=79, attack_range_m=0, attack_splash_range_m=0, attack_interval=0.6, color=(100, 200, 100), tile_size=32, tile_size_m=10, pixel_position=None):
        # movement_speed_mps=16 means 16 meters/sec, attack_range_m=2 means 2 meters
        Unit.__init__(self, grid_pos, team, health, max_health, movement_speed_mps, attack_power, attack_range_m, attack_splash_range_m, attack_interval,  size=(1, 1), color=color, tile_size=tile_size, tile_size_m=tile_size_m, pixel_position=pixel_position)
        pygame.sprite.Sprite.__init__(self)
        self.angle = 0
        self.tile_size = tile_size
        self.update_sprite(tile_size)

        self.is_ranged = False  

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
        self._visual_center_offset = center
        self.update_rect_position(tile_size, 0, 0)
        self.collider_center = (self.rect.x + center, self.rect.y + center)
        self.collider_radius = radius

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
            # Set collider center to match visual center
            if hasattr(self, '_visual_center_offset'):
                self.collider_center = (self.rect.x + self._visual_center_offset, self.rect.y + self._visual_center_offset)
            else:
                self.collider_center = (self.rect.x + self.rect.width // 2, self.rect.y + self.rect.height // 2)

    def check_collision(self, other_sprite):
        if hasattr(other_sprite, 'collider_center') and hasattr(other_sprite, 'collider_radius'):
            dx = self.collider_center[0] - other_sprite.collider_center[0]
            dy = self.collider_center[1] - other_sprite.collider_center[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5
            return distance < (self.collider_radius + other_sprite.collider_radius)
        else:
            return self.rect.colliderect(other_sprite.rect)


class CrawlerGroup:
    def __init__(self, start_grid_pos, team, tile_size=32, color=(100, 200, 100)):
        self.unit_type = "CrawlerGroup"
        self.start_grid_pos = start_grid_pos
        self.team = team
        self.tile_size = tile_size
        self.color = color
        self.width = 5
        self.height = 2
        self.size = (self.width, self.height)
        self.crawlers = self._spawn_crawlers()

    def _spawn_crawlers(self):
        crawlers = []
        for dy in range(self.height):
            for dx in range(self.width):
                grid_x = self.start_grid_pos[0] + dx
                grid_y = self.start_grid_pos[1] + dy
                # Top-left position
                crawler_topleft = Crawler(
                    grid_pos=(grid_x, grid_y),
                    team=self.team,
                    color=self.color,
                    tile_size=self.tile_size,
                    pixel_position=((grid_x - 1) * self.tile_size, (grid_y - 1) * self.tile_size)
                )
                crawlers.append(crawler_topleft)
                # Bottom-right position: adjust pixel_pos directly
                crawler_bottomright = Crawler(
                    grid_pos=(grid_x, grid_y),
                    team=self.team,
                    color=self.color,
                    tile_size=self.tile_size,
                    pixel_position=((grid_x - 1) * self.tile_size, (grid_y - 1) * self.tile_size)
                )
                crawler_bottomright.pixel_pos = (
                    crawler_bottomright.pixel_pos[0] + self.tile_size // 2,
                    crawler_bottomright.pixel_pos[1] + self.tile_size // 2
                )
                crawlers.append(crawler_bottomright)
        return crawlers

    def get_units(self):
        return self.crawlers
    
    def find_closest_enemy(self, enemy_units):
        for crawler in self.crawlers:
            if not crawler.alive:
                continue
            crawler.find_closest_enemy(enemy_units)
    
    def get_positions(self):
        # Return all grid positions of crawlers in the group
        return [crawler.grid_pos for crawler in self.crawlers if crawler.alive]

    def is_alive(self):
        # Group is alive if any crawler is alive
        return any(crawler.alive for crawler in self.crawlers)




class Projectile:
    def __init__(self, start_pos, target_unit, damage, speed=400, splash_range=0, all_units=None):
        self.pos = list(start_pos)
        self.target_unit = target_unit
        self.damage = damage
        self.speed = speed
        self.active = True
        self.splash_range = splash_range
        self.all_units = all_units

    def update(self, dt):
        # if not self.active or not self.target_unit.alive:
        #     self.active = False
        #     return
        # Target center of target unit
        if hasattr(self.target_unit, 'rect'):
            tx = self.target_unit.rect.x + self.target_unit.rect.width // 2
            ty = self.target_unit.rect.y + self.target_unit.rect.height // 2
        else:
            tx, ty = self.target_unit.pixel_pos
        dx = tx - self.pos[0]
        dy = ty - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < self.speed * dt or dist == 0:
            # Reached target
            self.pos[0], self.pos[1] = tx, ty
            # Splash damage logic
            if self.splash_range > 0 and self.all_units is not None:
                for unit in self.all_units:
                    if unit.alive and unit is not self.target_unit:
                        # Use center of unit for distance
                        if hasattr(unit, 'rect'):
                            ux = unit.rect.x + unit.rect.width // 2
                            uy = unit.rect.y + unit.rect.height // 2
                        else:
                            ux, uy = unit.pixel_pos
                        splash_dist = math.hypot(ux - tx, uy - ty)
                        if splash_dist <= self.splash_range:
                            unit.take_damage(self.damage)
            self.target_unit.take_damage(self.damage)
            self.active = False
        else:
            self.pos[0] += self.speed * dt * dx / dist
            self.pos[1] += self.speed * dt * dy / dist

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, (255, 255, 0), (int(self.pos[0]), int(self.pos[1])), 6)


    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, (255, 255, 0), (int(self.pos[0]), int(self.pos[1])), 6)

    def update_sprite(self, tile_size):
        raise NotImplementedError("update_sprite must be implemented in subclasses")