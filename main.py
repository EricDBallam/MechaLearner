class Button:
    def __init__(self, rect, text, font, bg_color=(60, 60, 60), fg_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.active = True

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, self.fg_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.active and self.rect.collidepoint(pos)

import pygame
import sys

from game.board import Board  # Import the Board class
from game.unit import Building, Marksman, Arclight, Crawler, spawn_crawlers  # Import the Building class


# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
# Simulation speed (seconds per frame)
SIM_DT = 0.04  # Increase for faster simulation, decrease for slower (0.04 feels like a normal speed)

TEAM_COLOR_TOP = (40, 40, 240)  
TEAM_COLOR_BOTTOM = (40, 240, 40)

team0_units = []  # e.g., crawlers, marksman, etc. for team 0
team1_units = []  # for team 1

projectiles = []

def find_closest_enemy(unit, enemy_units):
    min_dist = float('inf')
    closest = None
    ux, uy = unit.pixel_pos
    for enemy in enemy_units:
        ex, ey = enemy.pixel_pos
        dist = ((ux - ex) ** 2 + (uy - ey) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            closest = enemy
    if closest:
        return closest, closest.pixel_pos
    return None, None

def main():
    victory_message = None
    def get_unit_size(unit_type):
        # Query the unit class for its size
        if unit_type == "Crawler":
            return Crawler.size if hasattr(Crawler, "size") else (5, 2)
        elif unit_type == "Marksman":
            return Marksman.size if hasattr(Marksman, "size") else (2, 2)
        elif unit_type == "Arclight":
            return Arclight.size if hasattr(Arclight, "size") else (2, 2)
        return (1, 1)

    def get_highlight_tiles(mx, my, placement_mode):
        tile_size = min(int(screen.get_width() * 0.9) // board.TOTAL_WIDTH, int(screen.get_height() * 0.9) // board.TOTAL_HEIGHT)
        board_width = tile_size * board.TOTAL_WIDTH
        board_height = tile_size * board.TOTAL_HEIGHT
        x_offset = (screen.get_width() - board_width) // 2
        y_offset = (screen.get_height() - board_height) // 2
        grid_x = int((mx - x_offset) / tile_size) + 1
        grid_y = int((my - y_offset) / tile_size) + 1
        tiles = []
        size = get_unit_size(placement_mode)
        for dy in range(size[1]):
            for dx in range(size[0]):
                tiles.append((grid_x + dx, grid_y + dy))
        return tiles, tile_size, x_offset, y_offset
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("MechaLearner Prototype")
    clock = pygame.time.Clock()

    board = Board(surface=screen, outline_top=TEAM_COLOR_TOP, outline_bottom=TEAM_COLOR_BOTTOM)  # Create the board instance
    building_top = Building(grid_pos=(9, 4), team=0, color=TEAM_COLOR_TOP)
    building_bottom = Building(grid_pos=(9, 16), team=1, color=TEAM_COLOR_BOTTOM)
    # marksman = Marksman(grid_pos=(6, 14), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)
    # arclight = Arclight(grid_pos=(12, 14), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)
    # crawlers = spawn_crawlers((8, 12), team=0, tile_size=board.tile_size, color=(100, 200, 100))

    team0_units.extend([Marksman(grid_pos=(6, 16), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)])
    team0_units.extend(spawn_crawlers((8, 14), team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM))
    
    team1_units.extend([Arclight(grid_pos=(6, 4), team=0, color=TEAM_COLOR_TOP, tile_size=board.tile_size)])
    team1_units.extend(spawn_crawlers((6, 6), team=1, tile_size=board.tile_size, color=TEAM_COLOR_TOP))

    font = pygame.font.SysFont(None, 24)
    button_width, button_height = 120, 48
    button_margin = 20
    start_button_rect = (WINDOW_WIDTH - button_width - button_margin, button_margin, button_width, button_height)
    start_button = Button(start_button_rect, "Start Round", font)
    round_active = False

    # Placement buttons (bottom right)
    placement_buttons = []
    placement_types = ["Crawler", "Marksman", "Arclight"]
    for i, label in enumerate(placement_types):
        rect = (WINDOW_WIDTH - button_width - button_margin, WINDOW_HEIGHT - (button_height + button_margin) * (len(placement_types) - i), button_width, button_height)
        placement_buttons.append(Button(rect, label, font))
    placement_mode = None  # None or unit type string

    sim_time = 0.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    board.toggle_grid()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if start_button.is_clicked(event.pos) and not round_active:
                        round_active = True
                        start_button.active = False
                    # Placement button click
                    for i, btn in enumerate(placement_buttons):
                        if btn.is_clicked(event.pos):
                            placement_mode = placement_types[i]
                            break
                    # Board click for placement
                    if placement_mode:
                        # Convert mouse pos to board grid
                        mx, my = event.pos
                        tile_size = min(int(screen.get_width() * 0.9) // board.TOTAL_WIDTH, int(screen.get_height() * 0.9) // board.TOTAL_HEIGHT)
                        board_width = tile_size * board.TOTAL_WIDTH
                        board_height = tile_size * board.TOTAL_HEIGHT
                        x_offset = (screen.get_width() - board_width) // 2
                        y_offset = (screen.get_height() - board_height) // 2
                        grid_x = int((mx - x_offset) / tile_size) + 1
                        grid_y = int((my - y_offset) / tile_size) + 1
                        # 10x10 center square on bottom side
                        min_x = (board.TOTAL_WIDTH // 2) - 4
                        max_x = min_x + 9
                        min_y = board.TOTAL_HEIGHT - 9
                        max_y = board.TOTAL_HEIGHT
                        if min_x <= grid_x <= max_x and min_y <= grid_y <= max_y:
                            # Check overlap with units/buildings
                            def overlaps(new_unit):
                                for unit in team0_units + team1_units + [building_top, building_bottom]:
                                    if hasattr(unit, 'rect') and unit.rect.colliderect(new_unit.rect):
                                        return True
                                return False
                            # Create unit instance (team 0)
                            if placement_mode == "Crawler":
                                # Place a full unit of crawlers
                                new_crawlers = spawn_crawlers((grid_x, grid_y), team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM)
                                # Check all crawlers fit in area and do not overlap
                                valid = True
                                # Gather all occupied grid positions by crawlers
                                crawler_positions = set()
                                for crawler in new_crawlers:
                                    crawler.update_rect_position(board.tile_size, x_offset, y_offset)
                                    cx, cy = crawler.grid_pos
                                    if not (min_x <= cx <= max_x and min_y <= cy <= max_y):
                                        valid = False
                                        break
                                    crawler_positions.add((cx, cy))
                                # Check overlap by grid position for crawlers
                                for unit in team0_units + team1_units + [building_top, building_bottom]:
                                    if hasattr(unit, 'size'):
                                        for dy in range(unit.size[1]):
                                            for dx in range(unit.size[0]):
                                                ux = unit.grid_pos[0] + dx
                                                uy = unit.grid_pos[1] + dy
                                                if (ux, uy) in crawler_positions:
                                                    valid = False
                                                    break
                                    else:
                                        if (unit.grid_pos[0], unit.grid_pos[1]) in crawler_positions:
                                            valid = False
                                            break
                                if valid:
                                    team0_units.extend(new_crawlers)
                                    placement_mode = None
                            elif placement_mode == "Marksman":
                                new_unit = Marksman(grid_pos=(grid_x, grid_y), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)
                                new_unit.update_rect_position(board.tile_size, x_offset, y_offset)
                                if not overlaps(new_unit):
                                    team0_units.append(new_unit)
                                    placement_mode = None
                            elif placement_mode == "Arclight":
                                new_unit = Arclight(grid_pos=(grid_x, grid_y), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)
                                new_unit.update_rect_position(board.tile_size, x_offset, y_offset)
                                if not overlaps(new_unit):
                                    team0_units.append(new_unit)
                                    placement_mode = None

        screen.fill((30, 30, 30))  # Background color
        board.draw(screen)

        tile_size = min(int(screen.get_width() * 0.9) // board.TOTAL_WIDTH, int(screen.get_height() * 0.9) // board.TOTAL_HEIGHT)
        board_width = tile_size * board.TOTAL_WIDTH
        board_height = tile_size * board.TOTAL_HEIGHT
        x_offset = (screen.get_width() - board_width) // 2
        y_offset = (screen.get_height() - board_height) // 2

        # Draw buildings with offset
        building_top.draw(screen, tile_size, x_offset, y_offset)
        building_bottom.draw(screen, tile_size, x_offset, y_offset)

        # Draw Units
        for unit in team0_units + team1_units:
            unit.update_rect_position(tile_size, x_offset, y_offset)
            unit.draw(screen)

        # Draw Start Round button
        if not round_active:
            start_button.draw(screen)
        # Draw placement buttons
        for btn in placement_buttons:
            btn.draw(screen)
        # Placement mode indicator and highlight
        if placement_mode:
            info_text = font.render(f"Placing: {placement_mode}", True, (255, 255, 0))
            screen.blit(info_text, (WINDOW_WIDTH - button_width - button_margin, WINDOW_HEIGHT - (button_height + button_margin) * (len(placement_types) + 1)))
            mx, my = pygame.mouse.get_pos()
            highlight_tiles, tile_size, x_offset, y_offset = get_highlight_tiles(mx, my, placement_mode)
            min_x = (board.TOTAL_WIDTH // 2) - 4
            max_x = min_x + 9
            min_y = board.TOTAL_HEIGHT - 9
            max_y = board.TOTAL_HEIGHT
            # Check if placement is valid
            valid = True
            temp_units = []
            if placement_mode == "Crawler":
                temp_units = spawn_crawlers(highlight_tiles[0], team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM)
            elif placement_mode == "Marksman":
                temp_units = [Marksman(grid_pos=highlight_tiles[0], team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)]
            elif placement_mode == "Arclight":
                temp_units = [Arclight(grid_pos=highlight_tiles[0], team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size)]
            # Gather all grid positions for previewed units
            preview_positions = set()
            for unit in temp_units:
                unit.update_rect_position(board.tile_size, x_offset, y_offset)
                size = getattr(unit, 'size', (1, 1))
                for dy in range(size[1]):
                    for dx in range(size[0]):
                        gx = unit.grid_pos[0] + dx
                        gy = unit.grid_pos[1] + dy
                        if not (min_x <= gx <= max_x and min_y <= gy <= max_y):
                            valid = False
                        preview_positions.add((gx, gy))
            # Gather all grid positions for existing units/buildings
            occupied_positions = set()
            for unit in team0_units + team1_units + [building_top, building_bottom]:
                size = getattr(unit, 'size', (1, 1))
                for dy in range(size[1]):
                    for dx in range(size[0]):
                        ux = unit.grid_pos[0] + dx
                        uy = unit.grid_pos[1] + dy
                        occupied_positions.add((ux, uy))
            # Check for overlap
            if preview_positions & occupied_positions:
                valid = False
            # Draw tiles
            for gx, gy in highlight_tiles:
                px = x_offset + (gx - 1) * tile_size
                py = y_offset + (gy - 1) * tile_size
                color = (80, 200, 80, 120) if valid else (200, 80, 80, 120)
                pygame.draw.rect(screen, color, (px, py, tile_size, tile_size), border_radius=4)

        dt = SIM_DT
        sim_time += dt
        current_time = sim_time

        if round_active:
            # Move units and remove dead ones
            team0_units[:] = [unit for unit in team0_units if getattr(unit, 'health', 1) > 0]
            team1_units[:] = [unit for unit in team1_units if getattr(unit, 'health', 1) > 0]

            # Check victory condition
            if not team0_units:
                victory_message = "Team 1 Wins!"
                round_active = False
            elif not team1_units:
                victory_message = "Team 0 Wins!"
                round_active = False

            if round_active:
                for unit in team0_units:
                    closest_enemy, enemy_pixel = find_closest_enemy(unit, team1_units)
                    if closest_enemy:
                        unit.move_toward(enemy_pixel, target_unit=closest_enemy, allies=team0_units, dt=dt)
                        dist = ((unit.pixel_pos[0] - closest_enemy.pixel_pos[0]) ** 2 + (unit.pixel_pos[1] - closest_enemy.pixel_pos[1]) ** 2) ** 0.5
                        if hasattr(unit, 'collider_radius') and hasattr(closest_enemy, 'collider_radius'):
                            melee_contact = unit.collider_radius + closest_enemy.collider_radius
                            if dist <= melee_contact or dist <= unit.attack_range:
                                if getattr(unit, 'is_ranged', False):
                                    unit.attack(closest_enemy, current_time, projectiles=projectiles, all_units=team1_units)
                                else:
                                    unit.attack(closest_enemy, current_time)

                for unit in team1_units:
                    closest_enemy, enemy_pixel = find_closest_enemy(unit, team0_units)
                    if closest_enemy:
                        unit.move_toward(enemy_pixel, target_unit=closest_enemy, allies=team1_units, dt=dt)
                        unit.update(tile_size, x_offset, y_offset)
                        dist = ((unit.pixel_pos[0] - closest_enemy.pixel_pos[0]) ** 2 + (unit.pixel_pos[1] - closest_enemy.pixel_pos[1]) ** 2) ** 0.5
                        if hasattr(unit, 'collider_radius') and hasattr(closest_enemy, 'collider_radius'):
                            melee_contact = unit.collider_radius + closest_enemy.collider_radius
                            if dist <= melee_contact or dist <= unit.attack_range:
                                if getattr(unit, 'is_ranged', False):
                                    unit.attack(closest_enemy, current_time, projectiles=projectiles, all_units=team0_units)
                                else:
                                    unit.attack(closest_enemy, current_time)

                for projectile in projectiles[:]:
                    projectile.update(dt)
                    projectile.draw(screen)
                    if not projectile.active:
                        projectiles.remove(projectile)

        # Draw victory message if any
        if victory_message:
            msg_surf = font.render(victory_message, True, (255, 255, 0))
            msg_rect = msg_surf.get_rect(center=(WINDOW_WIDTH // 2, 60))
            screen.blit(msg_surf, msg_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
