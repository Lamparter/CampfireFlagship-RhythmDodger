"""
Configuration/constants
"""

import os

# Responsive UI

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Derived layout values (relative)

GROUND_FRACTION = 0.82 # fraction of window height where ground top sits

GROUND_Y = int(WINDOW_HEIGHT * GROUND_FRACTION)

# Base sprite frame sizes (pixel-art native sizes)

NATIVE_TILE = 16
NATIVE_PLAYER = 24
NATIVE_MASCOT = 24
NATIVE_OBS = 24

# Sprite scale factor (integer) derived from window height to keep pixel-art crisp

SPRITE_SCALE = max(1, int(WINDOW_HEIGHT / 240))

# Scaled sizes used for rendering

TILE_SIZE = NATIVE_TILE * SPRITE_SCALE
PLAYER_W = NATIVE_PLAYER * SPRITE_SCALE
PLAYER_H = NATIVE_PLAYER * SPRITE_SCALE
MASCOT_SIZE = NATIVE_MASCOT * SPRITE_SCALE
OBS_W = NATIVE_OBS * SPRITE_SCALE
OBS_H = NATIVE_OBS * SPRITE_SCALE

PLAYER_X = int(WINDOW_WIDTH * 0.12) # relative horizontal player position

GRAVITY = 2000.0 * SPRITE_SCALE
JUMP_VELOCITY = -700.0 * SPRITE_SCALE

OBSTACLE_SPEED = 400.0 * SPRITE_SCALE
OBSTACLE_SPACING_MIN = 3 # * SPRITE_SCALE
OBSTACLE_SPACING_MAX = 5 # * SPRITE_SCALE

FONT_SMALL = max(14, int(WINDOW_HEIGHT * 0.035))
FONT_LARGE = max(28, int(WINDOW_HEIGHT * 0.06))

# Timing / beat

DEFAULT_BPM = 120
BEAT_TOLERANCE_PERFECT = 0.05
BEAT_TOLERANCE_GOOD = 0.10
MUSIC_LATENCY = -0.35

# Assets

ASSET_DIR = ""
FONTS_DIR = os.path.join(ASSET_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSET_DIR, "music")
SFX_DIR = os.path.join(ASSET_DIR, "sfx")
SPRITES_DIR = os.path.join(ASSET_DIR, "sprites")

FONT_NAME = "PixelifySans"

FONT_PATH = os.path.join(FONTS_DIR, FONT_NAME, f"{FONT_NAME}.ttf")
PLAYER_SHEET = os.path.join(SPRITES_DIR, "player_sheet_24x24.png")
TILESET = os.path.join(SPRITES_DIR, "tileset_16x16.png")
OBSTACLES_SPR = os.path.join(SPRITES_DIR, "obstacles_24x24.png")
BG_LAYER0 = os.path.join(SPRITES_DIR, "bg_layer0.png")
BG_LAYER1 = os.path.join(SPRITES_DIR, "bg_layer1.png")
BG_LAYER2 = os.path.join(SPRITES_DIR, "bg_layer2.png")
FG_LAYER = os.path.join(SPRITES_DIR, "fg_layer.png")
MASCOT_SHEET = os.path.join(SPRITES_DIR, "mascot_sheet_24x24.png")
TITLE_LOGO = os.path.join(SPRITES_DIR, "title_logo.png")
TITLE_MUSIC = os.path.join(SFX_DIR, "title_theme.ogg")

TRACKS = [
	("BackToBlack.ogg", "Amy Winehouse - Back to Black", 123),
	("DJGotUsFallinInLove.ogg", "Usher - DJ Got Us Fallin' In Love", 120),
	("GimmeGimmeGimme.ogg", "ABBA - Gimme Gimme Gimme!", 120),
	("OnlySoMuchOilInTheGround.ogg", "Stefanie Heinzmann - Only So Much Oil In The Ground", 121),
	("ShizumeruMachi.ogg", "YOEKO - Sinking Town", 125),
]

# Colours

BACKGROUND_COLOUR = (30, 34, 45)
GROUND_COLOUR = (120, 100, 80)
TEXT_COLOUR = (240, 240, 235)
BEAT_BAR_BG = (60, 50, 40)
BEAT_BAR_COLOUR = (212, 163, 115)

# UI relative sizes

BEAT_BAR_WIDTH_FRAC = 0.325 # fraction of window width

BEAT_BAR_HEIGHT = max(12, int(WINDOW_HEIGHT * 0.022))
UI_MARGIN_FRAC = 0.025 # fraction of window width for margins

# CAPTION = "One-Button Rhythm Dodger"
# GROUND_Y = WINDOW_HEIGHT - 80
# PLAYER_WIDTH = 40
# PLAYER_HEIGHT = 60
# PLAYER_X = 120

# GRAVITY = 2000.0
# JUMP_VELOCITY = -900.0

# OBSTACLE_WIDTH = 40
# OBSTACLE_MIN_HEIGHT = 40
# OBSTACLE_MAX_HEIGHT = 120
# OBSTACLE_SPEED = 400.0

# OBSTACLE_SPACING_MIN = 3
# OBSTACLE_SPACING_MAX = 5

# BPM = 90
# BEAT_INTERVAL = 60.0 / BPM
# BEAT_TOLERANCE = 0.12 # the time window for 'on beat'/perfect timing

# PERFECT_WINDOW = 0.05
# GOOD_WINDOW = 0.10

# FONT = "PixelifySans"

# BACKGROUND_COLOUR = (15, 15, 15)
# GROUND_COLOUR = (40, 40, 40)
# PLAYER_COLOUR = (80, 200, 255)
# OBSTACLE_COLOUR = (255, 80, 120)
# TEXT_COLOUR = (230, 230, 240)
# BEAT_BAR_COLOUR = (120, 255, 160)
# BEAT_BAR_BG = (40, 70, 60)
# FLASH_COLOUR_PERFECT = (255, 185, 0)
# FLASH_COLOUR_GOOD = (120, 255, 160)
# FLASH_COLOUR_BAD = (231, 72, 86)
# FLASH_ALPHA = 50

# # Music / track selection

# MUSIC_FOLDER = "music"
# TRACKS = [
# 	("BackToBlack.ogg", "Amy Winehouse - Back to Black", 123),
# 	("DJGotUsFallinInLove.ogg", "Usher - DJ Got Us Fallin' In Love", 120),
# 	("GimmeGimmeGimme.ogg", "ABBA - Gimme Gimme Gimme!", 120),
# 	("OnlySoMuchOilInTheGround.ogg", "Stefanie Heinzmann - Only So Much Oil In The Ground", 121),
# 	("ShizumeruMachi.ogg", "YOEKO - Sinking Town", 125),
# ]
# # small calibration offset to compensate for audio playback latency
# MUSIC_LATENCY = 0.0 # to tune