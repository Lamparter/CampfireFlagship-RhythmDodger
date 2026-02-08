"""
Main game class
"""

import sys, math, random # bcl
import helpers, models; from constants import * # local
import pygame # main

class RhythmDodgerGame:
	def __init__(self):
		pygame.init()
		pygame.mixer.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption(CAPTION)
		self.clock = pygame.time.Clock()

		self.font_small = helpers.load_font(20)
		self.font_large = helpers.load_font(40)

		self.player = models.Player()
		self.obstacles: list[models.Obstacle] = []
		self.beat_tracker = models.BeatTracker(BEAT_INTERVAL)

		self.running = True
		self.game_over = False

		self.score = 0
		self.best_score = 0
		self.combo = 0
		self.max_combo = 0

		self.beat_sound = helpers.create_click_sound()

	def reset(self):
		self.player.reset()
		self.obstacles.clear()
		self.beat_tracker = models.BeatTracker(BEAT_INTERVAL)
		self.game_over = False
		self.score = 0
		self.combo = 0

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
		
		# update beat tracker
		beat_trigerred = self.beat_tracker.update(dt)
		if beat_trigerred:
			# play beat sound
			self.beat_sound.play()
			# spawn obstacle every beat (change?)
			spawn_x = WINDOW_WIDTH + 40
			self.obstacles.append(models.Obstacle(spawn_x))
		
		# player jump
		if jump_pressed:
			on_beat = self.beat_tracker.is_on_beat()
			self.player.try_jump()
			if on_beat:
				self.combo += 1
				self.score += 10 + self.combo # reward combo
				self.max_combo = max(self.max_combo, self.combo)
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

		pygame.draw.rect( # background
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
			(centre_x, y - 4)
			(centre_x, y + bar_height + 4),
			2,
		)

	def draw_hud(self):
		score_text = self.font_small.render(f"Score: {int(self.score)}", True, TEXT_COLOUR)
		combo_text = self.font_small.render(f"Combo: {self.combo}", True, TEXT_COLOUR)
		best_text = self.font_small.render(f"Best: {int(self.best_score)}", True, TEXT_COLOUR)

		self.screen.blit(score_text, (20, 20))
		self.screen.blit(combo_text, (20, 50))
		self.screen.blit(best_text, (20, 80))

	def draw_game_over(self):
		title = self.font_large.render("GAME OVER", True, TEXT_COLOUR)
		info = self.font_small.render("Press 'R' / 'Enter' / 'Space' to restart", True, TEXT_COLOUR)
		score_info = self.font_small.render(
			f"Score: {int(self.score)}    Best: {int(self.best_score)}    Max Combo: {self.max_combo}",
			True,
			TEXT_COLOUR,
		)

		title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
		info_rect = info.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
		score_rect = score_info.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))

		self.screen.blit(title, title_rect)
		self.screen.blit(info, info_rect)
		self.screen.blit(score_info, score_rect)

	def render(self):
		self.screen.fill(BACKGROUND_COLOUR)
		self.draw_ground()
		self.draw_player()
		self.draw_obstacles()
		self.draw_beat_bar()
		self.draw_hud()
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