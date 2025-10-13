
import pygame
import sys

from game.board import Board  # Import the Board class
from game.unit import Building, Marksman, Arclight, Crawler, spawn_crawlers  # Import the Building class


# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

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

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    board.toggle_grid()

        screen.fill((30, 30, 30))  # Background color
        # TODO: Draw game elements here
        board.draw(screen)         # Draw the board

        
        
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

        current_time = pygame.time.get_ticks() / 1000.0
        dt = clock.get_time() / 1000.0  # milliseconds to seconds


        # Move units and remove dead ones
        team0_units[:] = [unit for unit in team0_units if getattr(unit, 'health', 1) > 0]
        team1_units[:] = [unit for unit in team1_units if getattr(unit, 'health', 1) > 0]

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

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
