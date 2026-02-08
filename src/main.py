"""
Main game class
"""

import sys, math, random # bcl
import helpers; from constants import * # local
import pygame # main

class RhythmDodgerGame:
	def __init__(self):
		pygame.init()
		pygame.mixer.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption(CAPTION)

	# input handling

	def handle_events(self): # todo
		jump_pressed = False
		# implement keys
		return jump_pressed
	
	# game update

	def update(self, dt: float, jump_pressed: bool): # todo
		pass
	
	# rendering

	def draw_ground(self):
		pygame.draw.rect(
			self.screen,
			GROUND_COLOUR,
			pygame.Rect(0, GROUND_Y, WINDOW_WIDTH, WINDOW_HEIGHT - GROUND_Y),
		)

	def draw_player(self): # todo
		pass

	def draw_obstacles(self): # todo
		pass

	def draw_beat_bar(self): # todo
		pass

	def draw_hud(self): # yet another todo
		pass

	def draw_game_over(self): # im slowly getting tired of writing the same thing over and over again
		pass

	def render(self): # finally
		pass

	# main loop (new App())

	def run(self):
		pygame.quit()
		sys.exit()

if __name__ == "__main__": # one of the things i hate most about python
	game = RhythmDodgerGame()
	game.run()