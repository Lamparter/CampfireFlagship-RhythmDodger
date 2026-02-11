"""
Game objects
"""

import pygame, random, sprites
from constants import *

# Game objects

class Player: # player
	def __init__(self, spritesheet: sprites.SpriteSheet, font):
		# store native frames then scale for rendering
		self.x = PLAYER_X
		self.y = float(GROUND_Y - PLAYER_H)
		self.vy = 0.0
		self.on_ground = True
		self.recently_landed = False
		self.spritesheet = spritesheet
		self.animations = {} # load animations: assume sheet rows: idle(0), jump(1), land(2)
		frames = 4 # frames per row: 4
		# load native frames (24x24) and scale them to PLAYER_W/PLAYER_H
		for row, name, fps in [(0,"idle",6),(1,"jump",1),(2,"land",8)]:
			native_frames = spritesheet.load_strip((0, row * NATIVE_PLAYER, NATIVE_PLAYER, NATIVE_PLAYER), frames)
			scaled_frames = [pygame.transform.scale(f, (PLAYER_W, PLAYER_H)) for f in native_frames]
			self.animations[name] = sprites.AnimatedSprite(scaled_frames, fps=fps, loop=(name!="jump"))
		self.state = "idle"
		self.font = font
		self.width = PLAYER_W
		self.height = PLAYER_H
	
	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
	
	def reset(self):
		self.y = float(GROUND_Y - PLAYER_H)
		self.vy = 0.0
		self.on_ground = True
		self.recently_landed = False
		self.state = "idle"
	
	def try_jump(self):
		if self.on_ground:
			self.vy = JUMP_VELOCITY
			self.on_ground = False
			self.state = "jump"
	
	def update(self, dt):
		self.vy += GRAVITY * dt
		self.y += self.vy * dt
		ground_y = GROUND_Y - self.height
		if self.y >= ground_y:
			if not self.on_ground:
				self.recently_landed = True
			self.y = ground_y
			self.vy = 0.0
			self.on_ground = True
			if self.recently_landed:
				self.state = "land"
		else:
			self.on_ground = False
		self.animations[self.state].update(dt) # animation update
		if self.recently_landed:
			# clear flag after one update so land animation can play briefly
			self.recently_landed = False

	def draw(self, surf, scale_x = 1.0, scale_y = 1.0):
		img = self.animations[self.state].get_image()
		# img already scaled to PLAYER_W/PLAYER_H; apply micro squash/stretch via transform
		w,h = img.get_size()
		sw = max(1, int(w * scale_x))
		sh = max(1, int(h * scale_y))
		img_scaled = pygame.transform.scale(img, (sw, sh))
		draw_x = int(self.x) # anchor bottom left
		draw_y = int(self.y + (h - sh))
		surf.blit(img_scaled, (draw_x, draw_y))

class Obstacle:
	def __init__(self, x, sprite):
		# sprite is native 24x24; scale to OBS_W/OBS_H
		self.x = x
		self.sprite = pygame.transform.scale(sprite, (OBS_W, OBS_H))
		self.width = self.sprite.get_width()
		self.height = self.sprite.get_height()
		self.y = GROUND_Y - self.height
		if random.random() < 0.25: # random vertical offset for variety (floating obstacles)
			self.y -= random.choice([24 * SPRITE_SCALE, 40 * SPRITE_SCALE])
		self.passed = False

	@property
	def rect(self):
		return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
	
	def update(self, dt):
		self.x -= OBSTACLE_SPEED * dt
	
	def draw(self, surf):
		surf.blit(self.sprite, (int(self.x), int(self.y)))
	
	def offscreen(self):
		return self.x + self.width < 0

class Mascot:
	def __init__(self, sheet: sprites.SpriteSheet, font_small):
		# load native frames and scale to MASCOT_SIZE
		native_frames = sheet.load_strip((0,0,NATIVE_MASCOT,NATIVE_MASCOT), 3)
		scaled = [pygame.transform.scale(f, (MASCOT_SIZE,MASCOT_SIZE)) for f in native_frames]
		self.anim = sprites.AnimatedSprite(scaled, fps=3) # slower default fps so it doesn't animate too fast
		self.x = int(WINDOW_WIDTH * 0.02)
		self.y = int(WINDOW_HEIGHT * 0.02)
		self.font_small = font_small

	def react(self, mood):
		# mood: "happy", "sad", "idle"
		if mood == "happy":
			self.anim.fps = 5
		elif mood == "sad":
			self.anim.fps = 2
		else:
			self.anim.fps = 3
	
	def update(self, dt):
		self.anim.update(dt)
	
	def draw(self, surf, x = None, y = None, size = None):
		img = self.anim.get_image()
		if size and (img.get_width() != size or img.get_height() != size):
			img = pygame.transform.scale(img, (size, size))
			draw_x = self.x if x is None else x
			draw_y = self.y if y is None else y
			surf.blit(img, (draw_x, draw_y))

# Helper classes

class ParallaxLayer:
	def __init__(self, path, speed):
		self.image = pygame.image.load(path).convert_alpha()
		self.speed = speed
		self.offset = 0.0
		self.w = self.image.get_width()
	
	def update(self, dt, camera_dx):
		# camera_dx is in pixels per second; multiply by dt for per-frame offset
		self.offset = (self.offset + camera_dx * self.speed * dt) % self.w

	def draw(self, surf):
		x = -int(self.offset)
		surf.blit(self.image, (x, 0))
		if x + self.w < surf.get_width():
			surf.blit(self.image, (x + self.w, 0))

class BeatTracker: # internal clock
	def __init__(self, interval):
		self.interval = interval
		self.last_beat_time = 0.0
		self.beat_count = 0
		self.time_acc = 0.0
	
	def update(self, dt, absolute_time = None):
		"""
		If absolute_time is provided (seconds since music start / global music clock,
		e.g. the current playback position including any MUSIC_LATENCY adjustment),
		align beats to that clock. Otherwise fall back to incremental dt accumulation.
		Returns True if a beat was triggered this update.
		"""
		beat_triggered = False

		if absolute_time is not None:
			# compute phase relative to the interval
			phase = (absolute_time % self.interval)
			# last_beat_time is time since last beat
			self.last_beat_time = phase
			# determine if a beat boundary was crossed during current frame
			# it can be approximated by checking if phase is small (~0) or if dt is large enough to cross boundary
			prev_phase = ((absolute_time - dt) % self.interval)
			# if prev_phase > phase, a beat occurred
			if prev_phase > phase:
				self.beat_count += 1
				beat_triggered = True
		else:
			self.time_acc += dt
			while self.time_acc >= self.interval:
				self.time_acc -= self.interval
				self.last_beat_time = 0.0
				self.beat_count += 1
				beat_triggered = True
			self.last_beat_time += dt

		return beat_triggered
	
	def is_on_beat(self, tolerance: float = BEAT_TOLERANCE_GOOD) -> bool:
		# ~close to the beat moment
		return abs(self.last_beat_time) <= tolerance or \
			abs(self.interval - self.last_beat_time) <= tolerance
	
	def normalised_phase(self) -> float:
		return min(1.0, self.last_beat_time / self.interval)