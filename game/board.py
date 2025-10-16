
import pygame


class Board:
    # Section sizes
    SIDE_WIDTH = 4
    MAIN_WIDTH = 10
    HEIGHT = 10
    TOTAL_WIDTH = SIDE_WIDTH * 2 + MAIN_WIDTH      # 4 + 10 + 4 = 18
    TOTAL_HEIGHT = HEIGHT * 2                      # 10 + 10 = 20


    # Colors
    DEFAULT_OUTLINE_TOP = (40, 240, 40)      # Top 10x10 main section
    DEFAULT_OUTLINE_BOTTOM = (40, 40, 240)   # Bottom 10x10 main section
    GRID_COLOR = (80, 80, 80)          # Light grid lines

    def __init__(self, surface, show_grid=True, outline_top=None, outline_bottom=None, window_width=800, window_height=600):
        self.show_grid = show_grid
        self.OUTLINE_TOP = outline_top if outline_top is not None else self.DEFAULT_OUTLINE_TOP
        self.OUTLINE_BOTTOM = outline_bottom if outline_bottom is not None else self.DEFAULT_OUTLINE_BOTTOM
        self.tile_size = 32

        if surface is not None:
            self.window_width, self.window_height = surface.get_size()
        else:
            self.window_width = window_width
            self.window_height = window_height
        # Scale board to 90% of window size for margin
        board_scale = 0.9
        scaled_width = int(self.window_width * board_scale)
        scaled_height = int(self.window_height * board_scale)
        tile_size = min(scaled_width // self.TOTAL_WIDTH, scaled_height // self.TOTAL_HEIGHT)
        self.tile_size = tile_size

    def toggle_grid(self):
        self.show_grid = not self.show_grid

    @property
    def get_tile_size(self):
        return self.tile_size


    def draw(self, surface):
        # window_width, window_height = surface.get_size()
        # # Scale board to 90% of window size for margin
        # board_scale = 0.9
        # scaled_width = int(window_width * board_scale)
        # scaled_height = int(window_height * board_scale)
        # tile_size = min(scaled_width // self.TOTAL_WIDTH, scaled_height // self.TOTAL_HEIGHT)
        # self.tile_size = tile_size
        board_width = self.tile_size * self.TOTAL_WIDTH
        board_height = self.tile_size * self.TOTAL_HEIGHT
        x_offset = (self.window_width - board_width) // 2
        y_offset = (self.window_height - board_height) // 2    

        # Section rectangles
        # Left side section (4x20)
        left_rect = pygame.Rect(
            x_offset,
            y_offset,
            self.SIDE_WIDTH * self.tile_size,
            self.TOTAL_HEIGHT * self.tile_size
        )
        # Right side section (4x20)
        right_rect = pygame.Rect(
            x_offset + (self.SIDE_WIDTH + self.MAIN_WIDTH) * self.tile_size,
            y_offset,
            self.SIDE_WIDTH * self.tile_size,
            self.TOTAL_HEIGHT * self.tile_size
        )

        # Ensure right_rect is fully inside the window
        if right_rect.right > x_offset + self.TOTAL_WIDTH * self.tile_size:
            right_rect.width -= (right_rect.right - (x_offset + self.TOTAL_WIDTH * self.tile_size))
        # Top main section (10x10)
        top_rect = pygame.Rect(
            x_offset + self.SIDE_WIDTH * self.tile_size,
            y_offset,
            self.MAIN_WIDTH * self.tile_size,
            self.HEIGHT * self.tile_size
        )
        # Bottom main section (10x10)
        bottom_rect = pygame.Rect(
            x_offset + self.SIDE_WIDTH * self.tile_size,
            y_offset + self.HEIGHT * self.tile_size,
            self.MAIN_WIDTH * self.tile_size,
            self.HEIGHT * self.tile_size
        )

        # Draw main section outlines
        # Draw main section outlines with custom colors
        pygame.draw.rect(surface, self.OUTLINE_TOP, top_rect, 4)
        pygame.draw.rect(surface, self.OUTLINE_BOTTOM, bottom_rect, 4)


        # Split left and right side sections in half horizontally (two 4x10 boxes each)
        left_top_rect = pygame.Rect(left_rect.left, left_rect.top, left_rect.width, left_rect.height // 2)
        left_bottom_rect = pygame.Rect(left_rect.left, left_rect.top + left_rect.height // 2, left_rect.width, left_rect.height // 2)
        right_top_rect = pygame.Rect(right_rect.left, right_rect.top, right_rect.width, right_rect.height // 2)
        right_bottom_rect = pygame.Rect(right_rect.left, right_rect.top + right_rect.height // 2, right_rect.width, right_rect.height // 2)

        # Draw side section outlines with custom colors
        pygame.draw.rect(surface, self.OUTLINE_BOTTOM, left_top_rect, 4)
        pygame.draw.rect(surface, self.OUTLINE_TOP, left_bottom_rect, 4)
        pygame.draw.rect(surface, self.OUTLINE_BOTTOM, right_top_rect, 4)
        pygame.draw.rect(surface, self.OUTLINE_TOP, right_bottom_rect, 4)

        # Draw grid lines (light) if enabled
        if self.show_grid:
            # Top and bottom main sections
            # Draw top section grid lines as usual
            for x in range(top_rect.left, top_rect.right, self.tile_size):
                pygame.draw.line(surface, self.GRID_COLOR, (x, top_rect.top), (x, top_rect.bottom), 1)
            pygame.draw.line(surface, self.GRID_COLOR, (top_rect.right, top_rect.top), (top_rect.right, top_rect.bottom), 1)
            for y in range(top_rect.top, top_rect.bottom, self.tile_size):
                pygame.draw.line(surface, self.GRID_COLOR, (top_rect.left, y), (top_rect.right, y), 1)
            # Draw the last horizontal line at the bottom edge of the top section
            pygame.draw.line(surface, self.GRID_COLOR, (top_rect.left, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)

            # Draw bottom section grid lines, but skip the first horizontal line (shared with top)
            for x in range(bottom_rect.left, bottom_rect.right, self.tile_size):
                pygame.draw.line(surface, self.GRID_COLOR, (x, bottom_rect.top), (x, bottom_rect.bottom), 1)
            pygame.draw.line(surface, self.GRID_COLOR, (bottom_rect.right, bottom_rect.top), (bottom_rect.right, bottom_rect.bottom), 1)
            for y in range(bottom_rect.top + self.tile_size, bottom_rect.bottom, self.tile_size):
                pygame.draw.line(surface, self.GRID_COLOR, (bottom_rect.left, y), (bottom_rect.right, y), 1)
            # Draw the last horizontal line at the bottom edge of the bottom section
            pygame.draw.line(surface, self.GRID_COLOR, (bottom_rect.left, bottom_rect.bottom - 1), (bottom_rect.right, bottom_rect.bottom - 1), 1)

            # Left and right side sections
            for section in [left_rect, right_rect]:
                for x in range(section.left, section.right, self.tile_size):
                    pygame.draw.line(surface, self.GRID_COLOR, (x, section.top), (x, section.bottom), 1)
                # Draw the last vertical line at the right edge
                pygame.draw.line(surface, self.GRID_COLOR, (section.right, section.top), (section.right, section.bottom), 1)
                for y in range(section.top, section.bottom, self.tile_size):
                    pygame.draw.line(surface, self.GRID_COLOR, (section.left, y), (section.right, y), 1)
                # Draw the last horizontal line at the bottom edge
                pygame.draw.line(surface, self.GRID_COLOR, (section.left, section.bottom - 1), (section.right, section.bottom - 1), 1)
