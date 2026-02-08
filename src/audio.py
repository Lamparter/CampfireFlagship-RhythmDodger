import pygame, os

class AudioManager:
	def __init__(self):
		pygame.mixer.init()
		self.sfx = {}
		self.music_loaded = False
	
	def load_sfx(self, name: str, path: str):
		if os.path.exists(path):
			self.sfx[name] = pygame.mixer.Sound(path)

	def play_sfx(self, name: str, volume: float = 1.0):
		s = self.sfx.get(name)
		if s:
			s.set_volume(volume)
			s.play()
	
	def load_music(self, path: str):
		try:
			pygame.mixer.music.load(path)
			self.music_loaded = True
		except Exception as e:
			print("Music load error:", e)
			self.music_loaded = False
	
	def play_music(self, loop: int = -1):
		if self.music_loaded:
			pygame.mixer.music.play(loop)
	
	def stop_music(self):
		pygame.mixer.music.stop()