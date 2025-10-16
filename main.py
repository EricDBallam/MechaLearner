
import pygame
import sys

from game.board import Board  # Import the Board class
from game.units import Building, Marksman, Arclight, Crawler, CrawlerGroup  # Import the Building class


# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

SIM_DT = 0.02  # Increase for faster simulation, decrease for slower (0.02 feels like a normal speed)
FPS = 60

TEAM_COLOR_TOP = (40, 40, 240)  
TEAM_COLOR_BOTTOM = (40, 240, 40)

team0_units = []
team1_units = []
projectiles = []

team0 = []
team1 = []


def setup_game():
    # Setup/reset game state
    global team0_units, team1_units, projectiles
    team0_units = []
    team1_units = []
    projectiles = []

    board = Board(surface=screen, outline_top=TEAM_COLOR_TOP, outline_bottom=TEAM_COLOR_BOTTOM)
    building_top = Building(grid_pos=(9, 4), team=0, color=TEAM_COLOR_TOP)
    building_bottom = Building(grid_pos=(9, 16), team=1, color=TEAM_COLOR_BOTTOM)

    team0_units.append(Marksman(grid_pos=(6, 16), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size))
    team0_units.append(CrawlerGroup((8, 14), team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM))
    # team0_units.append(CrawlerGroup((8, 12), team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM))
    
    team1_units.append(Arclight(grid_pos=(6, 4), team=0, color=TEAM_COLOR_TOP, tile_size=board.tile_size))
    team1_units.append(CrawlerGroup((6, 6), team=1, tile_size=board.tile_size, color=TEAM_COLOR_TOP))
    # team1_units.append(CrawlerGroup((6, 8), team=1, tile_size=board.tile_size, color=TEAM_COLOR_TOP))

    for unit in team0_units:
        team0.extend(unit.get_units())
    for unit in team1_units:
        team1.extend(unit.get_units())

    return board, building_top, building_bottom


def unit_placement_mode(board, building_top, building_bottom):
    pass

def play_mode(board, current_time):

    # screen.fill((30, 30, 30))
    # board.draw(screen)
    tile_size = min(int(screen.get_width() * 0.9) // board.TOTAL_WIDTH, int(screen.get_height() * 0.9) // board.TOTAL_HEIGHT)
    board_width = tile_size * board.TOTAL_WIDTH
    board_height = tile_size * board.TOTAL_HEIGHT
    x_offset = (screen.get_width() - board_width) // 2
    y_offset = (screen.get_height() - board_height) // 2
    # building_top.draw(screen, tile_size, x_offset, y_offset)
    # building_bottom.draw(screen, tile_size, x_offset, y_offset)
    for unit in team0 + team1:
        unit.update_rect_position(tile_size, x_offset, y_offset)
        # unit.draw(screen)
    team0[:] = [unit for unit in team0 if getattr(unit, 'health', 1) > 0]
    team1[:] = [unit for unit in team1 if getattr(unit, 'health', 1) > 0]
    for unit in team0:
        unit.act(team0, team1, tile_size, x_offset, y_offset, current_time, SIM_DT, projectiles)
    for unit in team1:
        unit.act(team1, team0, tile_size, x_offset, y_offset, current_time, SIM_DT, projectiles)
    for projectile in projectiles[:]:
        projectile.update(SIM_DT)
        # projectile.draw(screen)
        if not projectile.active:
            projectiles.remove(projectile)


def draw_scene(board, building_top, building_bottom, units, projectiles, start_button, placement_buttons):
    """Draw board, buildings, units, and optional UI. Does not flip the display.
    """
    # Draw everything
    screen.fill((30, 30, 30))
    board.draw(screen)
    # Compute tile size and board offsets (same as in play mode)
    tile_size = min(int(screen.get_width() * 0.9) // board.TOTAL_WIDTH, int(screen.get_height() * 0.9) // board.TOTAL_HEIGHT)
    board_width = tile_size * board.TOTAL_WIDTH
    board_height = tile_size * board.TOTAL_HEIGHT
    x_offset = (screen.get_width() - board_width) // 2
    y_offset = (screen.get_height() - board_height) // 2
    building_top.draw(screen, tile_size, x_offset, y_offset)
    building_bottom.draw(screen, tile_size, x_offset, y_offset)
    # Draw Units (handle groups that expose get_units)
    for unit in units:
        if hasattr(unit, 'update_rect_position'):
            unit.update_rect_position(tile_size, x_offset, y_offset)
        unit.draw(screen)

    for projectile in projectiles[:]:
            projectile.draw(screen)
    
    # Draw UI
    start_button.draw(screen)
    for btn in placement_buttons:
        btn.draw(screen)
    pygame.display.flip()
    clock.tick(FPS)

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


def main():
    global screen, clock
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("MechaLearner Prototype")
    clock = pygame.time.Clock()

    board, building_top, building_bottom = setup_game()

    # --- Placement UI setup ---
    font = pygame.font.SysFont(None, 24)
    button_width, button_height = 120, 48
    button_margin = 20
    start_button_rect = (WINDOW_WIDTH - button_width - button_margin, button_margin, button_width, button_height)
    start_button = Button(start_button_rect, "Start Round", font)
    placement_buttons = []
    placement_types = ["Crawler", "Marksman", "Arclight"]
    for i, label in enumerate(placement_types):
        rect = (WINDOW_WIDTH - button_width - button_margin, WINDOW_HEIGHT - (button_height + button_margin) * (len(placement_types) - i), button_width, button_height)
        placement_buttons.append(Button(rect, label, font))
    placement_mode = None
    round_active = False

    sim_time = 0.0

    game_state = "placement"
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                    running = False
                    break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    board.toggle_grid()
        if game_state == "placement":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if start_button.is_clicked(event.pos) and not round_active:
                        round_active = True
                        start_button.active = False
                        game_state = "play"
                    for i, btn in enumerate(placement_buttons):
                        if btn.is_clicked(event.pos):
                            placement_mode = placement_types[i]
                            break
                    # ...handle placement logic here...

        elif game_state == "play":
            current_time = sim_time + SIM_DT
            move_to_next = play_mode(board, current_time)
            sim_time = current_time
            if move_to_next:
                game_state = "done"
        elif game_state == "done":
            running = False

        draw_scene(board, building_top, building_bottom, team0 + team1, projectiles, start_button, placement_buttons)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()



