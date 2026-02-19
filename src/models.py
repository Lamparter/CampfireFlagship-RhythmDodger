"""
Game objects
"""

import os, pygame, random, sprites, particles
from constants import *

# Game objects

class Player: # player
	def __init__(self, spritesheet: sprites.SpriteSheet, font):
		# store native frames then scale for rendering
		self.x = PLAYER_X
		self.y = float(GROUND_Y - PLAYER_H)
		self.vy = 0.0
		self.on_ground = True
		self.land_time_remaining = 0.0
		self.recently_landed = False
		self.spritesheet = spritesheet
		self.animations = {}
		self.anim_durations = {}
		frames = 4

		anim_rows = [
			(0, "idle", 6),
			(1, "jump", 4),
			(2, "land", 8),
		]

		# load native frames (24x24) and scale them to PLAYER_W/PLAYER_H
		for row, name, fps in anim_rows:
			native_frames = spritesheet.load_strip((0, row * NATIVE_PLAYER, NATIVE_PLAYER, NATIVE_PLAYER), frames)
			scaled_frames = [pygame.transform.scale(f, (PLAYER_W, PLAYER_H)) for f in native_frames]
			self.animations[name] = sprites.AnimatedSprite(scaled_frames, fps=fps, loop=True)
			self.anim_durations[name] = frames / float(fps)

		self.state = "idle"
		self.font = font
		self.width = PLAYER_W
		self.height = PLAYER_H

		self._mask_cache = {}

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
			self.land_time_remaining = 0.0
	
	def get_mask(self):
		# get the current frame surface from the AnimatedSprite
		img = self.animations[self.state].get_image()
		if img is None:
			return None
		key = id(img)
		mask = self._mask_cache.get(key)
		if mask is None:
			mask = pygame.mask.from_surface(img)
			self._mask_cache[key] = mask
		return mask
	
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
				self.land_time_remaining = self.anim_durations.get("land", 0.25)
		else:
			self.on_ground = False

		self.animations[self.state].update(dt) # animation update

		if self.state == "land":
			# decrement timer
			self.land_time_remaining -= dt
			if self.land_time_remaining <= 0.0:
				self.state = "idle"
				self.land_time_remaining = 0.0

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

		# create a mask from the scaled surface for pixel-perfect collision
		self.mask = pygame.mask.from_surface(self.sprite)

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

