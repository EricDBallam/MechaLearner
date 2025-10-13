
import pygame
import sys

from game.board import Board  # Import the Board class
from game.unit import Building  # Import the Building class


# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

TEAM_COLOR_TOP = (40, 40, 240)  
TEAM_COLOR_BOTTOM = (40, 240, 40)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("MechaLearner Prototype")
    clock = pygame.time.Clock()

    board = Board(outline_top=TEAM_COLOR_TOP, outline_bottom=TEAM_COLOR_BOTTOM)  # Create the board instance
    building_top = Building(grid_pos=(9, 4), team=0, color=TEAM_COLOR_TOP)
    building_bottom = Building(grid_pos=(9, 16), team=1, color=TEAM_COLOR_BOTTOM)


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
        
        # building_top.draw(screen, tile_size)
        # building_bottom.draw(screen, tile_size)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
