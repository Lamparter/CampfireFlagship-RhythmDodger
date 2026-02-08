import random, pygame

class Particle:
	__slots__ = ("alive","x","y","vx","vy","life","colour","size")
	def __init__(self):
		self.alive = False
	def spawn(self, x,y, vx,vy, life, colour, size):
		self.x,self.y,self.vx,self.vy,self.life,self.colour,self.size = x,y,vx,vy,life,colour,size
		self.alive = True
	def update(self, dt):
		if not self.alive: return
		self.life -= dt
		if self.life <= 0:
			self.alive = False
			return
		self.x += self.vx * dt
		self.y += self.vy * dt
		self.vy += 900 * dt
	def draw(self, surf):
		if not self.alive: return
		rect = pygame.Rect(int(self.x), int(self.y), self.size, self.size)
		pygame.draw.rect(surf, self.colour, rect)