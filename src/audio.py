import pygame

class AudioManager:
	def __init__(self):
		self.enabled = False
		try:
			pygame.mixer.init()
			self.enabled = True
		except Exception:
			self.enabled = False
		self.sfx = {}
		self.music_loaded = False
	
	def load_sfx(self, name: str, path: str):
		if not self.enabled:
			return
		try:
			self.sfx[name] = pygame.mixer.Sound(path)
		except Exception:
			pass

	def play_sfx(self, name: str, volume: float = 1.0):
		if not self.enabled:
			return
		s = self.sfx.get(name)
		if s:
			s.set_volume(volume)
			s.play()
	
	def load_music(self, path: str):
		if not self.enabled:
			self.music_loaded = False
			return
		try:
			pygame.mixer.music.load(path)
			self.music_loaded = True
		except Exception as e:
			print("Music load error:", e)
			self.music_loaded = False
	
	def play_music(self, loop: int = -1):
		if self.enabled and self.music_loaded:
			pygame.mixer.music.play(loop)
	
	def stop_music(self):
		if self.enabled:
			pygame.mixer.music.stop()