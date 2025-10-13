
class Unit:
	def __init__(self, grid_pos, team, health, max_health, movement_speed, attack_power, attack_range, size=(1, 1), color=None):
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

	def move(self, new_grid_pos):
		self.grid_pos = new_grid_pos

	def attack(self, target):
		if self.alive and target.alive:
			target.take_damage(self.attack_power)

	def take_damage(self, amount):
		self.health -= amount
		if self.health <= 0:
			self.health = 0
			self.alive = False


	def draw(self, surface, tile_size, x_offset=0, y_offset=0):
		# Convert 1-based grid position to pixel position for drawing, including board offset
		import pygame
		x, y = self.grid_pos
		w, h = self.size
		pixel_x = int((x - 1) * tile_size + x_offset)
		pixel_y = int((y - 1) * tile_size + y_offset)
		rect = pygame.Rect(pixel_x, pixel_y, int(w * tile_size), int(h * tile_size))
		pygame.draw.rect(surface, self.color, rect)


class Building(Unit):
	def __init__(self, grid_pos, team, health=200, max_health=200, color=None):
		# Buildings do not move or attack, size is 2x2
		super().__init__(grid_pos, team, health, max_health, movement_speed=0, attack_power=0, attack_range=0, size=(2, 2), color=color if color is not None else ((100, 100, 255) if team == 0 else (255, 100, 100)))

	def draw(self, surface, tile_size, x_offset=0, y_offset=0):
		# Draw a 2x2 square for the building, using 1-based grid position and board offset
		import pygame
		x, y = self.grid_pos
		w, h = self.size
		pixel_x = int((x - 1) * tile_size + x_offset)
		pixel_y = int((y - 1) * tile_size + y_offset)
		rect = pygame.Rect(pixel_x, pixel_y, int(w * tile_size), int(h * tile_size))
		pygame.draw.rect(surface, self.color, rect)

