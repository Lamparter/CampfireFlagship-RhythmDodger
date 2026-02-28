#!/usr/bin/env python3
from pathlib import Path
import sys


def apply_replacements(text: str) -> str:
	replacements = [
		("ume_block : 1", "ume_block : 0"),
		("gui_debug : 2", "gui_debug : 0"),
		("body {", "body {\n            overflow: hidden;\n            width: 100vw;\n            height: 100vh;"),
		("</style>", "\n        #pyconsole, #crt { display: none !important; }\n    </style>"),
	]
	for old, new in replacements:
		text = text.replace(old, new)
	return text


def main() -> int:
	if len(sys.argv) != 2:
		print("usage: fix_web_index.py <path-to-index.html>")
		return 1

	path = Path(sys.argv[1])
	if not path.exists():
		print(f"missing file: {path}")
		return 1

	original = path.read_text(encoding="utf-8")
	updated = apply_replacements(original)
	if updated != original:
		path.write_text(updated, encoding="utf-8")
		print(f"patched {path}")
	else:
		print(f"no changes needed for {path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
