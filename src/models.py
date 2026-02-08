import pygame, helpers
from constants import *

class Player:
	def __init__(self):
		self.width = PLAYER_WIDTH
		self.height = PLAYER_HEIGHT
		self.x = PLAYER_X
		self.y = float(GROUND_Y - self.height)
		self.vy = 0.0
		self.on_ground = True

	@property
	def rect(self) -> pygame.Rect:
		return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
	
	def reset(self):
		self.y = float(GROUND_Y - self.height)
		self.vy = 0.0
		self.on_ground = True

	def update(self, dt: float):
		# Apply gravity
		self.vy += GRAVITY * dt
		self.y += self.vy * dt

		# Ground collision
		ground_y = GROUND_Y - self.height
		if self.y >= ground_y:
			self.y = ground_y
			self.vy = 0.0
			self.on_ground = True
		else:
			self.on_ground = False
	
	def try_jump(self):
		if self.on_ground:
			self.vy = JUMP_VELOCITY
			self.on_ground = False
