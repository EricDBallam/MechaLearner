
import pygame
import sys

from game.board import Board  # Import the Board class


# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("MechaLearner Prototype")
    clock = pygame.time.Clock()

    board = Board()  # Create the board instance


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

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
