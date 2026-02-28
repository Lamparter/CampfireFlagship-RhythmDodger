"""
Root launcher for desktop and web packaging.
"""

import os
import sys

ROOT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
	sys.path.insert(0, SRC_DIR)

from src.main import RhythmDodgerGame, IS_WEB

if __name__ == "__main__":
	game = RhythmDodgerGame()
	if IS_WEB:
		import asyncio
		asyncio.run(game.run_web())
	else:
		game.run()
