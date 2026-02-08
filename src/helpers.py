"""
Helper functions
"""

import pygame, math, random; from constants import *

def load_font(size: int) -> pygame.font.Font:
	return pygame.font.SysFont(FONT_NAME, size)

def create_click_sound(): # soft sine-wave beep for the beat
	sample_rate = 44100
	duration = 0.12
	frequency = 600

	n_samples = int(sample_rate * duration)
	buf = bytearray()

	volume = 20000

	for i in range(n_samples):
		t = i / sample_rate
		# sine wave
		sample = int(volume * math.sin(2 * math.pi * frequency * t))

		# apply fade-out envelope
		fade = 1.0 - (i / n_samples)
		sample = int(sample * fade)

		buf += sample.to_bytes(2, byteorder='little', signed=True)
	
	return pygame.mixer.Sound(buffer=buf)

def space_obstacle() -> int:
	return random.randint(OBSTACLE_SPACING_MIN, OBSTACLE_SPACING_MAX)