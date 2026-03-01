import pygame
import helpers

def draw_panel(
	surf,
	rect,
	bg_colour,
	border_colour,
	*,
	radius=12,
	subtitle=None,
	subtitle_font=None,
	subtitle_colour=(180, 170, 160),
	subtitle_offset=20
):
	# panel border
	pygame.draw.rect(
		surf,
		border_colour,
		rect.inflate(4, 4),
		border_radius=radius
	)

	# panel background
	pygame.draw.rect(
		surf,
		bg_colour,
		rect.inflate(4, 4),
		border_radius=radius
	)

	# optional subtitle
	if subtitle and subtitle_font:
		subtitle_surf = subtitle_font.render(subtitle, True, subtitle_colour)
		subtitle_x = rect.centerx - subtitle_surf.get_width() // 2
		subtitle_y = rect.bottom + subtitle_offset
		surf.blit(subtitle_surf, (subtitle_x, subtitle_y))

def render_text(font, text, colour):
	return font.render(text, True, colour)

class Button:
	def __init__(self, rect, text, font: pygame.font.Font, on_click, *,
			  	bg=(250,244,238), fg=(40,34,30), border=(220,200,190),
				hover_bg=(255,245,235), radius=10, padding=8, id=None):
		self.rect = pygame.Rect(rect)
		self.text = text
		self.font = font
		self.on_click = on_click
		self.bg = bg
		self.fg = fg
		self.border = border
		self.hover_bg = hover_bg
		self.radius = radius
		self.padding = padding
		self.hover = False
		self.focus = False
		self.enabled = True
		self.id = id

		self._render_text()

	def _render_text(self):
		self.text_surf = self.font.render(self.text, True, self.fg)
		self.text_rect = self.text_surf.get_rect(center=self.rect.center)
	
	def set_text(self, text):
		self.text = text
		self._render_text()
	
	def handle_event(self, event):
		if not self.enabled:
			return False
		if event.type == pygame.MOUSEMOTION:
			self.hover = self.rect.collidepoint(event.pos)
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.rect.collidepoint(event.pos):
				self._click()
				return True
		elif event.type == pygame.KEYDOWN and self.focus:
			if event.key in (pygame.K_RETURN, pygame.K_SPACE):
				self._click()
				return True
	
	def _click(self):
		if callable(self.on_click):
			self.on_click(self)
	
	def draw(self, surf):
		# background colour changes when focused or hovered
		if self.focus or self.hover:
			bg = (255, 245, 235) # warmer when focused
			border_col = (255, 200, 120)
		else:
			bg = self.bg
			border_col = self.border
		
		# draw border and background
		pygame.draw.rect(surf, border_col, self.rect.inflate(6,6), border_radius=self.radius)
		pygame.draw.rect(surf, bg, self.rect, border_radius=self.radius)

		# subtle glow when focused
		if self.focus or self.hover:
			glow = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
			glow.fill((255, 220, 160, 40))
			surf.blit(glow, self.rect.topleft, special_flags=pygame.BLEND_RGBA_ADD)

		# text
		self.text_rect = self.text_surf.get_rect(center=self.rect.center)
		surf.blit(self.text_surf, self.text_rect)

		# focus indicator outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=3, border_radius=self.radius)

class ToggleSwitch:
	def __init__(self, rect, value=False, radius=10,
			  	on_colour=(200, 160, 120),
				off_colour=(120, 120, 120),
				text_colour=(40, 34, 30),
				font=None):
		self.rect = pygame.Rect(rect)
		self.value = bool(value)
		self.radius = radius
		self.on_colour = on_colour
		self.off_colour = off_colour
		self.text_colour = text_colour
		self.font = font

		self.hover = False
		self.focus = False
		self.on_change = None
	
	def handle_event(self, e):
		if e.type == pygame.MOUSEMOTION:
			self.hover = self.rect.collidepoint(e.pos)
		elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
			if self.rect.collidepoint(e.pos):
				self.toggle()
				return True
		elif e.type == pygame.KEYDOWN and self.focus:
			if e.key in (pygame.K_RETURN, pygame.K_SPACE):
				self.toggle()
				return True
		return False
	
	def toggle(self):
		self.value = not self.value
		print(f"[DEBUG] Value of {self} set to {self.value}")
		if callable(self.on_change):
			self.on_change(self.value)
	
	def draw(self, surf):
		# background colour
		bg = self.on_colour if self.value else self.off_colour

		# draw box
		pygame.draw.rect(surf, bg, self.rect, border_radius=self.radius)

		# focus outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=2, border_radius=self.radius)
		
		# ON/OFF text
		if self.font:
			txt = "ON" if self.value else "OFF"
			txt_surf = self.font.render(txt, True, self.text_colour)
			txt_rect = txt_surf.get_rect(center=self.rect.center)
			surf.blit(txt_surf, txt_rect)

