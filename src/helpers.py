"""
Helper functions
"""

import pygame, math, random, models, audio; from constants import *

def space_obstacle() -> int:
	return random.randint(OBSTACLE_SPACING_MIN, OBSTACLE_SPACING_MAX)

def get_timing_judgement(clock: models.BeatTracker): # returns a string judgement based on how close the jump was to the beat
	t = clock.last_beat_time
	dist = min(abs(t), abs(clock.interval - t))

	if dist <= BEAT_TOLERANCE_PERFECT:
		return "Perfect!"
	elif dist <= BEAT_TOLERANCE_GOOD:
		return "Good!"
	else:
		# early vs late
		if t < clock.interval / 2:
			return "Early!"
		else:
			return "Late!"

def get_accuracy_percent(accurate_jumps: int, total_jumps: int):
	if total_jumps == 0:
		return 0
	return int((accurate_jumps / total_jumps) * 100)

def get_rank(accuracy):
	if accuracy >= 95: return "S"
	if accuracy >= 85: return "A"
	if accuracy >= 70: return "B"
	return "C"

def play_ui_sound(audioManager: audio.AudioManager):
	audioManager.play_sfx("ui_" + random.randint(1, 5) + ".wav")

def _with_click_sfx(cb, audioManager: audio.AudioManager):
	def wrapper(btn):
		play_ui_sound(audioManager)
		cb(btn)
	return wrapper