class TitleScreen:
	def __init__(self, game):
		self.game = game
		self.screen = game.screen
		self.clock = game.clock
		self.font_small = game.font_small
		self.font_large = game.font_large
		self.bg_layers = getattr(game, "bg_layers", [])

		# load logo if present
		self.logo = None
		if os.path.exists(TITLE_LOGO):
			try:
				logo_img = pygame.image.load(TITLE_LOGO).convert_alpha()
				target_w = int(WINDOW_WIDTH * 0.5)
				scale = target_w / logo_img.get_width()
				target_h = int(logo_img.get_height() * scale)
				self.logo = pygame.transform.smoothscale(logo_img, (target_w, target_h))
			except Exception:
				self.logo = None

		
		# load music if present
		self.title_music_loaded = False
		if os.path.exists(TITLE_MUSIC):
			try:
				pygame.mixer.music.load(TITLE_MUSIC)
				self.title_music_loaded = True
			except Exception:
				self.title_music_loaded = False
		
		# menu
		self.menu_items = ["Start", "Options", "Quit"]
		self.selected = 0

		# pulse for 'press key'
		self.pulse = 0.0
		self.pulse_dir = 1

		# mascot reference
		self.mascot = game.mascot

		# ambient particles
		self.particles = particles.ParticleSystem(200)

		# start title music if available
		if self.title_music_loaded:
			try:
				pygame.mixer.music.play(-1)
				pygame.mixer.music.set_volume(0.6)
			except Exception:
				pass
	
	def handle_input(self, events):
		for event in events:
			if event.type == pygame.KEYDOWN:
				if event.key in (pygame.K_RETURN, pygame.K_SPACE):
					sel = self.menu_items[self.selected]
					if sel == "Start":
						# fade title music and start gameplay
						if self.title_music_loaded:
							try:
								pygame.mixer.music.fadeout(400)
							except Exception:
								pass
						self.game.start_random_track()
						self.game.state = "playing"
					elif sel == "Options":
						self.game.state = "options"
					elif sel == "Quit":
						self.game.running = False
				elif event.key in (pygame.K_UP,):
					self.selected = (self.selected - 1) % len(self.menu_items)
				elif event.key in (pygame.K_DOWN,):
					self.selected = (self.selected + 1) % len(self.menu_items)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mx,my = event.pos
				self._try_click_menu(mx,my)
		
	def _try_click_menu(self, mx, my):
		centre_x = WINDOW_WIDTH // 2
		base_y = int(WINDOW_HEIGHT * 0.62)
		spacing = int(self.font_large.get_height() * 1.6)
		for i, item in enumerate(self.menu_items):
			text = self.font_large.render(item, True, TEXT_COLOUR)
			tx = centre_x - text.get_width() // 2
			ty = base_y + i * spacing
			rect = pygame.Rect(tx, ty, text.get_width(), text.get_height())
			if rect.collidepoint(mx,my):
				self.selected = i
				if item == "Start":
					if self.title_music_loaded:
						try:
							pygame.mixer.music.fadeout(400)
						except Exception:
							pass
						self.game.start_random_track()
						self.game.state = "playing"
				elif item == "Options":
					self.game.state = "options"
				elif item == "Quit":
					self.game.running = False
	
	def update(self, dt):
		# pulse animation
		self.pulse += dt * 2.0 * self.pulse_dir
		if self.pulse > 1.0:
			self.pulse = 1.0
			self.pulse_dir = -1
		elif self.pulse < 0.0:
			self.pulse = 0.0
			self.pulse_dir = -1
		
		# ambient particles
		if random.random() < 0.02:
			x = random.uniform(WINDOW_WIDTH*0.2, WINDOW_WIDTH*0.8)
			y = random.uniform(WINDOW_HEIGHT*0.2, WINDOW_HEIGHT*0.6)
			self.particles.emit(x,y, count=4, colour=(255,240,200))
		self.particles.update(dt)
		self.mascot.update(dt)

	def draw(self):
		surf = self.screen
		surf.fill(BACKGROUND_COLOUR)

		# draw background layers (static)
		for layer in self.bg_layers:
			layer.draw(surf)
		
		# logo or fallback text (because i haven't designed logo yet)
		if self.logo:
			logo_x = WINDOW_WIDTH // 2 - self.logo.get_width() // 2
			logo_y = int(WINDOW_HEIGHT * 0.12)
			surf.blit(self.logo, (logo_x, logo_y))
		else:
			title_text = self.font_large.render("Campfire Flagship Rhythm Dodger", True, TEXT_COLOUR)
			surf.blit(title_text, (WINDOW_WIDTH//2 - title_text.get_width()//2, int(WINDOW_HEIGHT * 0.12)))
		
		# mascot near logo
		mascot_size = max(MASCOT_SIZE, int(self.font_large.get_height() * 0.9))
		mascot_x = int(WINDOW_WIDTH * 0.12)
		mascot_y = int(WINDOW_HEIGHT * 0.12)
		self.mascot.draw(surf, x=mascot_x, y=mascot_y, size=mascot_size)

		# menu
		centre_x = WINDOW_WIDTH // 2
		base_y = int(WINDOW_HEIGHT * 0.62)
		spacing = int(self.font_large.get_height() * 1.6)
		for i, item in enumerate(self.menu_items):
			colour = (255, 230, 200) if i == self.selected else TEXT_COLOUR
			text = self.font_large.render(item, True, colour)
			tx = centre_x - text.get_width() // 2
			ty = base_y + i * spacing
			surf.blit(text, (tx,ty))
		
		# press key text (pulsing alpha)
		press_text = self.font_small.render("Press Enter or Space to select", True, TEXT_COLOUR)
		alpha = int(160 + 95 * self.pulse)
		press_surf = press_text.copy()
		press_surf.set_alpha(alpha)
		surf.blit(press_surf, (WINDOW_WIDTH//2 - press_text.get_width()//2, int(WINDOW_HEIGHT * 0.9)))

		# particles
		self.particles.draw(surf)

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