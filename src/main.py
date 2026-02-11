"""
Main game class
"""

import sys, os, math, random # bcl
import helpers, models, sprites, particles, audio, ui; from constants import * # local
import pygame # main

class RhythmDodgerGame:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption("Rhythm Dodger")
		self.clock = pygame.time.Clock()

		# fonts (scale with window height)

		self.font_small = pygame.font.Font(FONT_PATH, FONT_SMALL)
		self.font_large = pygame.font.Font(FONT_PATH, FONT_LARGE)

		# audio

		self.audio = audio.AudioManager()

		# preload sfx
		# TODO: move to constants
		self.audio.load_sfx("perfect", os.path.join(SFX_DIR, "beat_perfect.wav"))
		self.audio.load_sfx("good", os.path.join(SFX_DIR, "beat_good.wav"))
		self.audio.load_sfx("miss", os.path.join(SFX_DIR, "beat_miss.wav"))
		self.audio.load_sfx("jump", os.path.join(SFX_DIR, "jump.wav"))
		self.audio.load_sfx("land", os.path.join(SFX_DIR, "land.wav"))

		# sprites

		self.player_sheet = sprites.SpriteSheet(PLAYER_SHEET)
		self.player = models.Player(self.player_sheet, self.font_small)

		self.tileset_native = pygame.image.load(TILESET).convert_alpha()
		self.tiles_native = []
		native_tiles_count = max(3, self.tileset_native.get_width() // NATIVE_TILE)
		for i in range(native_tiles_count):
			surf = pygame.Surface((NATIVE_TILE, NATIVE_TILE), pygame.SRCALPHA)
			surf.blit(self.tileset_native, (0,0), (i * NATIVE_TILE, 0, NATIVE_TILE, NATIVE_TILE))
			self.tiles_native.append(pygame.transform.scale(surf, (TILE_SIZE, TILE_SIZE))) # scale to TILE_SIZE
		
		# obstacles

		self.obstacles_img = pygame.image.load(OBSTACLES_SPR).convert_alpha()

		# split obstacles into frames (assume horizontal strip)
		self.obstacle_sprites = []
		count = max(1, self.obstacles_img.get_width() // NATIVE_OBS)
		for i in range(count):
			surf = pygame.Surface((NATIVE_OBS, NATIVE_OBS), pygame.SRCALPHA)
			surf.blit(self.obstacles_img, (0,0), (i * NATIVE_OBS, 0, NATIVE_OBS, NATIVE_OBS))
			self.obstacle_sprites.append(surf)
		
		# mascot

		self.mascot_sheet = sprites.SpriteSheet(MASCOT_SHEET)
		self.mascot = models.Mascot(self.mascot_sheet, self.font_small)

		# parallax

		self.bg_layers = [
			models.ParallaxLayer(BG_LAYER0, 0.08),
			models.ParallaxLayer(BG_LAYER1, 0.18),
			models.ParallaxLayer(BG_LAYER2, 0.35),
		]
		self.fg_layer = models.ParallaxLayer(FG_LAYER, 0.6)

		# particles

		self.particles = particles.ParticleSystem(300)

		# beat / music

		self.current_track = None
		self.beat_tracker = models.BeatTracker(60.0 / DEFAULT_BPM)
		self.music_started = False
		self.music_start_time = 0.0
		self.beats_until_next_obstacle = helpers.space_obstacle()

		# game state

		self.running = True
		self.game_over = False
		self.score = 0
		self.best_score = 0
		self.combo = 0
		self.max_combo = 0

		# judgement

		self.last_judgement = ""
		self.judgement_timer = 0.0

		# accuracy counters

		self.total_jumps = 0
		self.accurate_jumps = 0

		# obstacles

		self.obstacles = []

		# UI / shake

		self.shake_time = 0.0
		self.shake_intensity = 0.0

		# day/night

		self.time_of_day = random.random()

		# weather

		self.raining = False
		self.rain_timer = 0.0

		# load tracks list

		self.available_tracks = []
		for fn, name, bpm in TRACKS:
			path = os.path.join(MUSIC_DIR, fn)
			self.available_tracks.append((path, name, bpm))

		# start a random track

		self.start_random_track()

		# hud

		self.left_margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		self.top_margin = int(WINDOW_HEIGHT * UI_MARGIN_FRAC)

		# mascot position in top-left near HUD
		self.mascot.x = self.left_margin
		self.mascot.y = self.top_margin

	# music / beat

	def start_random_track(self):
		if not self.available_tracks:
			return
		path, name, bpm = random.choice(self.available_tracks)
		self.current_track = {"path": path, "name": name, "bpm": bpm}
		try:
			self.audio.load_music(path)
			self.audio.play_music(-1)
			self.music_started = True
			self.music_start_time = pygame.time.get_ticks() / 1000.0 + MUSIC_LATENCY
			self.beat_tracker = models.BeatTracker(60.0 / bpm)
		except Exception as e:
			print("Music start failed:", e)
			self.music_started = False

	# input handling

	def handle_events(self):
		jump_pressed = False
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.running = False # Why are you running? Why are you running?

			elif event.type == pygame.KEYDOWN:
				if event.key in (pygame.K_ESCAPE, pygame.K_q):
					self.running = False
				if event.key in (pygame.K_SPACE, pygame.K_UP):
					jump_pressed = True
				if self.game_over and event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
					self.reset()

		return jump_pressed
	
	# game update

	def update(self, dt, jump_pressed):
		if self.game_over:
			# still update particles and mascot
			self.particles.update(dt)
			self.mascot.update(dt)
			return
		
		# compute absolute time if music started
		absolute_time = None
		if self.music_started and self.current_track:
			absolute_time = (pygame.time.get_ticks() / 1000.0) - self.music_start_time
			# keep absolute_time positive
			if absolute_time < 0: absolute_time = 0.0

		# update beat tracker with absolute time if available
		beat_triggered = self.beat_tracker.update(dt, absolute_time)
		if beat_triggered:
			# play soft metronome (use good sound) TODO: add this back via a feature switch in settings
			# self.audio.play_sfx("good", 0.6)

			# count down until next obstacle
			self.beats_until_next_obstacle -= 1

			if self.beats_until_next_obstacle <= 0:
				# spawn obstacle
				spawn_x = WINDOW_WIDTH + int(WINDOW_WIDTH * 0.05)
				sprite = random.choice(self.obstacle_sprites)
				self.obstacles.append(models.Obstacle(spawn_x, sprite))

				# reset spacing
				self.beats_until_next_obstacle = helpers.space_obstacle()
		
		# player jump
		if jump_pressed:
			self.player.try_jump()

			# count jumps
			self.total_jumps += 1

			# determine judgement
			judgement = helpers.get_timing_judgement(self.beat_tracker)
			self.last_judgement = judgement
			self.judgement_timer = 0.6 # show for 0.6s

			if judgement == "Perfect!":
				self.combo += 1
				self.score += 15 + self.combo
				self.accurate_jumps += 1
				self.audio.play_sfx("perfect", 0.9)

				# particles + mascot
				cx = self.player.x + self.player.width / 2
				cy = self.player.y + self.player.height / 2
				self.particles.emit(cx, cy, count = 12, colour = (255, 230, 180))
				self.mascot.react("happy")
			elif judgement == "Good!":
				self.combo += 1
				self.score += 8 + self.combo
				self.accurate_jumps += 1
				self.audio.play_sfx("good", 0.8)
				self.particles.emit(self.player.x + 12, self.player.y + 12, count = 6, colour = (220, 200, 160))
				self.mascot.react("happy")
			else:
				self.combo = 0
				self.audio.play_sfx("miss", 0.6)
				self.mascot.react("sad")
			self.max_combo = max(self.max_combo, self.combo)

		# update player physics
		self.player.update(dt)

		# update obstacles
		for obs in self.obstacles:
			obs.update(dt)
		
		# collision
		for obs in self.obstacles:
			if self.player.rect.colliderect(obs.rect):
				# collision -> game over unless ghost powerup (todo)
				self.game_over = True
				self.best_score = max(self.best_score, self.score)
				self.audio.play_sfx("miss", 0.8)
				self.apply_screen_shake(6, 0.18)
				break
		
		# remove offscreen
		self.obstacles = [o for o in self.obstacles if not o.offscreen()]
		
		# passive score over time
		self.score += dt * 2 * SPRITE_SCALE # small survival score

		# particles and mascot update
		self.particles.update(dt)
		self.mascot.update(dt)

		# judgement timer
		if self.judgement_timer > 0:
			self.judgement_timer -= dt

		# day/night
		self.time_of_day += dt * 0.01
		if self.time_of_day > 1.0: self.time_of_day -= 1.0

		# toggle rain occasionally
		self.rain_timer -= dt
		if self.rain_timer <= 0:
			self.rain_timer = random.uniform(8.0, 20.0)
			self.raining = random.random() < 0.25
			if self.raining:
				self.particles.emit_rain(WINDOW_WIDTH, WINDOW_HEIGHT, count = 60)
	
	# rendering

	def draw_ground(self, surf):
		# tiles_native[0] = ground tile (top soil)
		# tiles_native[1] = grass edge (drawn above ground)
		# tiles_native[2] = shadow/subsoil (drawn below ground repeatedly)

		tiles = self.tiles_native

		# ensure tiles exist
		if not tiles:
			return
		
		# draw grass edge
		if len(tiles) > 1:
			grass = tiles[1]
			x = 0
			while x < WINDOW_WIDTH:
				surf.blit(grass, (x, GROUND_Y))
				x += TILE_SIZE

		# draw tiles below ground to bottom of screen
		if len(tiles) > 2:
			ground = tiles[0]
			y = GROUND_Y + TILE_SIZE
			while y < WINDOW_HEIGHT:
				x = 0
				while x < WINDOW_WIDTH:
					surf.blit(ground, (x, y))
					x += TILE_SIZE
				y += TILE_SIZE
		else:
			pygame.draw.rect(surf, (40, 36, 32), pygame.Rect(0, GROUND_Y + TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT - (GROUND_Y + TILE_SIZE))) # fallback
		
	def draw_beat_bar(self, surf):
		bar_width = int(WINDOW_WIDTH * BEAT_BAR_WIDTH_FRAC)
		bar_height = BEAT_BAR_HEIGHT
		margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		x = WINDOW_WIDTH - bar_width - margin
		y = margin
		pygame.draw.rect(surf, BEAT_BAR_BG, pygame.Rect(x, y, bar_width, bar_height), border_radius = 6)
		phase = self.beat_tracker.normalised_phase()
		fill_w = int(bar_width * phase)
		pygame.draw.rect(surf, BEAT_BAR_COLOUR, pygame.Rect(x, y, fill_w, bar_height), border_radius = 6)

		# centre marker
		cx = x + bar_width // 2
		pygame.draw.line(surf, (255, 255, 255), (cx, y-4), (cx, y+bar_height+4), max(1, int(WINDOW_WIDTH * 0.002)))

	def draw_judgement(self, surf):
		if self.judgement_timer > 0 and self.last_judgement:
			surf_text = self.font_small.render(self.last_judgement, True, TEXT_COLOUR)
			bar_width = int(WINDOW_WIDTH * BEAT_BAR_WIDTH_FRAC)
			margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
			bar_x = WINDOW_WIDTH - bar_width - margin
			bar_y = margin
			x = bar_x + bar_width - surf_text.get_width()
			y = bar_y + BEAT_BAR_HEIGHT + int(WINDOW_HEIGHT * 0.01)
			colour = (200, 255, 200) if "Perfect" in self.last_judgement else (220, 220, 180) if "Good" in self.last_judgement else (255, 200, 180) # colour code
			surf_text = self.font_small.render(self.last_judgement, True, colour)
			surf.blit(surf_text, (x, y))

	def draw_track_info(self, surf):
		if not self.current_track:
			return
		
		text = f"{self.current_track['name']} ({self.current_track['bpm']} BPM)"
		surf_text = self.font_small.render(text, True, TEXT_COLOUR)

		margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		bottom_tile_top = GROUND_Y + TILE_SIZE

		# position: above bottom shadow tiles, aligned to bottom-right tile grid

		x = WINDOW_WIDTH - surf_text.get_width() - margin
		y = max(bottom_tile_top - surf_text.get_height() - int(WINDOW_HEIGHT * 0.01), WINDOW_HEIGHT - surf_text.get_height() - margin)
		surf.blit(surf_text, (x, y))

	def draw_hud(self, surf):
		# mascot, scaled to match text height (left)
		mascot_size = max(MASCOT_SIZE, int(self.font_small.get_height() * 1.2))
		mascot_x = self.left_margin
		mascot_y = self.top_margin
		self.mascot.draw(surf, x=mascot_x, y=mascot_y, size=mascot_size)

		# info cluster (left)
		text_x = mascot_x + mascot_size + int(WINDOW_WIDTH * 0.01)
		line_h = self.font_small.get_height() + int(WINDOW_HEIGHT * 0.008)
		y0 = mascot_y

		# score
		score_surf = self.font_small.render(f"Score: {int(self.score)}", True, TEXT_COLOUR)
		surf.blit(score_surf, (text_x, y0))
		# combo
		combo_surf = self.font_small.render(f"Combo: {self.combo}", True, TEXT_COLOUR)
		surf.blit(combo_surf, (text_x, y0 + line_h))
		# best
		best_surf = self.font_small.render(f"Best: {int(self.best_score)}", True, TEXT_COLOUR)
		surf.blit(best_surf, (text_x, y0 + line_h * 2))

		# beat cluster (right)
		self.draw_beat_bar(surf)
		self.draw_judgement(surf)
		self.draw_track_info(surf)

	def apply_screen_shake(self, intensity = 4, duration = 0.12):
		self.shake_time = duration
		self.shake_intensity = intensity

	def draw_game_over(self, surf):
		panel_w = int(WINDOW_WIDTH * 0.6) # centre panel in the middle of the window
		panel_h = int(WINDOW_HEIGHT * 0.45)
		panel_x = (WINDOW_WIDTH - panel_w) // 2
		panel_y = (WINDOW_HEIGHT - panel_h) // 2
		ui.draw_panel(surf, pygame.Rect(panel_x, panel_y, panel_w, panel_h), (40,36,44), (120,100,90))
		title = self.font_large.render("GAME OVER", True, TEXT_COLOUR)
		surf.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, panel_y + int(panel_h * 0.06)))
		score_info = self.font_small.render(f"Score: {int(self.score)}   Best: {int(self.best_score)}   Max Combo: {self.max_combo}", True, TEXT_COLOUR)
		surf.blit(score_info, (WINDOW_WIDTH//2 - score_info.get_width()//2, panel_y + int(panel_h * 0.22)))
		accuracy = helpers.get_accuracy_percent(self.accurate_jumps, self.total_jumps)
		acc_text = self.font_small.render(f"Beat Accuracy: {accuracy}%", True, TEXT_COLOUR)
		surf.blit(acc_text, (WINDOW_WIDTH//2 - acc_text.get_width()//2, panel_y + int(panel_h * 0.34)))
		rank = helpers.get_rank(accuracy)
		rank_text = self.font_small.render(f"Rank: {rank}", True, TEXT_COLOUR)
		surf.blit(rank_text, (WINDOW_WIDTH//2 - rank_text.get_width()//2, panel_y + int(panel_h * 0.44)))
		hint = self.font_small.render("Press R / Enter / Space to restart", True, TEXT_COLOUR)
		surf.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, panel_y + int(panel_h * 0.62)))

	# render

	def render(self):
		# draw to scene surface for shake
		scene = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		scene.fill(BACKGROUND_COLOUR)

		# camera_dx: use obstacle speed as camera reference (pixels/sec)
		camera_dx = OBSTACLE_SPEED

		for layer in self.bg_layers:
			layer.update(1.0 / FPS, camera_dx)
			layer.draw(scene)
		
		# ground and tiles (scaled)
		self.draw_ground(scene)

		# obstacles
		for obs in self.obstacles:
			obs.draw(scene)
		
		# player squash/stretch micro-animations
		scale_x, scale_y = 1.0, 1.0
		if self.player.vy < -50 * SPRITE_SCALE:
			scale_y = 1.06; scale_x = 0.96
		elif self.player.on_ground and self.player.recently_landed:
			scale_y = 0.9; scale_x = 1.12
		self.player.draw(scene, scale_x, scale_y)

		# mascot
		#self.mascot.draw(scene)

		# particles
		self.particles.draw(scene)

		# foreground parallax
		self.fg_layer.update(1.0 / FPS, camera_dx)
		self.fg_layer.draw(scene)

		# day/night tint
		t = abs(math.sin(self.time_of_day * math.pi * 2))
		tint = (int(255 - 120 * t), int(255 - 120 * t), int(255 - 100 * t))
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill(tint)
		overlay.set_alpha(18)
		scene.blit(overlay, (0, 0))

		# subtle rain overlay
		if self.raining:
			rain_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
			rain_overlay.fill((180, 200, 230, 20))
			scene.blit(rain_overlay, (0, 0))
		
		# HUD (incl. mascot)
		self.draw_hud(scene)

		# subtle judgement flash on perfect
		if "Perfect" in self.last_judgement and self.judgement_timer > 0:
			flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
			alpha = int(120 * (self.judgement_timer / 0.6))
			flash.fill((220, 255, 200, alpha))
			scene.blit(flash, (0, 0))

		# screen shake
		if self.shake_time > 0:
			self.shake_time -= 1.0 / FPS
			dx = random.uniform(-1, 1) * self.shake_intensity
			dy = random.uniform(-1, 1) * self.shake_intensity
			self.screen.blit(scene, (int(dx), int(dy)))
		else:
			self.screen.blit(scene, (0, 0))
		
		# game over overlay
		if self.game_over:
			self.draw_game_over(self.screen)

		pygame.display.flip()

	# reset
	
	def reset(self):
		self.player.reset()
		self.obstacles.clear()
		self.beat_tracker = models.BeatTracker(60.0 / (self.current_track['bpm'] if self.current_track else DEFAULT_BPM))
		self.game_over = False
		self.score = 0
		self.combo = 0
		self.max_combo = 0
		self.total_jumps = 0
		self.accurate_jumps = 0
		self.beats_until_next_obstacle = helpers.space_obstacle()

		# restart music
		if self.current_track:
			try:
				self.audio.play_music(-1)
				self.music_start_time = pygame.time.get_ticks() / 1000.0 + MUSIC_LATENCY
				self.music_started = True
			except Exception:
				self.music_started = False

	# main loop

	def run(self):
		while self.running:
			dt_ms = self.clock.tick(FPS)
			dt = dt_ms / 1000.0

			jump_pressed = self.handle_events()
			self.update(dt, jump_pressed)
			self.render()

		pygame.quit()
		sys.exit()

if __name__ == "__main__": # one of the things i hate most about python
	game = RhythmDodgerGame()
	game.run()