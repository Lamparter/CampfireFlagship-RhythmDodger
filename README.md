# `CampfireFlagship-RhythmDodger`

*Simple rhythm dodger game for Campfire Flagship*

---

- **Player**: 24×24 sprite sheet (rows = states, columns = frames). Simple idle/jump/land frames.
- **Tiles**: 16×16 tileset for ground; repeated horizontally.
- **Background**: 3 parallax layers (bg_layer0..2) + foreground.
- **Audio**: music tracks in `assets/music/` with correct BPM; SFX in `assets/sfx/`.
- **Polish**: particles, squash/stretch, beat‑synced pulses, judgement text, mascot reactions, day/night tint, weather, post‑game stats and ranks.

### Disclaimer

**This game may use copyrighted audio, as found in the `music/` and `sfx/` folders, which is justifiable given that the game is intended for *personal use only*. Do NOT publish the game with these audio files present, and instead use royalty-free ones.**

---

## Running

- Desktop: `python main.py`

## Web build (PyGBag)

This codebase now includes a web-safe game loop and launcher so it can be compiled for browser targets.

1. Setup + build in one command:
	- `make web-build`
2. Serve/run locally (also one command, includes setup):
	- `make web-run`

Optional size override:
- `make web-build WEB_WIDTH=1280 WEB_HEIGHT=720`

Notes:
- The browser build uses `main.py` at repo root as the entry point.
- Audio may be muted until browser user interaction (browser policy).
- Build step applies a small `index.html` patch to remove debug panes and prevent horizontal page scroll.