"""
Game objects
"""

import pygame, random
from constants import *

class Player: # player
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
		# apply gravity
		self.vy += GRAVITY * dt
		self.y += self.vy * dt

		# ground collision
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

class Obstacle: # enemy
	def __init__(self, x: float):
		self.width = OBSTACLE_WIDTH
		self.height = random.randint(OBSTACLE_MIN_HEIGHT, OBSTACLE_MAX_HEIGHT)
		self.x = x
		self.y = GROUND_Y - self.height

	@property
	def rect(self) -> pygame.Rect:
		return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
	
	def update(self, dt: float):
		self.x -= OBSTACLE_SPEED * dt
	
	def is_offscreen(self) -> bool:
		return self.x + self.width < 0

class BeatTracker: # internal clock
	def __init__(self, interval: float):
		self.interval = interval
		self.time_since_last_beat = 0.0 # isn't this kind of like how wakatime works ? lol
		self.last_beat_time = 0.0
		self.beat_count = 0
	
	def update(self, dt: float):
		self.time_since_last_beat += dt
		beat_triggered = False
		while self.time_since_last_beat >= self.interval:
			self.time_since_last_beat -= self.interval
			self.last_beat_time = 0.0
			self.beat_count += 1
			beat_triggered = True
		# track time since last beat for input timing
		self.last_beat_time += dt
		return beat_triggered
	
	def is_on_beat(self) -> bool:
		# ~close to the beat moment
		return abs(self.last_beat_time) <= BEAT_TOLERANCE or \
			abs(self.interval - self.last_beat_time) <= BEAT_TOLERANCE
	
	def normalised_phase(self) -> float:
		return min(1.0, self.last_beat_time / self.interval)