class Slider:
	def __init__(self, rect, minv=0.0, maxv=1.0, value=0.0):
		self.rect = pygame.Rect(rect)
		self.minv = float(minv)
		self.maxv = float(maxv)
		self.value = float(value)
		self.dragging = False
		self.focus = False
		self.on_change = None
	
	def handle_event(self, e):
		# mouse down -> start dragging
		if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
			if self.rect.collidepoint(e.pos):
				self.dragging = True
				self._set_from_pos(e.pos[0])
				return True

		# mouse up -> stop dragging
		elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
			self.dragging = False
		
		# mouse move while dragging
		elif e.type == pygame.MOUSEMOTION and self.dragging:
			self._set_from_pos(e.pos[0])
			return True
		
		# keyboard control when focused
		elif e.type == pygame.KEYDOWN and self.focus:
			step = (self.maxv - self.minv) * 0.02
			if e.key == pygame.K_LEFT:
				self.set(self.value - step)
				return True
			elif e.key == pygame.K_RIGHT:
				self.set(self.value + step)
				return True
		return False
	
	def _set_from_pos(self, x):
		t = (x - self.rect.x) / max(1, self.rect.w)
		val = self.minv + t * (self.maxv - self.minv)
		self.set(val)
	
	def set(self, v):
		old = self.value
		self.value = max(self.minv, min(self.maxv, v))
		print(f"[DEBUG] Value of {self} set to {self.value}")
		if self.on_change and self.value != old:
			self.on_change(self.value)
	
	def draw(self, surf):
		# track
		track_rect = pygame.Rect(self.rect.x, self.rect.centery - 4, self.rect.w, 8)
		pygame.draw.rect(surf, (80, 80, 84), track_rect, border_radius=6)

		# thumb
		t = (self.value - self.minv) / (self.maxv - self.minv) if self.maxv != self.minv else 0
		thumb_x = int(self.rect.x + t * self.rect.w)
		thumb_rect = pygame.Rect(thumb_x - 8, self.rect.centery - 12, 16, 24)
		pygame.draw.rect(surf, (200, 160, 120), thumb_rect, border_radius=6)

		# focus outline
		if self.focus:
			pygame.draw.rect(surf, (255, 210, 140), self.rect, width=2, border_radius=8)

class TextInput:
	def __init__(self, rect, text="", font=None):
		self.rect = pygame.Rect(rect)
		self.text = str(text)
		self.font = font
		self.focus = False
		self.cursor = 0

	def handle_event(self, e):
		if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
			self.focus = self.rect.collidepoint(e.pos)
			return self.focus
		if not self.focus:
			return False
		if e.type == pygame.KEYDOWN:
			if e.key == pygame.K_BACKSPACE:
				self.text = self.text[:max(0, self.cursor-1)] + self.text[self.cursor:]
				self.cursor = max(0, self.cursor-1)
				return True
			elif e.key == pygame.K_LEFT:
				self.cursor = max(0, self.cursor-1)
				return True
			elif e.key == pygame.K_RIGHT:
				self.cursor = min(len(self.text), self.cursor+1)
				return True
			elif e.key == pygame.K_RETURN:
				self.focus = False
				return True
			else:
				if e.unicode:
					self.text = self.text[:self.cursor] + e.unicode + self.text[self.cursor:]
					self.cursor += 1
					return True
		return False
	
	def draw(self, surf):
		pygame.draw.rect(surf, (245,240,235), self.rect, border_radius=8)
		txt = self.font.render(self.text, True, (40,34,30))
		surf.blit(txt, (self.rect.x + 8, self.rect.y + (self.rect.h - txt.get_height())//2))
		if self.focus:
			pygame.draw.rect(surf, (255,210,140), self.rect, width=2, border_radius=8)