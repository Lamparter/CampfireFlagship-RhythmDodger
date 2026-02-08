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

		# fonts

		self.font_small = pygame.font.Font(FONT_PATH, 14)
		self.font_large = pygame.font.Font(FONT_PATH, 28)

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

	# music

	def start_random_track(self):
		# choose a random track
		self.current_track = random.choice(self.available_tracks)
		track_path = f"{MUSIC_FOLDER}/{self.current_track.filename}"

		# load and play music
		try:
			pygame.mixer.music.load(track_path)
			# -1 loops indefinitely; start immediately
			pygame.mixer.music.play(-1)
		except Exception as e:
			print("Failed to load music:", track_path, e)
			# ensure game state reflects that no music is playing
			self.current_track = None
			pygame.mixer.music.stop()
			self.music_started = False
			self.music_start_time = 0.0
			# restore beat tracker to a safe default interval
			self.beat_tracker = models.BeatTracker(BEAT_INTERVAL)
			return
		
		# sync beat tracker to the track bpm
		self.beat_tracker = models.BeatTracker(self.current_track.interval)

		# record the start time
		self.music_start_time = pygame.time.get_ticks() / 1000.0 + MUSIC_LATENCY
		self.music_started = True

		# reset beat tracker internal clock so the first beat aligns with music start
		self.beat_tracker.time_since_last_beat = 0.0
		self.beat_tracker.last_beat_time = 0.0

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

	def update(self, dt: float, jump_pressed: bool):
		if self.game_over:
			return
		
		# compute absolute time if music started
		absolute_time = None
		if self.music_started and self.current_track is not None:
			absolute_time = (pygame.time.get_ticks() / 1000.0) - self.music_start_time
			# keep absolute_time positive
			if absolute_time < 0:
				absolute_time = 0.0

		# update beat tracker with absolute time if available
		beat_triggered = self.beat_tracker.update(dt, absolute_time)
		if beat_triggered:
			# play beat sound
			self.beat_sound.play()

			# count down until next obstacle
			self.beats_until_next_obstacle -= 1

			if self.beats_until_next_obstacle <= 0:
				# spawn obstacle
				spawn_x = WINDOW_WIDTH + 40
				self.obstacles.append(models.Obstacle(spawn_x))

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

			if judgement in ("Perfect!", "Good!"):
				self.accurate_jumps += 1
			
			self.flash_alpha = FLASH_ALPHA

			# scoring logic
			if judgement == "Perfect!":
				self.combo += 1
				self.score += 15 + self.combo
				#self.max_combo = max(self.max_combo, self.combo)
			elif judgement == "Good!":
				self.combo += 1
				self.score += 8 + self.combo
			else:
				self.combo = 0 # break combo if off-beat

		# update player physics
		self.player.update(dt)

		# update obstacles
		for obs in self.obstacles:
			obs.update(dt)
		self.obstacles = [o for o in self.obstacles if not o.is_offscreen()]

		# collision detection
		player_rect = self.player.rect
		for obs in self.obstacles:
			if player_rect.colliderect(obs.rect):
				self.game_over = True
				self.best_score = max(self.best_score, self.score)
				break
		
		# passive score over time
		if not self.game_over:
			self.score += dt * 2 # small survival score

		if self.judgement_timer > 0:
			self.judgement_timer -= dt
	
	# rendering

	def draw_ground(self):
		pygame.draw.rect(
			self.screen,
			GROUND_COLOUR,
			pygame.Rect(0, GROUND_Y, WINDOW_WIDTH, WINDOW_HEIGHT - GROUND_Y),
		)

	def draw_player(self):
		pygame.draw.rect(self.screen, PLAYER_COLOUR, self.player.rect)

	def draw_obstacles(self):
		for obs in self.obstacles:
			pygame.draw.rect(self.screen, OBSTACLE_COLOUR, obs.rect)

	def draw_beat_bar(self):
		bar_width = 260
		bar_height = 16
		margin = 20
		x = WINDOW_WIDTH - bar_width - margin
		y = margin

		# background
		pygame.draw.rect(
			self.screen,
			BEAT_BAR_BG,
			pygame.Rect(x, y, bar_width, bar_height),
			border_radius=8,
		)

		# fill based on phase
		phase = self.beat_tracker.normalised_phase()
		fill_width = int(bar_width * phase)
		pygame.draw.rect(
			self.screen,
			BEAT_BAR_COLOUR,
			pygame.Rect(x, y, fill_width, bar_height),
			border_radius=8,
		)

		# centre marker for beat moment
		centre_x = x + bar_width // 2
		pygame.draw.line(
			self.screen,
			(255, 255, 255),
			(centre_x, y - 4),
			(centre_x, y + bar_height + 4),
			2,
		)

	def draw_judgement(self):
		if self.judgement_timer > 0 and self.last_judgement:
			surf = self.font_small.render(self.last_judgement, True, TEXT_COLOUR)

			bar_width = 260
			bar_height = 16
			margin = 20

			bar_x = WINDOW_WIDTH - bar_width - margin
			bar_y = margin
		
			x = bar_x + bar_width - surf.get_width()
			y = bar_y + bar_height + 15 # small gap below bar

			self.screen.blit(surf, (x, y))

	def draw_track_info(self):
		if self.current_track:
			text = f"{self.current_track.display_name} ({self.current_track.bpm} BPM)"
			surf = self.font_small.render(text, True, TEXT_COLOUR)

			# position: top-right, under the beat bar
			x = WINDOW_WIDTH - surf.get_width() - 20
			y = GROUND_Y + 25 # slightly below the beat bar and judgement text

			self.screen.blit(surf, (x, y))

	def draw_hud(self):
		score_text = self.font_small.render(f"Score: {int(self.score)}", True, TEXT_COLOUR)
		combo_text = self.font_small.render(f"Combo: {self.combo}", True, TEXT_COLOUR)
		best_text = self.font_small.render(f"Best: {int(self.best_score)}", True, TEXT_COLOUR)

		self.screen.blit(score_text, (20, 20))
		self.screen.blit(combo_text, (20, 50))
		self.screen.blit(best_text, (20, 80))

	def draw_flash(self):
		if self.flash_alpha > 0:
			overlay = pygame.Surface((WINDOW_WIDTH, GROUND_Y))
			overlay.set_alpha(int(self.flash_alpha))
			overlay.fill(helpers.get_flash_colour(self.last_judgement))
			self.screen.blit(overlay, (0, 0))

			# fade out
			self.flash_alpha -= 6 # adjust?

	def draw_game_over(self):
		accuracy = helpers.get_accuracy_percent(self.accurate_jumps, self.total_jumps)

		title = self.font_large.render("GAME OVER", True, TEXT_COLOUR)
		info = self.font_small.render("Press 'R' / 'Enter' / 'Space' to restart", True, TEXT_COLOUR)
		score_info = self.font_small.render(
			f"Score: {int(self.score)}    Best: {int(self.best_score)}    Max Combo: {self.max_combo}",
			True,
			TEXT_COLOUR,
		)
		accuracy_text = self.font_small.render(f"Beat Accuracy: {accuracy}%", True, TEXT_COLOUR)

		title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
		info_rect = info.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10))
		score_rect = score_info.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
		accuracy_rect = accuracy_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))

		self.screen.blit(title, title_rect)
		self.screen.blit(info, info_rect)
		self.screen.blit(score_info, score_rect)
		self.screen.blit(accuracy_text, accuracy_rect)

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