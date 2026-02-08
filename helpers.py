import pygame, main, math

def load_font(size: int) -> pygame.font.Font:
	return pygame.font.SysFont(main.FONT_NAME, size)

def create_click_sound():
	sample_rate = 44100
	duration = 0.05
	frequency = 1000

	n_samples = int(sample_rate * duration)
	buf = bytearray()

	volume = 127
	for i in range(n_samples):
		t = i / sample_rate
		# simple square wave
		sample = int(volume * math.sin(2 * math.pi * frequency * t))
		# 16 bit signed little endian yay
		buf += sample.to_bytes(1, byteorder='little', signed=True)
	
	sound = pygame.mixer.Sound(buffer=buf)
	return sound
