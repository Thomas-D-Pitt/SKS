import constants
import pygame

class ui_button:

	def __init__(self, surface, coords, size, text, click_function = None, click_function_params = None,
	 text_color = constants.COLOR_RED, color_box = constants.COLOR_GREY,
	  color_mouseover = constants.COLOR_LIGHT_GREY, pos_from_center = False, font = "FONT_MENU", sprite = None):

		self.surface = surface
		self.coords = coords
		self.size = size
		self.text = text
		self.font = font
		self.click_function = click_function
		self.text_color = text_color
		self.color_box = color_box
		self.color_mouseover = color_mouseover
		self.pos_from_center = pos_from_center
		self.click_function_params = click_function_params
		self.sprite = sprite

		

		self.rect = pygame.Rect(coords, size)

		if self.pos_from_center == True:
			self.rect.center = self.center(coords)

			w, h = self.size
			x, y = self.rect.center
			x -= w/2
			y -= h/2

			self.coords = (x,y)


	@property
	def is_highlighted(self):

		x, y = self.coords
		w,h = self.size

		return (mouse_in_window(x, y, w, h) != None)

	def center(self, coords):

		x,y = coords

		x += constants.WINDOW_WIDTH/2
		y += constants.WINDOW_HEIGHT/2

		return (x,y)

	def draw(self):

		global MOUSE_CLICKED

	

		if self.is_highlighted:
			color = self.color_mouseover
		else:
			color = self.color_box

		if self.sprite:

			w,h = self.size
			x,y = self.coords 

			button_center = (w/2 + x, h/2 + y)

			d_x, d_y = button_center

			d_x -= constants.GAME_TILE_SIZE/2
			d_y -= constants.GAME_TILE_SIZE/2

			d_coords = (d_x, d_y)

			pygame.draw.rect(self.surface, color, self.rect)
			self.surface.blit(self.sprite, d_coords)
		else:

			pygame.draw.rect(self.surface, color, self.rect)
			draw_text(self.surface, self.text, self.rect.center, self.text_color, center = True, font = self.font)

		if self.is_highlighted == True:
			if MOUSE_CLICKED == True:

				MOUSE_CLICKED = False

				if self.click_function:
					
					if self.click_function == "RETURN":

						return "END"

					elif self.click_function_params:
						self.click_function(*self.click_function_params)


					else:
						self.click_function()


					return "END"
				else:
					return "END"




		return None

class ui_slider:

	def __init__(self, surface, coords, size, fill = .5, bg_color = constants.COLOR_LIGHT_GREY, fg_color = constants.COLOR_RED,
	 pos_from_center = False, text = "", draw_percent_text = True):

		self.surface = surface
		self.coords = coords
		self.size = size
		self.bg_color = bg_color
		self.fg_color = fg_color
		self.pos_from_center = pos_from_center
		self.fill = fill
		self.text = text
		self.draw_percent_text = draw_percent_text

		if self.text != "":
			self.text = self.text + ": "
		
		self.bg_rect = pygame.Rect((0,0), size)
		self.bg_rect.center = coords

		self.fg_rect = pygame.Rect((0,0), (self.bg_rect.width * self.fill, self.bg_rect.height))
		self.fg_rect.topleft = self.bg_rect.topleft

		if self.pos_from_center == True:
			self.bg_rect.center = self.center(coords)
			self.fg_rect.center = self.center(coords)

			w, h = self.size
			x, y = self.bg_rect.center
			x -= w/2
			y -= h/2

			self.coords = (x,y)

	@property
	def is_highlighted(self):

		x, y = self.coords
		w,h = self.size

		buffer = 20
		return (mouse_in_window(x-buffer, y, w+2*buffer, h) != None)

	def center(self, coords):

		x,y = coords

		x += constants.WINDOW_WIDTH/2
		y += constants.WINDOW_HEIGHT/2

		return (x,y)

	def update(self):

		mouse_down = pygame.mouse.get_pressed()[0]

		mouse_x, mouse_y = pygame.mouse.get_pos()

		if self.is_highlighted and mouse_down:

			dis = (mouse_x - self.bg_rect.left)
			width = (self.bg_rect.width)

			self.fill = util.clamp((float(mouse_x) - float(self.bg_rect.left)) / self.bg_rect.w, 0, 1)
			

			self.fg_rect.width =  self.bg_rect.width * self.fill

		return self.fill


			

	def draw(self):

		pygame.draw.rect(self.surface, self.bg_color, self.bg_rect)
		self.fg_rect.topleft = self.bg_rect.topleft
		pygame.draw.rect(self.surface, self.fg_color, self.fg_rect)

		if self.draw_percent_text:
			util.draw_text(self.surface, self.text + str(int(self.fill * 100)), self.bg_rect.center, constants.COLOR_BLUE, center = True)

		else:
			util.draw_text(self.surface, self.text, self.bg_rect.center, constants.COLOR_BLUE, center = True)

		
		

		return None

class ui_inputbox:

    def __init__(self, x, y, w, h, text='', pos_from_center = False, back_color = constants.COLOR_BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = constants.COLOR_LIGHT_GREY
        self.text = text
        self.txt_surface = constants.FONT_DEFAULT.render(text, True, self.color)
        self.active = False
        self.pos_from_center = pos_from_center
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.back_surface = pygame.Surface((w - 20, h))
        self.back_surface.fill(back_color)


        if self.pos_from_center == True:


			x += constants.WINDOW_WIDTH/2
			y += constants.WINDOW_HEIGHT/2

			self.rect.center = (x,y)

			x -= w/2
			y -= h/2

			self.x = x
			self.y = y

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = constants.COLOR_LIGHT_GREY if self.active else constants.COLOR_DARK_GREY
        if event.type == pygame.KEYDOWN:

            if self.active:

                if event.key == pygame.K_RETURN:
                    
                    self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = constants.FONT_DEFAULT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
    	screen.blit(self.back_surface, (self.rect.x, self.rect.y))
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

	

def mouse_in_window(x, y, width, height):

	mouse_x, mouse_y = pygame.mouse.get_pos()

	mouse_x = int(mouse_x)
	mouse_y = int(mouse_y)

	rel_x = mouse_x - x
	rel_y = mouse_y - y
	if (rel_x > 0 and rel_y > 0) and (rel_x < width and rel_y < height):
		return (rel_x, rel_y)
	else:
		return None

def draw_text(display_surface, text, t_coords, color = constants.COLOR_WHITE, back_color = None, font = "FONT_DEFAULT", center = False, flip = False):

	text_surf, text_rect = helper_text_objects(text, color, back_color, font)

	if not center:
		text_rect.topleft = t_coords
	else:
		text_rect.center = t_coords

	if flip:
		text_surf = pygame.transform.flip(text_surf, False, True)

	display_surface.blit(text_surf, text_rect)


def helper_text_objects(inc_text, inc_color, inc_bg, font1 = "FONT_DEFAULT"):

	font = constants.font_dict[font1]

	if inc_bg:
		Text_surface = font.render(" " + inc_text + " ", False, inc_color, inc_bg)

	else:
		Text_surface = font.render(inc_text, False, inc_color)

	return Text_surface, Text_surface.get_rect()

def helper_text_height(font1 = "FONT_DEFAULT"):

	font = constants.font_dict[font1]

	font_object = font.render('A', False, (0,0,0))
	font_rect = font_object.get_rect()

	return font_rect.height

def helper_text_width(text, font):

	font = constants.font_dict[font]

	font_object = font.render(text, False, (0,0,0))
	font_rect = font_object.get_rect()

	return font_rect.width