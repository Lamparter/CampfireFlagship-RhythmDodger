import pygame
from typing import List, Tuple

class SpriteSheet:
	def __init__(self, path: str):
		self.sheet = pygame.image.load(path).convert_alpha()

	def image_at(self, rect: Tuple[int,int,int,int]) -> pygame.Surface:
		x,y,w,h = rect
		image = pygame.Surface((w,h), pygame.SRCALPHA)
		image.blit(self.sheet, (0,0), rect)
		return image
	
	def load_strip(self, rect: Tuple[int,int,int,int], count: int) -> List[pygame.Surface]:
		x,y,w,h = rect
		return [self.image_at((x + i*w, y, w, h)) for i in range(count)]

class AnimatedSprite:
	def __init__(self, frames: List[pygame.Surface], fps: float = 8.0, loop: bool = True):
		self.frames = frames
		self.fps = fps
		self.loop = loop
		self.time = 0.0
		self.index = 0
	
	def update(self, dt: float):
		if len(self.frames) <= 1: return
		self.time += dt
		frame_time = 1.0 / max(0.0001, self.fps)
		while self.time >= frame_time:
			self.time -= frame_time
			self.index += 1
			if self.index >= len(self.frames):
				if self.loop:
					self.index = 0
				else:
					self.index = len(self.frames) - 1
	
	def get_image(self) -> pygame.Surface:
		return self.frames[self.index]