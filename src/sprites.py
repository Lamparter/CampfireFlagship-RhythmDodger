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
