import pygame, sys
from os import path

pygame.init()

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 550

MENU_WIDTH = 350
MENU_HEIGHT = 365

LINES_TO_DRAW = 16
MAX_LINES_DRAWABLE = 17

PROGRAM_TITLE = "Swiftkey Soundboard"

First_time_message = "Thank you for using Swiftkey Soundboard, feel free to reach me through my Discord channel https://discord.gg/36nEUmg where I also upload other projects I've been working on"

DATA_LOC = "Data/"
#DATA_LOC = __file__

QUEUE = path.join(path.dirname(__file__),  DATA_LOC + "Queue.wav")
STACK = path.join(path.dirname(__file__),  DATA_LOC + "Stack.wav")
REPLACE = path.join(path.dirname(__file__),  DATA_LOC + "Replace.wav")

BACK = pygame.image.load( path.join(path.dirname(__file__), DATA_LOC + "back.png") )
ICON_PNG = pygame.image.load(path.join(path.dirname(__file__), DATA_LOC + "icon.png") )
ICO = path.join(path.dirname(__file__), DATA_LOC + "icon.ico")



#Colors Definitions
COLOR_BLACK = (0,0,0)
COLOR_WHITE = (254, 254, 254)
COLOR_GREY = (100, 100, 100)
COLOR_LIGHT_GREY_2 = (140, 140, 140)
COLOR_LIGHT_GREY = (175, 175, 175)
COLOR_GREY_68 = (68, 68, 68)
COLOR_DARK_GREY = (50, 50, 50)
COLOR_VERY_DARK_GREY = (20, 20, 20)
COLOR_RED = (130,0,0)
COLOR_LIGHT_RED = (220,0,0)
COLOR_VERY_LIGHT_RED = (255, 100, 100)
COLOR_GOLD = (255,223,0)
COLOR_PINK = (255,105,180)
COLOR_LIGHT_GREEN = (124,252,0)
COLOR_GREEN = (45,200,45)
COLOR_DARK_GREEN = (34,139,34)
COLOR_DARK_TEAL = (0, 153, 153)
COLOR_LIGHT_BLUE = (65, 105, 225)
COLOR_BLUE = (0, 102, 204)
COLOR_DARK_BLUE = (0, 0, 175)
COLOR_BRIGHT_PINK = (255,0,255)
COLOR_ORANGE = (255,165,0)
COLOR_RED_TINT = (255,0,0,.9)
COLOR_INDIGO = (75,0,130)
COLOR_PURPLE = (138,43,226)
COLOR_BROWN = (139,69,19)
COLOR_BROWN_2 = (170,100,40)
COLOR_LIGHT_BROWN = (205,133,63)
COLOR_TAN = (210, 180, 140)

font_loc = path.join(path.dirname(__file__), DATA_LOC + "libel-suit-rg.ttf")
FONT_DEFAULT = pygame.font.Font(font_loc, 16)
FONT_MENU = pygame.font.Font(font_loc, 20)
FONT_LARGE = pygame.font.Font(font_loc, 26)

font_dict = {
	
	"FONT_DEFAULT" : FONT_DEFAULT,
	"FONT_LARGE" : FONT_LARGE,
	"FONT_MENU" : FONT_MENU

}