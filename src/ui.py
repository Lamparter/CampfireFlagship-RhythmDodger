import pygame

def draw_panel(surface, rect, bg_colour, border_colour, border=2):
	pygame.draw.rect(surface, border_colour, rect)
	inner = rect.inflate(-border*2, -border*2)
	pygame.draw.rect(surface, bg_colour, inner)

def render_text(font, text, colour):
	return font.render(text, True, colour)