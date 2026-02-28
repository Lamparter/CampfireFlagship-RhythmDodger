"""
Game settings
"""

import json, os
from constants import *

class SettingsManager:
	DEFAULTS = {
		"beat_sound": False,
		"debug_hud": False,
		"music_latency": MUSIC_LATENCY,
		"master_volume": 0.7,
		"show_fps": False,
		"fullscreen": False,
		"ui_scale": 1.0
	}

	def __init__(self, path):
		self.path = path
		self._data = dict(SettingsManager.DEFAULTS)
		self.load()
	
	def load(self):
		try:
			if os.path.exists(self.path):
				with open(self.path, "r", encoding="utf-8") as f:
					data = json.load(f)
					self._data.update(data)
		except Exception:
			pass

	def save(self):
		print(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.path))
		os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), self.path), exist_ok=True)
		with open(self.path, "w", encoding="utf-8") as f:
			json.dump(self._data, f, indent=2)

	def get(self, key):
		return self._data.get(key, SettingsManager.DEFAULTS.get(key))
	
	def set(self, key, value):
		self._data[key] = value
		self.save()