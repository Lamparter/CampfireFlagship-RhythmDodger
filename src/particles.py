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

class ParticleSystem:
	def __init__(self, max_particles=300):
		self.pool = [Particle() for _ in range(max_particles)]
	def emit(self, x,y, count=8, colour=(255,220,160)):
		for p in self.pool:
			if not p.alive:
				vx = random.uniform(-140,140)
				vy = random.uniform(-320,-80)
				life = random.uniform(0.22,0.6)
				size = random.choice([1,2,3])
				p.spawn(x,y,vx,vy,life,colour,size)
				count -= 1
				if count <= 0: break
	def emit_rain(self, width, height, count=40):
		# spawn rain particles across screen top
		for _ in range(count):
			for p in self.pool:
				if not p.alive:
					x = random.uniform(0, width)
					y = random.uniform(-50, 0)
					vx = random.uniform(-20, 20)
					vy = random.uniform(300, 600)
					life = random.uniform(0.6, 1.2)
					size = 1
					p.spawn(x,y,vx,vy,life,(180,200,230),size)
					break
	def update(self, dt):
		for p in self.pool: p.update(dt)
	def draw(self, surf):
		for p in self.pool: p.draw(surf)