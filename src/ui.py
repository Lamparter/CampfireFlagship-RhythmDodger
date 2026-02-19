import pygame

def draw_panel(surface, rect, bg_colour, border_colour, border=2):
	pygame.draw.rect(surface, border_colour, rect)
	inner = rect.inflate(-border*2, -border*2)
	pygame.draw.rect(surface, bg_colour, inner)

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
		# background
		bg = self.hover and self.hover_bg or self.bg
		pygame.draw.rect(surf, self.border, self.rect.inflate(4,4), border_radius=self.radius)
		pygame.draw.rect(surf, bg, self.rect, border_radius=self.radius)

		# text
		self.text_rect = self.text_surf.get_rect(center=self.rect.center)
		surf.blit(self.text_surf, self.text_rect)

		# focus indicator
		if self.focus:
			pygame.draw.rect(surf, (255,255,255,30), self.rect, width=2, border_radius=self.radius)