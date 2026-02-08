"""
Helper functions
"""

import pygame, math, random, models; from constants import *

def load_font(size: int) -> pygame.font.Font:
	return pygame.font.Font(f"fonts/{FONT}/{FONT}.ttf", size)

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

def get_timing_judgement(clock: models.BeatTracker): # returns a string judgement based on how close the jump was to the beat
	t = clock.last_beat_time
	dist = min(abs(t), abs(clock.interval - t))

	if dist <= PERFECT_WINDOW:
		return "Perfect!"
	elif dist <= GOOD_WINDOW:
		return "Good!"
	elif t < clock.interval / 2:
		return "Early!"
	else:
		return "Late!"
	
def get_flash_colour(judgement: str):
	if judgement == "Perfect!":
		return FLASH_COLOUR_PERFECT
	elif judgement == "Good!":
		return FLASH_COLOUR_GOOD
	elif judgement == "Early!" or "Late!":
		return FLASH_COLOUR_BAD

def get_accuracy_percent(accurate_jumps: int, total_jumps: int):
	if total_jumps == 0:
		return 0
	return int((accurate_jumps / total_jumps) * 100)