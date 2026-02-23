"""
Game objects
"""

import os, pygame, random, sprites, particles, ui
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
		self.mascot = game.mascot

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
				pygame.mixer.music.set_volume(0.32)
				pygame.mixer.music.play(-1)
				self.title_music_loaded = True
			except Exception:
				self.title_music_loaded = False
		
		# UI buttons
		self.menu_buttons = []
		self._create_menu_buttons()

		self.press_text_y = int(WINDOW_HEIGHT * 0.88)

		# pulse for 'press key'
		self.pulse = 0.0
		self.pulse_dir = 1

		# ambient particles
		self.particles = particles.ParticleSystem(200)

		# initial keyboard focus on first button
		if self.menu_buttons:
			self.menu_buttons[0].focus = True
	
	def _create_menu_buttons(self):
		# compute size and positions
		btn_w = int(WINDOW_WIDTH * 0.28)
		btn_h = max(48, int(WINDOW_HEIGHT * 0.07))
		centre_x = WINDOW_WIDTH // 2
		base_y = int(WINDOW_HEIGHT * 0.48)
		spacing = btn_h + int(WINDOW_HEIGHT * 0.02)

		def make_btn(text, idx, cb):
			rect = (centre_x - btn_w // 2, base_y + idx * spacing, btn_w, btn_h)
			b = ui.Button(rect, text, self.font_large, cb)
			return b
		
		self.menu_buttons.append(make_btn("Start", 0, lambda b: self.open_song_select()))
		self.menu_buttons.append(make_btn("Settings", 1, lambda b: self.game.set_state("options")))
		self.menu_buttons.append(make_btn("Quit", 2, lambda b: setattr(self.game, "running", False)))
	
	def open_song_select(self):
		# play decide sfx and switch to song select screen
		try:
			self.game.audio.play_sfx("ui_decide_title")
		except Exception:
			pass

		# fade out title music gently if present
		if self.title_music_loaded:
			try:
				pygame.mixer.music.fadeout(300)
			except Exception:
				pass
		
		# switch to song select state
		self.game.set_state("song_select")
	
	def _focus_next(self):
		if not self.menu_buttons:
			return
		idx = next((i for i, b in enumerate(self.menu_buttons) if b.focus), -1)
		if idx >= 0:
			self.menu_buttons[idx].focus = False
		idx = (idx + 1) % len(self.menu_buttons)
		self.menu_buttons[idx].focus = True
	
	def _focus_prev(self):
		if not self.menu_buttons:
			return
		idx = next((i for i, b in enumerate(self.menu_buttons) if b.focus), -1)
		if idx >= 0:
			self.menu_buttons[idx].focus = False
		idx = (idx - 1) % len(self.menu_buttons)
		self.menu_buttons[idx].focus = True

	def handle_input(self, events):
		for e in events:
			if e.type == pygame.KEYDOWN:
				if e.key in (pygame.K_UP,):
					self._focus_prev()
				elif e.key in (pygame.K_DOWN,):
					self._focus_next()
				elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
					focused = next((b for b in self.menu_buttons if b.focus), None)
					if focused:
						focused._click()
				elif e.key in (pygame.K_q,):
					pass
			elif e.type == pygame.MOUSEMOTION:
				# update hover states so buttons show hover visuals
				for b in self.menu_buttons:
					b.hover = b.rect.collidepoint(e.pos)
	
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

		# dim background to focus UI
		dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
		dim.fill((10, 10, 12, 180))
		surf.blit(dim, (0, 0))
		
		# logo or fallback text (because i haven't designed logo yet)
		if self.logo:
			logo_x = WINDOW_WIDTH // 2 - self.logo.get_width() // 2
			logo_y = int(WINDOW_HEIGHT * 0.10)
			surf.blit(self.logo, (logo_x, logo_y))
		else:
			title_text = self.font_large.render("Campfire Flagship Rhythm Dodger", True, TEXT_COLOUR)
			surf.blit(title_text, (WINDOW_WIDTH//2 - title_text.get_width()//2, int(WINDOW_HEIGHT * 0.10)))
		
		# mascot near logo
		mascot_size = max(MASCOT_SIZE, int(self.font_large.get_height() * 0.9))
		mascot_x = int(WINDOW_WIDTH * 0.12)
		mascot_y = int(WINDOW_HEIGHT * 0.12)
		self.mascot.draw(surf, x=mascot_x, y=mascot_y, size=mascot_size)

		# menu
		for b in self.menu_buttons:
			b.draw(surf)
		
		# press key text (pulsing alpha)
		press_text = self.font_small.render("Press Enter or Space to select", True, TEXT_COLOUR)
		alpha = int(160 + 95 * self.pulse)
		press_surf = press_text.copy()
		press_surf.set_alpha(alpha)
		surf.blit(press_surf, (WINDOW_WIDTH//2 - press_text.get_width()//2, self.press_text_y))

		# particles
		self.particles.draw(surf)

class SongSelectScreen:
	def __init__(self, game):
		self.game = game
		self.screen = game.screen
		self.font_small = game.font_small
		self.font_large = game.font_large
		self.tracks = game.available_tracks

		# build tiles from TRACKS constant
		self.tiles = []
		self.selected_index = 0
		self._build_tiles()
	
	def _build_tiles(self):
		# tile layout: horizontal stretching tiles stacked vertically
		tile_w = int(WINDOW_WIDTH * 0.7)
		tile_h = max(80, int(WINDOW_HEIGHT * 0.12))
		margin_x = int(WINDOW_WIDTH * 0.15)
		base_y = int(WINDOW_HEIGHT * 0.28)
		spacing = tile_h + int(WINDOW_HEIGHT * 0.03)

		for i, t in enumerate(TRACKS):
			rect = pygame.Rect(margin_x, base_y + i * spacing, tile_w, tile_h)
			self.tiles.append((rect, t))
	
	def handle_input(self, events):
		for e in events:
			if e.type == pygame.KEYDOWN:
				if e.key in (pygame.K_ESCAPE, pygame.K_q):
					# return to title
					self.game.set_state("title")
					try: self.game.audio.play_sfx("ui_return_title")
					except: pass
				elif e.key in (pygame.K_UP,):
					self.selected_index = max(0, self.selected_index - 1)
				elif e.key in (pygame.K_DOWN,):
					self.selected_index = min(len(self.tiles)-1, self.selected_index + 1)
				elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
					self._selected_track(self.selected_index)
			elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
				for i, (rect, t) in enumerate(self.tiles):
					if rect.collidepoint(e.pos):
						self._select_track(i)
	
	def _select_track(self, idx):
		# set current track and go to playing state (but show confirm menu)
		rect, t = self.tiles[idx]
		filename, artist, title, bpm, art = t
		self.game.current_track = {"path": os.path.join(MUSIC_DIR, filename), "name": title, "bpm": bpm, "artist": artist, "art": art}

		# play decide sfx
		try: self.game.audio.play_sfx("ui_decide_title")
		except: pass

		# start music and go to playing
		self.game.start_track(self.game.current_track)
		self.game.set_state("playing")
	
	def draw(self):
		surf = self.screen
		surf.fill((20,20,24)) # dim background
		ui.draw_panel(surf, pygame.Rect(int(WINDOW_WIDTH*0.08), int(WINDOW_HEIGHT*0.12), int(WINDOW_WIDTH*0.84), int(WINDOW_HEIGHT*0.76)), (30,28,32), (80,70,60))
		for i, (rect, t) in enumerate(self.tiles):
			filename, artist, title, bpm, art = t
			# tile background
			colour = (255,245,235) if i == self.selected_index else (245,240,235)
			pygame.draw.rect(surf, colour, rect, border_radius=10)

			# album art
			if os.path.exists(art):
				try:
					img = pygame.image.load(art).convert_alpha()
					img = pygame.transform.smoothscale(img, (rect.height-8, rect.height-8))
					surf.blit(img, (rect.x+6, rect.y+4))
				except:
					pass
			# text
			txt = self.font_large.render(title, True, (40,34,30))
			surf.blit(txt, (rect.x + rect.height + 12, rect.y + 8))
			sub = self.font_small.render(f"{artist} - {bpm} BPM", True, (100,90,80))
			surf.blit(sub, (rect.x + rect.height + 12, rect.y + 8 + txt.get_height()))

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