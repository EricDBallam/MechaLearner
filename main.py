
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
    # building_top = Building(grid_pos=(9, 4), team=0, color=TEAM_COLOR_TOP)
    # building_bottom = Building(grid_pos=(9, 16), team=1, color=TEAM_COLOR_BOTTOM)

    team0_units.append(Building(grid_pos=(9, 17), team=1, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM))
    team0_units.append(Marksman(grid_pos=(6, 16), team=0, color=TEAM_COLOR_BOTTOM, tile_size=board.tile_size))
    team0_units.append(CrawlerGroup((8, 14), team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM))
    # team0_units.append(CrawlerGroup((8, 12), team=0, tile_size=board.tile_size, color=TEAM_COLOR_BOTTOM))
    
    team1_units.append(Building(grid_pos=(9, 3), team=0, tile_size=board.tile_size, color=TEAM_COLOR_TOP))
    team1_units.append(Arclight(grid_pos=(6, 4), team=0, color=TEAM_COLOR_TOP, tile_size=board.tile_size))
    team1_units.append(CrawlerGroup((6, 6), team=1, tile_size=board.tile_size, color=TEAM_COLOR_TOP))
    # team1_units.append(CrawlerGroup((6, 8), team=1, tile_size=board.tile_size, color=TEAM_COLOR_TOP))

    for unit in team0_units:
        team0.extend(unit.get_units())
    for unit in team1_units:
        team1.extend(unit.get_units())

    return board

def unit_placement(unit_type, grid_pos, team, color, board):
    new_unit = unit_type(grid_pos=grid_pos, team=team, color=color, tile_size=board.tile_size)
    team0_units.append(new_unit)
    team0.extend(new_unit.get_units())


def play_mode(board, current_time):

    tile_size, x_offset, y_offset = get_board_metrics(board, mouse_pos=None)

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


def draw_scene(board, units, projectiles, start_button, placement_buttons):
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


# Helper function to get grid position and board parameters
def get_board_metrics(board, mouse_pos=None):
    tile_size = min(int(screen.get_width() * 0.9) // board.TOTAL_WIDTH, int(screen.get_height() * 0.9) // board.TOTAL_HEIGHT)
    board_width = tile_size * board.TOTAL_WIDTH
    board_height = tile_size * board.TOTAL_HEIGHT
    x_offset = (screen.get_width() - board_width) // 2
    y_offset = (screen.get_height() - board_height) // 2

    return tile_size, x_offset, y_offset



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

    board = setup_game()

    # --- Placement UI setup ---
    font = pygame.font.SysFont(None, 24)
    button_width, button_height = 120, 48
    button_margin = 20
    start_button_rect = (WINDOW_WIDTH - button_width - button_margin, button_margin, button_width, button_height)
    start_button = Button(start_button_rect, "Start Round", font)
    placement_buttons = []
    placement_types = {
            "Marksman": Marksman,
            "Arclight": Arclight,
            "Crawler": CrawlerGroup,
        }
    for i, (label, create_func) in enumerate(placement_types.items()):
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
                    
                    # Check if start button clicked
                    if start_button.is_clicked(event.pos) and not round_active:
                        round_active = True
                        start_button.active = False
                        game_state = "play"
                    
                    # Check if any placement button clicked
                    # button_clicked = False
                    # for i, btn in enumerate(placement_buttons):
                    #     if btn.is_clicked(event.pos):
                    #         placement_mode = list(placement_types.keys())[i]
                    #         button_clicked = True
                    #         break

                    button_clicked = False
                    for i, btn in enumerate(placement_buttons):
                        if btn.is_clicked(event.pos):
                            # Get the unit *class* associated with the button
                            unit_class = list(placement_types.values())[i]

                            print(unit_class)
                            
                            # Store the placement_mode as the class itself for easy access, 
                            # or just the label as before
                            placement_mode = list(placement_types.keys())[i] 
                            
                            # *** NOW YOU CAN GET THE SIZE ***
                            try:
                                # Access the static GRID_SIZE attribute on the class
                                unit_grid_size = unit_class.GRID_SIZE 
                                print(f"Selected unit size: {unit_grid_size}")
                                # You can store this in a global variable if needed for drawing/checks 
                                # (e.g., current_unit_size = unit_grid_size)
                            except AttributeError:
                                print(f"Warning: {placement_mode} class does not have a GRID_SIZE attribute.")

                            button_clicked = True
                            break
                    
                    # Handle unit placement on mouse click
                    if placement_mode and not button_clicked:
                        # Compute grid position from mouse click
                        tile_size, x_offset, y_offset = get_board_metrics(board, mouse_pos=event.pos)
                        mx, my = event.pos
                        grid_x = (mx - x_offset) // tile_size
                        grid_y = (my - y_offset) // tile_size
                        grid_pos = (grid_x, grid_y)

                        # Find the correct function from placement_types and place the unit
                        for label, create_func in placement_types.items():
                            if label == placement_mode:
                                unit_placement(create_func, grid_pos=grid_pos, team=1, color=TEAM_COLOR_BOTTOM, board=board)
                                placement_mode = None # Clear mode after placement
                                break


            # Display the unit to be placed following the mouse
            # if placement_mode:
            #     print(f"Placing unit of type: {placement_mode}")

            # Display the unit to be placed following the mouse
            if placement_mode:
                # You would use the stored unit_grid_size here to draw an outline 
                # following the mouse, even before the unit is created.
                
                # 1. Get the unit class again from the placement_types dict
                unit_class_to_place = placement_types.get(placement_mode)
                
                # 2. Get the size
                if unit_class_to_place and hasattr(unit_class_to_place, 'GRID_SIZE'):
                    size_w, size_h = unit_class_to_place.GRID_SIZE
                    print(f"Placing unit of type: {placement_mode} with size: {size_w}x{size_h}")

                

        elif game_state == "play":
            current_time = sim_time + SIM_DT
            move_to_next = play_mode(board, current_time)
            sim_time = current_time
            if move_to_next:
                game_state = "done"
        elif game_state == "done":
            running = False

        draw_scene(board, team0 + team1, projectiles, start_button, placement_buttons)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()



