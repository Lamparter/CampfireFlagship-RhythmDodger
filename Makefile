PYTHON ?= python3
WEB_WIDTH ?= 960
WEB_HEIGHT ?= 540

.PHONY: web-build web-run

web-build:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pygbag --build --ume_block 0 --width $(WEB_WIDTH) --height $(WEB_HEIGHT) .
	$(PYTHON) scripts/fix_web_index.py build/web/index.html

web-run:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pygbag --build --ume_block 0 --width $(WEB_WIDTH) --height $(WEB_HEIGHT) .
	$(PYTHON) scripts/fix_web_index.py build/web/index.html
	$(PYTHON) -m pygbag --ume_block 0 --width $(WEB_WIDTH) --height $(WEB_HEIGHT) .
