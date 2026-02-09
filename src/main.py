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

		small_size = max(12, int(WINDOW_HEIGHT * 0.02))
		large_size = max(20, int(WINDOW_HEIGHT * 0.04))
		self.font_small = pygame.font.Font(FONT_PATH, small_size)
		self.font_large = pygame.font.Font(FONT_PATH, large_size)

		# audio

		self.audio = audio.AudioManager()

		# preload sfx
		self.audio.load_sfx("perfect", os.path.join(SFX_DIR, "beat_perfect.wav"))
		self.audio.load_sfx("good", os.path.join(SFX_DIR, "beat_good.wav"))
		self.audio.load_sfx("miss", os.path.join(SFX_DIR, "beat_miss.wav"))
		self.audio.load_sfx("jump", os.path.join(SFX_DIR, "jump.wav"))
		self.audio.load_sfx("land", os.path.join(SFX_DIR, "land.wav"))

		# sprites

		self.player_sheet = sprites.SpriteSheet(PLAYER_SHEET)
		self.player = models.Player(self.player_sheet, self.font_small)
		self.tileset = pygame.image.load(TILESET).convert_alpha()
		self.obstacles_img = pygame.image.load(OBSTACLES_SPR).convert_alpha()

		# split obstacles into frames (assume horizontal strip)
		self.obstacle_sprites = []
		obs_w = 24
		obs_h = 24
		count = max(1, self.obstacles_img.get_width() // obs_w)
		for i in range(count):
			surf = pygame.Surface((obs_w, obs_h), pygame.SRCALPHA)
			surf.blit(self.obstacles_img, (0,0), (i*obs_w, 0, obs_w, obs_h))
			self.obstacle_sprites.append(surf)
		
		# mascot

		self.mascot_sheet = sprites.SpriteSheet(MASCOT_SHEET)
		self.mascot = models.Mascot(self.mascot_sheet)

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

	def reset(self):
		self.player.reset()
		self.obstacles.clear()
		self.beat_tracker = models.BeatTracker(BEAT_INTERVAL)
		self.game_over = False
		self.score = 0
		self.combo = 0
		self.total_jumps = 0
		self.accurate_jumps = 0

		# restart music track
		if self.current_track:
			self.start_random_track()

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
		if self.music_started and self.current_track is not None:
			absolute_time = (pygame.time.get_ticks() / 1000.0) - self.music_start_time
			# keep absolute_time positive
			if absolute_time < 0: absolute_time = 0.0

		# update beat tracker with absolute time if available
		beat_triggered = self.beat_tracker.update(dt, absolute_time)
		if beat_triggered:
			# play soft metronome (use good sound)
			self.audio.play_sfx("good", 0.6)

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
		self.obstacles = [o for o in self.obstacles if not o.is_offscreen()]
		
		# passive score over time
		self.score += dt * 2 # small survival score

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
		# draw repeating tiles across bottom
		tile = self.tileset.subsurface((0, 0, TILE_SIZE, TILE_SIZE))
		x = 0
		while x < WINDOW_WIDTH:
			surf.blit(tile, (x, GROUND_Y))
			x += TILE_SIZE

		# ground overlay
		pygame.draw.rect(surf, GROUND_COLOUR, pygame.Rect(0, GROUND_Y + TILE_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT - (GROUND_Y + TILE_SIZE)))
		
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
		if self.current_track:
			text = f"{self.current_track['name']} ({self.current_track['bpm']} BPM)"
			surf_text = self.font_small.render(text, True, TEXT_COLOUR)

			# position: top-right, under the beat bar
			x = WINDOW_WIDTH - surf.get_width() - int(WINDOW_WIDTH * UI_MARGIN_FRAC)
			y = int(WINDOW_HEIGHT * 0.11) # slightly below the beat bar and judgement text

			surf.blit(surf_text, (x, y))

	def draw_hud(self, surf):
		# info cluster (left)
		left_margin = int(WINDOW_WIDTH * UI_MARGIN_FRAC)
		surf.blit(self.font_small.render(f"Score: {int(self.score)}", True, TEXT_COLOUR), (left_margin, int(WINDOW_HEIGHT * 0.03)))
		surf.blit(self.font_small.render(f"Combo: {self.combo}", True, TEXT_COLOUR), (left_margin, int(WINDOW_HEIGHT * 0.03)))
		surf.blit(self.font_small.render(f"Best: {int(self.best_score)}", True, TEXT_COLOUR), (left_margin, int(WINDOW_HEIGHT * 0.03)))

		# beat cluster (right)
		self.draw_beat_bar(surf)
		self.draw_judgement(surf)
		self.draw_track_info(surf)

	def apply_screen_shake(self, intensity = 4, duration = 0.12):
		self.shake_time = duration
		self.shake_intensity = intensity

	def draw_game_over(self, surf):
		panel_w = int(WINDOW_WIDTH * 0.7)
		panel_h = int(WINDOW_HEIGHT * 0.45)
		panel_x = (WINDOW_WIDTH - panel_w) // 2
		panel_y = int(WINDOW_HEIGHT * 0.12)
		ui.draw_panel(surf, pygame.Rect(panel_x, panel_y, panel_w, panel_h), (40, 36, 44), (120, 100, 90))
		title = self.font_large.render("GAME OVER", True, TEXT_COLOUR)
		surf.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, panel_y + int(WINDOW_HEIGHT * 0.03)))
		score_info = self.font_small.render(f"Score: {int(self.score)}    Best: {int(self.best_score)}    Max Combo: {self.max_combo}", True, TEXT_COLOUR)
		surf.blit(score_info, (WINDOW_WIDTH // 2 - score_info.get_width() // 2, panel_y + int(WINDOW_HEIGHT * 0.12)))
		accuracy = helpers.get_accuracy_percent(self.accurate_jumps, self.total_jumps)
		acc_text = self.font_small.render(f"Beat Accuracy: {accuracy}%", True, TEXT_COLOUR)
		surf.blit(acc_text, (WINDOW_WIDTH // 2 - acc_text.get_width() // 2, panel_y + int(WINDOW_HEIGHT * 0.24)))
		hint = self.font_small.render("Press R / Enter / Space to restart", True, TEXT_COLOUR)
		surf.blit(hint, (WINDOW_WIDTH//2 - hint.get_width()//2, panel_y + int(WINDOW_HEIGHT * 0.32)))

	def draw_player(self):
		pygame.draw.rect(self.screen, PLAYER_COLOUR, self.player.rect)

	def draw_obstacles(self):
		for obs in self.obstacles:
			pygame.draw.rect(self.screen, OBSTACLE_COLOUR, obs.rect)

	def draw_flash(self):
		if self.flash_alpha > 0:
			overlay = pygame.Surface((WINDOW_WIDTH, GROUND_Y))
			overlay.set_alpha(int(self.flash_alpha))
			overlay.fill(helpers.get_flash_colour(self.last_judgement))
			self.screen.blit(overlay, (0, 0))

			# fade out
			self.flash_alpha -= 6 # adjust?

	def render(self):
		self.screen.fill(BACKGROUND_COLOUR)
		self.draw_ground()
		self.draw_player()
		self.draw_obstacles()
		self.draw_beat_bar()
		self.draw_judgement()
		self.draw_track_info()
		self.draw_hud()
		self.draw_flash()
		if self.game_over:
			self.draw_game_over()
		pygame.display.flip()

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