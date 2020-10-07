import pygame
import pythoncom, pyHook
import Tkinter as tk
import tkFileDialog
import gzip, pickle
import pyaudio, sys
import pydub
from pydub.utils import make_chunks
from sys import exit
from os import path
import random

import constants as const
import util

class loader_file():
	""" 
	the object saved, it stores the settings objects that make up each profile, also handles switching between profiles
	"""
	def __init__(self):

		self.profiles = []
		self.current_profile = 0

		#create 5 default profiles, they are overwritten if a save is loaded
		for n in range(5):
			self.profiles.append(user_settings())

	@property
	def settings(self):
		#returns the settings object that is currently in use
		return self.profiles[self.current_profile]
	

	def next_profile(self):
		self.current_profile += 1
		if self.current_profile > 4:
			self.current_profile = 0

	def set_profile(self, profile):
		self.current_profile = profile



class user_settings():
	"""
	stores all the program settings, including keybinds
	"""
	def __init__(self):
		self.key_binds = []
		self.delay = 5#ms between each frame
		self.target_fps = None #I am not currently using this
		self.audio_chunk_size = 25 #ms of audio added to queue each frame
		self.double_tap_speed = 500 #wait period to determine if a button was double tapped
		self.hook_keys = True #are we capturing all key events
		self.mute = False
		self.output_device = None
		self.local_audio_device = None
		self.equalize_audio = True
		self.equalize_target = -25
		self.out_volume = 0
		self.local_volume = 0
		self.play_local = False
		self.queue = "Queue" # can be Queue, Stack, or Replace; determines how multiple events should be handled

		self.old_hook = None # used to restore setting after a temporary enable/disable

		#default keybinds in each profile
		kb = key_bind()
		kb.name = "Toggle Enabled"
		kb.call_function = toggle_muted
		kb.double_call_func = None
		self.key_binds.append(kb)

		kb2 = key_bind()
		kb2.name = "Stop Playback"
		kb2.call_function = stop_oldest_audio
		kb2.double_call_func = stop_all_audio
		kb2.cycle_reset_timer = 500
		self.key_binds.append(kb2)

		kb3 = key_bind()
		kb3.name = "Toggle Queue Settings"
		kb3.call_function = cycle_queue_audio
		kb3.double_call_func = None
		self.key_binds.append(kb3)

	def toggle_HM(self, val = None):
		#temporarly set the hook_keys property
		if val != None:

			if self.old_hook:
				self.hook_keys = self.old_hook
				self.old_hook = None

			self.old_hook = self.hook_keys
			
			if val == True:
				HMK.HookKeyboard()
				self.hook_keys = True
			else:
				HMK.UnhookKeyboard()
				self.hook_keys = False
		else:
			
			if self.old_hook:
				self.hook_keys = self.old_hook
				self.old_hook = None

			if LOADER_FILE.settings.hook_keys == True:
					HMK.HookKeyboard()
			else:
				HMK.UnhookKeyboard()
 
def cycle_queue_audio():
	#cycle through each option for user_settings.queue and play a notification 
	stop_all_audio()
	if LOADER_FILE.settings.queue == "Queue":
		LOADER_FILE.settings.queue = "Stack"
		play_audio(const.STACK, local = True)

	elif LOADER_FILE.settings.queue == "Stack":
		LOADER_FILE.settings.queue = "Replace"
		play_audio(const.REPLACE, local = True)
	else:
		LOADER_FILE.settings.queue = "Queue"
		play_audio(const.QUEUE, local = True)

	

class key_bind():

	"""
	A keybind event that stores data of what it should do when pressed as well as user information
	"""


	name = "Untitled"
	keybind_desc = ""
	keybind_readable = ""
	keybind = [] #array of keys that will triger this keybind
	audio_paths = []
	cycle = False #if multiple file in audio paths and not cycle then a random file will be picked
	cycle_pos = 0
	cycle_reset_timer = 0 #in ms/ticks
	last_played = None

	volume_adjust = 0

	call_function = None
	double_call_func = None #what should happen if keybind is called twice in short succession

	@property
	def desc(self):
		if self.keybind_desc:
			return self.keybind_desc
		else:
			return str(self.keybind_readable).replace("[", "").replace("]", "").replace("'", "")
	

	def get_track(self):
		# gets the next track to play based on keybind settings, such as cycle and cycle reset timer
		current_time = pygame.time.get_ticks()
		if len(self.audio_paths) > 1:

			if self.cycle == True:
				if self.cycle_reset_timer > 0: #check if we need to reset cycle
					

					if self.last_played and self.last_played + self.cycle_reset_timer > current_time: #dont reset
						self.last_played = current_time
						self.cycle_pos += 1
						if self.cycle_pos > len(self.audio_paths) - 1:
							self.cycle_pos = 0
						return self.audio_paths[self.cycle_pos]

					else: #reset cycle pos
						self.last_played = current_time
						self.cycle_pos = 0
						return self.audio_paths[0]

				else:
					self.last_played = current_time
					self.cycle_pos += 1
					if self.cycle_pos > len(self.audio_paths) - 1:
						self.cycle_pos = 0
					return self.audio_paths[self.cycle_pos - 1]

			else: #pick random path
				self.last_played = current_time
				i = random.randint(0, len(self.audio_paths) - 1)
				return self.audio_paths[i]


		else:
			self.last_played = current_time
			return self.audio_paths[0]

	def reset_cycle(self):
		self.cycle_pos = 0
		self.last_played = None
		if len(self.audio_paths) >= 1:
			play_audio(self.get_track(), self.volume_adjust)

def find_keybind(keys):
	#check to see if key event is bound to a keybind class, returns keybind class if found
	for keybind in LOADER_FILE.settings.key_binds:
		if keybind.keybind == keys:
			return keybind
			break

def key_event(keys, index = None):
	#checks if pressed keys correspond with a keybind class, if so call function or play audio set to that keybind
	if index:
		kb = LOADER_FILE.settings.key_binds[index]
	else:
		kb = find_keybind(keys)

	if kb:
		
		if kb.call_function:
			now = pygame.time.get_ticks()
			if kb.double_call_func and kb.last_played and kb.last_played + kb.cycle_reset_timer > now:
				kb.double_call_func()
				kb.last_played = now
			else:
				kb.call_function()
				kb.last_played = now
		else:
			now = pygame.time.get_ticks()
			if kb.last_played and kb.last_played + LOADER_FILE.settings.double_tap_speed > now:
				kb.reset_cycle()
			else:
				if len(kb.audio_paths) >= 1:
					play_audio(kb.get_track(), kb.volume_adjust)

		return True
	else:
		return False


class file_selector():

	"""
	select a file, to use it an instance of this class must be created, then *file_selector*.run must be called, returns file path as string
	"""

	val = None

	def __init__(self):

		self.selector_root = tk.Tk()
		self.selector_root.withdraw()
		self.selector_root.iconbitmap(const.ICO)
		self.selector_root.wm_attributes("-topmost", 1)
		#self.selector_root.bind("<FocusOut>", self.refocus)
		
		self.created_time = pygame.time.get_ticks()
		self.myfiletypes = [('Usable files', '*.wav'), ('All files', '*')]
		self.open = tkFileDialog.Open(self.selector_root, filetypes = self.myfiletypes)

		tk.Button(self.selector_root, text="Open File Dialog", command=self.openwindows).pack()

		self.statusbar = tk.Label(self.selector_root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
		self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

	def refocus(self, event):
		if (self.created_time + 500) < pygame.time.get_ticks():
			self.selector_root.bell()
		self.selector_root.focus_force()
        #

	def run(self):
		self.val = self.open.show()
		#self.statusbar.config(text = self.val)
		self.selector_root.destroy()
		return self.val

	def openwindows(self):
		self.val = self.open.show()
		self.statusbar.config(text = self.val)

class settings_menu():
	"""
	settings menu using tkinter library
	"""


	val = None

	def __init__(self):
		found = False
		for obj in ONGOING_FUNCTIONS:
			if obj.__class__.__name__ == self.__class__.__name__:
				found = True

		if found == False:

			self.root = tk.Tk(sync = False)
			#self.root.iconbitmap(const.ICO)
			self.root.title("Settings")
			self.root.protocol("WM_DELETE_WINDOW", self.end)
			#self.root.wm_attributes("-topmost", 1)
			#self.root.bind("<FocusOut>", self.refocus)
			self.created_time = pygame.time.get_ticks()


			self.mainframe = tk.Frame(self.root)
			self.mainframe.grid(column=0,row=0, sticky=(tk.N,tk.W,tk.E,tk.S) )
			self.mainframe.columnconfigure(0, weight = 1)
			self.mainframe.rowconfigure(0, weight = 1)
			self.mainframe.pack(pady = 15, padx = 5)

			#delay settings
			self.delay_lbl = tk.Label(self.mainframe, text = "Delay timer")
			CreateToolTip(self.delay_lbl, "The amount of time that should be waited between each frame, large numbers will cause the program to run slowly, small numbers may cause the program to use more cpu power than necessary")
			self.delayvar = tk.StringVar(self.mainframe)
			self.delayvar.set(LOADER_FILE.settings.delay)
			self.delay_Text = tk.Entry(self.mainframe, textvariable = self.delayvar)

			self.delay_lbl.grid(row = 1, column = 1)
			self.delay_Text.grid(row = 1, column = 2, columnspan = 2)

			#delay settings
			self.chunk_lbl = tk.Label(self.mainframe, text = "Chunk Size")
			CreateToolTip(self.chunk_lbl, "The amount of audio (in ms) processed each frame, if this is shorter than your time between frames audio tearing will occur, large numbers may cause the program to lag, (1/fps ~ chunk size/1000)")
			self.chunkvar = tk.StringVar(self.mainframe)
			self.chunkvar.set(LOADER_FILE.settings.audio_chunk_size)
			self.chunk_Text = tk.Entry(self.mainframe, textvariable = self.chunkvar)

			self.chunk_lbl.grid(row = 2, column = 1)
			self.chunk_Text.grid(row = 2, column = 2, columnspan = 2)

			#audio output selection
			self.dropdown_output_var = tk.StringVar(self.mainframe)
			self.dropdown_local_var = tk.StringVar(self.mainframe)
			choices = []
			dropdown_var_start = None

			for i in range(PA.get_device_count()):
				self.f = pydub.AudioSegment.from_wav(str(const.QUEUE), "rb")
				try:
					#check to see if we can use device for output
					self.stream = PA.open(format = PA.get_format_from_width(self.f.sample_width),
						channels = self.f.channels,
						rate = self.f.frame_rate,
						output = True, output_device_index = i)

					choices.append(PA.get_device_info_by_index(i)["name"])

					if PA.get_device_info_by_index(i)["name"] == LOADER_FILE.settings.output_device:
						self.dropdown_output_var.set(PA.get_device_info_by_index(i)["name"])

					if PA.get_device_info_by_index(i)["name"] == LOADER_FILE.settings.local_audio_device:
						self.dropdown_local_var.set(PA.get_device_info_by_index(i)["name"])

				except IOError:
					# "Invalid Output Device" dont add to list
					pass
				

				

			self.output_menu = tk.OptionMenu(self.mainframe, self.dropdown_output_var, *choices)
			
			self.local_menu = tk.OptionMenu(self.mainframe, self.dropdown_local_var, *choices)
			

			self.dropdown_output_var.trace('w', self.change_dropdown_output)
			self.dropdown_local_var.trace('w', self.change_dropdown_local)

			self.output_lbl = tk.Label(self.mainframe, text = "Output Device")
			CreateToolTip(self.output_lbl, "The device audio is played into")
			self.local_lbl = tk.Label(self.mainframe, text = "Local Audio Device")
			CreateToolTip(self.local_lbl, "The device used for user notifications, if left blank Output Device will be used")

			self.output_lbl.grid(row = 3, column = 1)
			self.output_menu.grid(row = 3, column = 2, columnspan = 2)

			self.local_lbl.grid(row = 4, column = 1)
			self.local_menu.grid(row = 4, column = 2, columnspan = 2)

			choices = ["Queue", "Stack", "Replace"]
			self.dropdown_queue = tk.StringVar(self.mainframe)
			self.dropdown_queue.trace('w', self.change_dropdown_queue)
			self.dropdown_queue.set(LOADER_FILE.settings.queue)
			self.queue_lbl = tk.Label(self.mainframe, text = "Audio Queue Setting")
			CreateToolTip(self.queue_lbl, "Queue: audio will play one after another in the order pressed, Stack: Audio files will play as soon as they are pressed, overtop of other files as necessary, Replace: Audio files will be played immediately removing other files as necessary")
			self.queue_menu = tk.OptionMenu(self.mainframe, self.dropdown_queue, *choices)
			self.queue_lbl.grid(row = 5, column = 1)
			self.queue_menu.grid(row = 5, column = 2, columnspan = 2)

			self.equalize_toggle_var = tk.IntVar(self.mainframe)
			self.equalize_toggle_var.set(int(LOADER_FILE.settings.equalize_audio))
			self.equalize_toggle = tk.Checkbutton(self.mainframe, text = "Equalize Audio", variable = self.equalize_toggle_var)
			CreateToolTip(self.equalize_toggle, "If checked audio volume will be equalized to target volume")
			self.equalize_toggle.grid(row = 6, column = 1, columnspan = 3)

			self.equalize_slider_lbl = tk.Label(self.mainframe, text = "Equalize Target")
			self.equalize_var = tk.IntVar(self.mainframe)
			self.equalize_var.set(LOADER_FILE.settings.equalize_target)
			self.equalize_slider = tk.Scale(self.mainframe, from_ = -100, to = 50, orient = tk.HORIZONTAL, variable = self.equalize_var, showvalue = False)
			self.equalize_slider.set(LOADER_FILE.settings.equalize_target)

			self.equalize_slider_lbl.grid(row = 7, column = 1)
			self.equalize_slider.grid(row = 7, column = 2, columnspan = 2)

			self.play_local_toggle_var = tk.IntVar(self.mainframe)
			self.play_local_toggle_var.set(int(LOADER_FILE.settings.play_local))
			self.play_local_toggle = tk.Checkbutton(self.mainframe, text = "Play Audio Locally", variable = self.play_local_toggle_var)
			CreateToolTip(self.play_local_toggle, "If checked audio will be played on local device as well as Output device")
			self.play_local_toggle.grid(row = 8, column = 1, columnspan = 3)

			self.volume_slider_lbl = tk.Label(self.mainframe, text = "Volume")
			self.volume_var = tk.DoubleVar(self.mainframe)
			self.volume_var.set(LOADER_FILE.settings.out_volume)
			self.volume_slider = tk.Scale(self.mainframe, from_ = -10.0, to = 10.0, orient = tk.HORIZONTAL, variable = self.volume_var, showvalue = False)
			self.vol_Text = tk.Entry(self.mainframe, textvariable = self.volume_var, width = 5)
			CreateToolTip(self.volume_slider_lbl, "Volume adjustment for files being played into Output device")

			self.local_volume_slider_lbl = tk.Label(self.mainframe, text = "Local Volume")
			self.local_volume_var = tk.DoubleVar(self.mainframe)
			self.local_volume_var.set(LOADER_FILE.settings.local_volume)
			self.local_volume_slider = tk.Scale(self.mainframe, from_ = -10.0, to = 10.0, orient = tk.HORIZONTAL, variable = self.local_volume_var, showvalue = False)
			self.localVol_Text = tk.Entry(self.mainframe, textvariable = self.local_volume_var, width = 5)
			CreateToolTip(self.local_volume_slider_lbl, "Volume adjustment for files being played into Local device")

			self.volume_slider_lbl.grid(row = 9, column = 1)
			self.vol_Text.grid(row = 9, column = 2)
			self.volume_slider.grid(row = 9, column = 3)
			
			self.local_volume_slider_lbl.grid(row = 10, column = 1)
			self.localVol_Text.grid(row = 10, column = 2)
			self.local_volume_slider.grid(row = 10, column = 3)

			self.quit_btn = tk.Button(self.mainframe, width = 15, text = "Close", command = self.end)
			self.quit_btn.grid(row = 11, column = 2, columnspan = 3)

			LOADER_FILE.settings.toggle_HM(False)
			self.run()

	def refocus(self, event):
		if (self.created_time + 500) < pygame.time.get_ticks():
			self.root.bell()
		self.root.focus_force()
        #

	def change_dropdown_output(self, *args):
		LOADER_FILE.settings.output_device = self.dropdown_output_var.get()

	def change_dropdown_local(self, *args):
		LOADER_FILE.settings.local_audio_device = self.dropdown_local_var.get()

	def change_dropdown_queue(self, *args):
		LOADER_FILE.settings.queue = self.dropdown_queue.get()
		stop_all_audio()

	def toggle_queue(self):
		toggle_queue_audio()
		if LOADER_FILE.settings.queue == True:
			self.queue_toggle.config(text = "Queue Audio")
		else:
			self.queue_toggle.config(text = "Stack Audio")

	def run(self):
		#self.mainframe.tkraise()
		#self.root.mainloop()
		ONGOING_FUNCTIONS.append(self)
		
	def draw(self):
		self.root.update()

		global KEY_LISTENER
		if KEY_LISTENER:
			self.bind_st_lbl.config(text = str(self.bind_st))
			self.bind_en_lbl.config(text = str(self.bind_en))

	def end(self):
		#save and close menu
		
		try:
			LOADER_FILE.settings.delay = int(self.delayvar.get())
		except ValueError:
			message_box("Delay must be an integer")

		try:
			LOADER_FILE.settings.audio_chunk_size = int(self.chunkvar.get())
		except ValueError:
			message_box("Chunk size must be an integer")

		LOADER_FILE.settings.output_device = self.dropdown_output_var.get()
		LOADER_FILE.settings.queue = self.dropdown_queue.get()

		LOADER_FILE.settings.equalize_audio = self.equalize_toggle_var.get()
		LOADER_FILE.settings.equalize_target = self.equalize_var.get()

		LOADER_FILE.settings.play_local = bool(self.play_local_toggle_var.get())
		LOADER_FILE.settings.out_volume = self.volume_var.get()
		LOADER_FILE.settings.local_volume = self.local_volume_var.get()

		LOADER_FILE.settings.toggle_HM()
		ONGOING_FUNCTIONS.remove(self)

		self.root.destroy()

class keybinds_menu():
	""" 
	menu for creating a new keybind or changing an existing one, uses tkinter library for interface
	"""

	def __init__(self, existing_bind = None):

		found = False
		for obj in ONGOING_FUNCTIONS:
			if obj.__class__.__name__ == self.__class__.__name__:
				found = True

		if found == False:

			self.existing_bind = existing_bind
			self.open_menu = None

			self.root = tk.Tk(sync = False)
			self.root.iconbitmap(const.ICO)
			self.root.title("Keybinds")
			self.root.protocol("WM_DELETE_WINDOW", self.end)
			#self.root.wm_attributes("-topmost", 1)
			#self.root.bind("<FocusOut>", self.refocus)
			self.created_time = pygame.time.get_ticks()



			self.mainframe = tk.Frame(self.root)
			self.mainframe.grid(column=0,row=0, sticky=(tk.N,tk.W,tk.E,tk.S) )
			self.mainframe.columnconfigure(0, weight = 1)
			self.mainframe.rowconfigure(0, weight = 1)
			self.mainframe.pack(pady = 15, padx = 25)

			self.name_lbl = tk.Label(self.mainframe, text = "Keybind Name")

			self.namevar = tk.StringVar(self.mainframe)
			if self.existing_bind:
				self.namevar.set(self.existing_bind.name)
			else:
				self.namevar.set("Untitled")
			self.name_text = tk.Entry(self.mainframe, textvariable = self.namevar)
			self.name_text.bind("<FocusIn>", self.end_binding)

			self.name_lbl.grid(row = 1, column = 1)
			self.name_text.grid(row = 1, column = 2, columnspan = 2)

			self.desc_lbl = tk.Label(self.mainframe, text = "Key Press Description")
			CreateToolTip(self.desc_lbl, "Optional description, if left blank the keybind will be displayed")
			self.descvar = tk.StringVar(self.mainframe)
			if self.existing_bind:
				self.descvar.set(self.existing_bind.keybind_desc)
			else:
				self.descvar.set("")
			self.desc_text = tk.Entry(self.mainframe, textvariable = self.descvar)
			self.desc_text.bind("<FocusIn>", self.end_binding)

			self.desc_lbl.grid(row = 2, column = 1)
			self.desc_text.grid(row = 2, column = 2, columnspan = 2)

			self.bind_btn = tk.Button(self.mainframe, width = 10, text = "Key Binding", command = self.start_binding)
			if self.existing_bind:
				self.bind = self.existing_bind.keybind
				self.bind_txt = self.existing_bind.keybind_readable
			else:
				self.bind = []
				self.bind_txt = ""
			

			self.bind_lbl = tk.Label(self.mainframe, text = str(self.bind_txt))

			self.bind_btn.grid(row = 3, column = 1)
			self.bind_lbl.grid(row = 3, column = 2, columnspan = 2)

			self.cycle_btn = tk.Button(self.mainframe, width = 10, text = "Cycle: On", command = self.toggle_cycle)
			self.cycle_btn.bind("<FocusIn>", self.end_binding)
			CreateToolTip(self.cycle_btn, "If turned on the audio files will cycle through, repeating only after the entire list has been played")
			self.timer_lbl = tk.Label(self.mainframe, text = "Cycle Reset Timer", wraplength = 200)
			self.timervar = tk.StringVar(self.mainframe)
			if self.existing_bind:
				self.timervar.set(str(self.existing_bind.cycle_reset_timer / 1000))
			else:
				self.timervar.set("0")
			self.timer_text = tk.Entry(self.mainframe, textvariable = self.timervar)
			self.timer_text.bind("<FocusIn>", self.end_binding)
			CreateToolTip(self.timer_lbl, "the amount of time (in seconds) before the cycle position is reset to 0")

			self.cycle_btn.grid(row = 5, column = 1)
			self.timer_lbl.grid(row = 6, column = 1)
			self.timer_text.grid(row = 6, column = 2, columnspan = 2)

			if self.existing_bind and self.existing_bind.call_function:
				self.files_lbl = tk.Label(self.mainframe, text = "Calls Function: " + str(self.existing_bind.call_function.__name__.replace("_", " ")), wraplength = 200)
				self.files_lbl.grid(row = 7, column = 1)
				self.files = None
			else:
				self.add_file_btn = tk.Button(self.mainframe, width = 10, text = "Add File", command = self.get_file)
				self.add_file_btn.bind("<FocusIn>", self.end_binding)
				if self.existing_bind:
					self.files = list(self.existing_bind.audio_paths)
				else:
					self.files = []
				self.remove_file_btn = tk.Button(self.mainframe, width = 10, text = "Remove File", command = self.remove_file)
				self.add_file_btn.bind("<FocusIn>", self.end_binding)
				self.files_lbl = tk.Label(self.mainframe, text = str(self.files), wraplength = 200)

				self.add_file_btn.grid(row = 7, column = 1)
				
				self.files_lbl.grid(row = 7, column = 2, rowspan = 2, columnspan = 2)
				if self.remove_file_btn:
					self.remove_file_btn.grid(row = 8, column = 1)

			self.cancel_btn = tk.Button(self.mainframe, width = 10, text = "Cancel", command = self.end)
			self.submit_btn = tk.Button(self.mainframe, width = 10, text = "Submit", command = self.save)


			self.vol_adjust_slider_lbl = tk.Label(self.mainframe, text = "Volume Adjust")
			self.vol_adjust_var = tk.IntVar(self.mainframe)
			if self.existing_bind:
				self.vol_adjust_var.set(self.existing_bind.volume_adjust)
			else:
				self.vol_adjust_var.set(0)
			self.vol_adjust_slider = tk.Scale(self.mainframe, from_ = -25, to = 25, orient = tk.HORIZONTAL, variable = self.vol_adjust_var, showvalue = False)

			self.vol_adjust_slider_lbl.grid(row = 9, column = 1)
			self.vol_adjust_slider.grid(row = 9, column = 2)


			self.cancel_btn.grid(row = 10, column = 1, pady = 10)
			self.submit_btn.grid(row = 10, column = 2, pady = 10)

			if self.existing_bind:
				self.remove_btn = tk.Button(self.mainframe, width = 10, text = "Delete", command = self.remove)
				self.remove_btn.grid(row = 10, column = 3, pady = 10)


			LOADER_FILE.settings.toggle_HM(False)

			ONGOING_FUNCTIONS.append(self)

	def refocus(self, event):
		if self.open_menu == None:
			if (self.created_time + 500) < pygame.time.get_ticks():
				self.root.bell()
			self.mainframe.focus_force()
        #

	def start_binding(self):
		global KEY_LISTENER
		self.bind = []
		self.bind_txt = ""
		self.bind_btn.config(text = "End Binding", command = self.end_binding)
		KEY_LISTENER = self.add_bind
		self.bind_btn.focus()

		LOADER_FILE.settings.toggle_HM(True)

	def end_binding(self, event = None):
		global KEY_LISTENER
		KEY_LISTENER = None
		self.bind_btn.config(text = "Start Binding", command = self.start_binding)
		
		LOADER_FILE.settings.toggle_HM(False)

	def add_bind(self, Key):
		found = False
		for KID in self.bind:
			if KID == Key.KeyID:
				found = True

		if found == False:
			self.bind.append(int(Key.KeyID))
			if Key.Key.find("Oem") == -1:
				self.bind_txt += " " + Key.Key
			else:
				self.bind_txt += " " + chr(Key.Ascii)

	def toggle_cycle(self):
		if self.cycle_btn.cget("text") == "Cycle: On":
			self.cycle_btn.config(text = "Cycle: Off")

		else:
			self.cycle_btn.config(text = "Cycle: On")

	def get_file(self):
		if self.open_menu == None:

			fs = file_selector()
			self.open_menu = fs
			result = fs.run()
			if result != "":
				self.files.append(result)
				self.files_lbl.config(text = str(self.files))
			self.open_menu = None


	def draw(self):
		self.root.update()

		global KEY_LISTENER
		if KEY_LISTENER:
			self.bind_lbl.config(text = str(self.bind_txt))

	def save(self):

		if self.existing_bind:

			self.existing_bind.name = self.namevar.get()
			self.existing_bind.keybind_desc = self.descvar.get()
			self.existing_bind.keybind = self.bind
			self.existing_bind.volume_adjust = self.vol_adjust_var.get()
			if self.files:
				self.existing_bind.audio_paths = self.files
			self.existing_bind.keybind_readable = self.bind_txt

			if self.cycle_btn.cget("text") == "Cycle: On":
				self.existing_bind.cycle = True
			else:
				self.existing_bind.cycle = False


			try:
				self.existing_bind.cycle_reset_timer = int(int(self.timervar.get()) * 1000)
			except ValueError:
				message_box("Delay must be an integer")

			for key in self.existing_bind.keybind:
				BOUND_KEYS.append(key)

		else:
			kb = key_bind()
			kb.name = self.namevar.get()
			kb.keybind_desc = self.descvar.get()
			kb.keybind = self.bind
			kb.audio_paths = self.files
			kb.keybind_readable = self.bind_txt
			kb.volume_adjust = self.vol_adjust_var.get()

			try:
				kb.cycle_reset_timer = int(int(self.timervar.get()) * 1000)
			except ValueError:
				message_box( "Delay must be an integer")

			if self.cycle_btn.cget("text") == "Cycle: On":
				kb.cycle = True
			else:
				kb.cycle = False

			LOADER_FILE.settings.key_binds.append(kb)

			for key in kb.keybind:
				BOUND_KEYS.append(key)

		self.end()

	def remove_file(self):
		remove_file(self.files, self)

	def update_files(self, files):
		self.files = files
		self.files_lbl.config(text = str(self.files))

	def remove(self): #delete keybind
		if self.existing_bind:
			LOADER_FILE.settings.key_binds.remove(self.existing_bind)

		self.end()

	def end(self):
		global ONGOING_FUNCTIONS, BOUND_KEYS, LOADER_FILE
		ONGOING_FUNCTIONS.remove(self)
		self.end_binding()
		self.root.destroy()
		LOADER_FILE.settings.toggle_HM()

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_attributes("-topmost", 1)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class remove_file():

	def __init__(self, files, binds_menu):

		"""
	opens menu to delete file paths from an array of file paths, uses tkinter for interface
		"""

		found = False
		for obj in ONGOING_FUNCTIONS:
			if obj.__class__.__name__ == self.__class__.__name__:
				found = True

		if found == False:

			self.files = files
			self.binds_menu = binds_menu

			if len(files) >= 1:

				self.root = tk.Tk(sync = False)
				self.root.iconbitmap(const.ICO)
				self.root.title("Remove")
				self.root.protocol("WM_DELETE_WINDOW", self.end)
				self.root.wm_attributes("-topmost", 1)
				#self.root.bind("<FocusOut>", self.refocus)
				self.created_time = pygame.time.get_ticks()


				self.mainframe = tk.Frame(self.root)
				self.mainframe.grid(column=0,row=0, sticky=(tk.N,tk.W,tk.E,tk.S) )
				self.mainframe.columnconfigure(0, weight = 1)
				self.mainframe.rowconfigure(0, weight = 1)
				self.mainframe.pack(pady = 15, padx = 25)

				self.lbls = []
				self.btns =[]
				for i, file in enumerate(self.files):
					self.btns.append(tk.Button(self.mainframe, width = 1, text = "X", command = lambda : self.remove_file(i)))
					self.lbls.append(tk.Label(self.mainframe, text = file, wraplength = 200))

					self.btns[i].grid(row = i, column = 1, pady = 10)
					self.lbls[i].grid(row = i, column = 2, pady = 10)

				ONGOING_FUNCTIONS.append(self)

	def refocus(self, event):
		if self.open_menu == None:
			if (self.created_time + 500) < pygame.time.get_ticks():
				self.root.bell()
			self.root.focus_force()
        #

	def remove_file(self, index):
		self.lbls[index].grid_forget()
		self.btns[index].grid_forget()

		self.files[index] = None
		self.files.remove(None)

		self.binds_menu.update_files(self.files)


	def draw(self):
		self.root.update()

	def end(self):
		self.root.destroy()
		ONGOING_FUNCTIONS.remove(self)

class message_box:

	def __init__(self, text):
		self.text = text

		self.root = tk.Tk(sync = False)
		self.root.iconbitmap(const.ICO)
		self.root.title("Warning")
		self.root.protocol("WM_DELETE_WINDOW", self.end)
		#self.root.wm_attributes("-topmost", 1)
		self.root.bind("<FocusOut>", self.refocus)
		self.created_time = pygame.time.get_ticks()

		self.mainframe = tk.Frame(self.root)
		self.mainframe.grid(column=0,row=0, sticky=(tk.N,tk.W,tk.E,tk.S) )
		self.mainframe.columnconfigure(0, weight = 1)
		self.mainframe.rowconfigure(0, weight = 1)
		self.mainframe.pack(pady = 15, padx = 5)

		self.message_lbl = tk.Label(self.mainframe, text = self.text, wraplength = 200)
		self.message_lbl.grid(row = 1, column = 1)

		self.ok_btn = tk.Button(self.mainframe, width = 10, text = "Okay", command = self.end)
		self.ok_btn.grid(row = 2, column = 1)

		ONGOING_FUNCTIONS.append(self)

	def draw(self):
		self.root.update()

	def refocus(self, event):
		if self.open_menu == None:
			if (self.created_time + 500) < pygame.time.get_ticks():
				self.root.bell()
			self.root.focus_force()

	def end(self):
		ONGOING_FUNCTIONS.remove(self)
		self.root.destroy()



class play_audio():
	"""
	creates a class that will be called every frame, each frame it will add the next chunk(as defined in user_settings) to the queue
	"""

	def __init__(self, file_name, volume_adjust = 0, local = False):

		self.stream = None #played on output device
		self.stream_local = None #played on local device if one is selected
		self.volume_adjust = volume_adjust

		if LOADER_FILE.settings.output_device:
			self.file_name = file_name
			self.stream = None
			print( "starting", self.file_name)
			self.f = None

			try:
				self.f = pydub.AudioSegment.from_file(str(file_name), file_name.split('.')[-1])
			except WindowsError:
				message_box("Invalid File Path was used:" + str(file_name))


			if self.f:

				if LOADER_FILE.settings.equalize_audio:
					self.f = equalize_audio(self.f)

					self.f = self.f.apply_gain(LOADER_FILE.settings.out_volume + self.volume_adjust)

				if LOADER_FILE.settings.play_local == True and LOADER_FILE.settings.local_audio_device:
					for i in range(PA.get_device_count()):
							if PA.get_device_info_by_index(i)["name"] == LOADER_FILE.settings.output_device:
								try:
									self.stream = PA.open(format = PA.get_format_from_width(self.f.sample_width),
									channels = self.f.channels,
									rate = self.f.frame_rate,
									output = True, output_device_index = i)
								except IOError:
									message_box("Invalid Output Device")


							if PA.get_device_info_by_index(i)["name"] == LOADER_FILE.settings.local_audio_device:
								try:

									self.stream_local = PA.open(format = PA.get_format_from_width(self.f.sample_width),
									channels = self.f.channels,
									rate = self.f.frame_rate,
									output = True, output_device_index = i)
								except IOError:
									message_box("Invalid Local Output Device")


				elif local == False or LOADER_FILE.settings.local_audio_device == None:
					for i in range(PA.get_device_count()):
							if PA.get_device_info_by_index(i)["name"] == LOADER_FILE.settings.output_device:
								try:
									self.stream = PA.open(format = PA.get_format_from_width(self.f.sample_width),
									channels = self.f.channels,
									rate = self.f.frame_rate,
									output = True, output_device_index = i)
								except IOError:
									message_box("Invalid Output Device")


								break

				else: # local == True:
					for i in range(PA.get_device_count()):
							if PA.get_device_info_by_index(i)["name"] == LOADER_FILE.settings.local_audio_device:
								try:
									self.stream_local = PA.open(format = PA.get_format_from_width(self.f.sample_width),
									channels = self.f.channels,
									rate = self.f.frame_rate,
									output = True, output_device_index = i)
								except IOError:
									message_box("Invalid Local Output Device")

								break


				if (self.stream or self.stream_local) and LOADER_FILE.settings.mute == False:
					self.chunks = make_chunks(self.f, LOADER_FILE.settings.audio_chunk_size)
					ONGOING_AUDIO.append(self)

		else:
			message_box("No Output Device Selected")

	def draw(self):
		"""
		the function called every frame
		"""
		if len(self.chunks) > 0:
			data = self.chunks.pop(0)

			if data != "":
				if self.stream:
					data = data.apply_gain(LOADER_FILE.settings.out_volume + self.volume_adjust)
					#data = data.speedup(4)
					self.stream.write((data + LOADER_FILE.settings.out_volume)._data)

				if self.stream_local:
					data = data.apply_gain(LOADER_FILE.settings.local_volume + self.volume_adjust)
					self.stream_local.write((data + LOADER_FILE.settings.local_volume)._data)
		else: 
			self.end()
			

	def end(self):
		if self.stream:
			self.stream.stop_stream()
			self.stream.close()
		if self.stream_local:
			self.stream_local.stop_stream()
			self.stream_local.close()
		ONGOING_AUDIO.remove(self)

def stop_all_audio():
	global ONGOING_AUDIO

	ONGOING_AUDIO = []

def stop_oldest_audio():
	global ONGOING_AUDIO
	if len(ONGOING_AUDIO) >= 1:
		ONGOING_AUDIO[0].end()

def equalize_audio(sound):
	delta_dBFS = LOADER_FILE.settings.equalize_target - sound.dBFS
	return sound.apply_gain(delta_dBFS)

def toggle_enabled(btn_object):
	#stops audio, and disables key hooking

	if KEY_LISTENER == None:
		LOADER_FILE.settings.hook_keys = not LOADER_FILE.settings.hook_keys
		LOADER_FILE.settings.toggle_HM()

		if LOADER_FILE.settings.hook_keys == False:
			btn_object.color_box = const.COLOR_RED
			btn_object.color_mouseover = const.COLOR_LIGHT_RED
			btn_object.text = "Disabled"
			stop_all_audio()
		else:
			btn_object.color_box = const.COLOR_DARK_GREEN
			btn_object.color_mouseover = const.COLOR_GREEN
			btn_object.text = "Enabled"

def toggle_muted():
	# stops audio and prevents more from being played
	global muted_btn
	btn_object = muted_btn

	LOADER_FILE.settings.mute = not LOADER_FILE.settings.mute

	if LOADER_FILE.settings.mute == False:

		btn_object.color_box = const.COLOR_RED
		btn_object.color_mouseover = const.COLOR_LIGHT_RED
		btn_object.text = "Mute"
	else:
		btn_object.color_box = const.COLOR_DARK_GREY
		btn_object.color_mouseover = const.COLOR_GREY
		btn_object.text = "Unmute"
		stop_all_audio()

def change_kb_list_start(func, amount):
	#for scrolling through the list of keybinds
	if func.__class__.__name__ == "draw_keybind_list" and len(LOADER_FILE.settings.key_binds) > const.LINES_TO_DRAW:
		func.draw_start = max(min(func.draw_start + amount, len(LOADER_FILE.settings.key_binds) - const.LINES_TO_DRAW), 0)


class draw_keybind_list():
	"""
	updated every frame, displays the list of keybinds
	"""

	menu_width = const.MENU_WIDTH
	menu_height = const.MENU_HEIGHT#constants.GAME_TILES_Y * constants.GAME_TILE_SIZE
	menu_font = "FONT_DEFAULT"

	coord_x = (const.WINDOW_WIDTH - menu_width) / 2
	coord_y = 155

	x_buffer = 0
	y_buffer = -20

	draw_start = 0

	def __init__(self): 


		self.surface = pygame.Surface((self.menu_width, self.menu_height))

	
	def draw(self):
		global MOUSE_CLICKED, RMOUSE_CLICKED

		self.surface.fill(const.COLOR_GREY)


		print_list = []
		for kb in LOADER_FILE.settings.key_binds:
			print_list.append(kb.name + " | " + kb.desc)

		mouse_line_selection = 0

		val = util.mouse_in_window(self.coord_x + self.x_buffer, self.coord_y + self.y_buffer, self.menu_width + self.x_buffer, self.menu_height - self.y_buffer)
		if val:
			rel_x, rel_y = val
			mouse_line_selection = rel_y / util.helper_text_height(self.menu_font) + self.draw_start

			global WHEEL_UP, WHEEL_DOWN
			if WHEEL_UP:
				change_kb_list_start(self, -1)
				WHEEL_UP = False

			elif WHEEL_DOWN:
				change_kb_list_start(self, 1)
				WHEEL_DOWN = False


		for line in range(self.draw_start, self.draw_start + const.LINES_TO_DRAW):

			if line == self.draw_start and self.draw_start >= 1:
				util.draw_text(self.surface, "...", (self.x_buffer, self.y_buffer + (line-self.draw_start+1)*util.helper_text_height(self.menu_font)), const.COLOR_WHITE)
			
			elif line == self.draw_start+const.LINES_TO_DRAW-1 and self.draw_start+const.LINES_TO_DRAW < len(LOADER_FILE.settings.key_binds):
				util.draw_text(self.surface, "...", (self.x_buffer, self.y_buffer + (line-self.draw_start+1)*util.helper_text_height(self.menu_font)), const.COLOR_WHITE)

			elif line < len(print_list):
				name = print_list[line]
				if (line == mouse_line_selection - 1) and (mouse_line_selection > 0):
					util.draw_text(self.surface, name, (self.x_buffer, self.y_buffer + (line-self.draw_start+1)*util.helper_text_height(self.menu_font)), const.COLOR_WHITE, back_color = const.COLOR_LIGHT_GREY_2)

					if RMOUSE_CLICKED == True:
						keybinds_menu(LOADER_FILE.settings.key_binds[line])
						MOUSE_CLICKED = False
					elif MOUSE_CLICKED == True:
						key_event(LOADER_FILE.settings.key_binds[line].keybind, line)
						RMOUSE_CLICKED = False

				else:
					util.draw_text(self.surface, name, (self.x_buffer, self.y_buffer + (line-self.draw_start+1)*util.helper_text_height(self.menu_font)), const.COLOR_WHITE)


		util.draw_text(self.surface, self.tooltip(), (self.menu_width/2, self.y_buffer + (const.MAX_LINES_DRAWABLE+1)*util.helper_text_height(self.menu_font)), const.COLOR_WHITE, center = True)

		SURFACE_MAIN.blit(self.surface, (self.coord_x, self.coord_y))

	def end(self):
		#prevents an error when ongoing functions are told to end
		pass

	def tooltip(self):
		#returns the text displaying profile and active audio file name
		val = "Profile:" + str(LOADER_FILE.current_profile + 1)
		if len(ONGOING_AUDIO) > 0:
			if LOADER_FILE.settings.queue != "Stack" or len(ONGOING_AUDIO) == 1:
				val += ', Playing "'
				val += ONGOING_AUDIO[0].file_name.split("/")[-1].split(".")[0]
				val += '"'
			else:
				val += ', Playing ' + str(len(ONGOING_AUDIO)) + "Audio Files"
		return str(val)
	

def main_loop():
	global MOUSE_CLICKED, RMOUSE_CLICKED, muted_btn, ONGOING_AUDIO
	init()

	kb_list = draw_keybind_list()



	btn_size = (120, 30)

	settings_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (7 + btn_size[0]/2), 85), btn_size, "Settings", click_function = settings_menu, pos_from_center = True)

	new_bind_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 - (7 + btn_size[0]/2), 85), btn_size, "New Bind", click_function = keybinds_menu, pos_from_center = True)

	enabled_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (7 + btn_size[0]/2), 125), btn_size, "Enabled",
	 click_function = toggle_enabled, pos_from_center = True, color_box = const.COLOR_DARK_GREEN, color_mouseover = const.COLOR_GREEN)
	enabled_btn.click_function_params = [enabled_btn]

	muted_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 - (7 + btn_size[0]/2), 125), btn_size, "Mute",
	 click_function = toggle_muted, pos_from_center = True, color_box = const.COLOR_RED, color_mouseover = const.COLOR_LIGHT_RED)



	btn_size = (10, 25)

	list_up_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (175 + btn_size[0]/2), 185), btn_size, "^" ,
	 click_function = change_kb_list_start, click_function_params = [kb_list, -3], pos_from_center = True, color_box = const.COLOR_RED, color_mouseover = const.COLOR_LIGHT_RED)

	list_down_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (175 + btn_size[0]/2), 490), btn_size, "^",
	 click_function = change_kb_list_start, click_function_params = [kb_list, 3], pos_from_center = True, color_box = const.COLOR_RED, color_mouseover = const.COLOR_LIGHT_RED, flip = True)



	btn_size = (20,20)

	profile_1_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (-140 + btn_size[0]/2), 535), btn_size, "1",
	 click_function = lambda : LOADER_FILE.set_profile(0), pos_from_center = True, color_box = const.COLOR_GREY)

	profile_2_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (-115 + btn_size[0]/2), 535), btn_size, "2",
	 click_function = lambda : LOADER_FILE.set_profile(1), pos_from_center = True, color_box = const.COLOR_GREY)

	profile_3_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (-90 + btn_size[0]/2), 535), btn_size, "3",
	 click_function = lambda : LOADER_FILE.set_profile(2), pos_from_center = True, color_box = const.COLOR_GREY)

	profile_4_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (-65 + btn_size[0]/2), 535), btn_size, "4",
	 click_function = lambda : LOADER_FILE.set_profile(3), pos_from_center = True, color_box = const.COLOR_GREY)

	profile_5_btn = ui_button(SURFACE_MAIN, (const.WINDOW_WIDTH/2 + (-40 + btn_size[0]/2), 535), btn_size, "5",
	 click_function = lambda : LOADER_FILE.set_profile(4), pos_from_center = True, color_box = const.COLOR_GREY)


	if LOADER_FILE.settings.mute == True:
		toggle_muted()
		toggle_muted()


	frames = 0
	
	LOADER_FILE.settings.toggle_HM()

	SURFACE_MAIN.blit(const.BACK, (0,0))

	while True:
			
		settings_btn.draw()

		new_bind_btn.draw()

		enabled_btn.draw()

		muted_btn.draw()


		kb_list.draw()

		#play audio segments 
		try:
			if LOADER_FILE.settings.queue == "Stack":
				for func in ONGOING_AUDIO:
					func.draw()

			elif LOADER_FILE.settings.queue == "Queue" and len(ONGOING_AUDIO) > 0:
				ONGOING_AUDIO[0].draw()

			elif len(ONGOING_AUDIO) > 0:
				if len(ONGOING_AUDIO) > 1:
					ONGOING_AUDIO = [ONGOING_AUDIO[-1]]
				ONGOING_AUDIO[0].draw()
		except TypeError:
			pass

		#update other open windows (settings, keybinds menu, etc)
		try:
			for func in ONGOING_FUNCTIONS:
				func.draw()
		except TypeError:
			pass

		list_up_btn.draw()
		list_down_btn.draw()

		profile_1_btn.draw()
		profile_2_btn.draw()
		profile_3_btn.draw()
		profile_4_btn.draw()
		profile_5_btn.draw()
		
		util.draw_text(SURFACE_MAIN, "FPS: " + str(int(CLOCK.get_fps())), (25, 540), center = True, back_color = const.COLOR_GREY_68)
		frames += 1
		if LOADER_FILE.settings.target_fps:
			CLOCK.tick(LOADER_FILE.settings.target_fps)
		else:
			CLOCK.tick()


		if LOADER_FILE.settings.hook_keys == True:
			pythoncom.PumpWaitingMessages()

		MOUSE_CLICKED = False
		RMOUSE_CLICKED = False
		WHEEL_UP = False
		WHEEL_DOWN = False
		event = handle_input()

		if event == "QUIT":
			break


		pygame.display.flip()

		if LOADER_FILE.settings.delay and LOADER_FILE.settings.delay > 0:
			pygame.time.wait(LOADER_FILE.settings.delay)


	quit()


def init():
	"""
	sets initial values, defines global variables, and loads saved settings
	"""
	global SURFACE_MAIN, HMK, CLOCK, ONGOING_FUNCTIONS, MOUSE_CLICKED, PA, KEYS_PRESSED, BOUND_KEYS, KEY_LISTENER, RMOUSE_CLICKED, ONGOING_AUDIO
	global WHEEL_DOWN, WHEEL_UP, LOADER_FILE

	pygame.init()
	pygame.display.set_caption(const.PROGRAM_TITLE)
	pygame.display.set_icon(const.ICON_PNG)

	pygame.event.set_blocked(None)
	pygame.event.set_allowed(pygame.QUIT)
	pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
	pygame.event.set_allowed(pygame.MOUSEBUTTONUP)

	SURFACE_MAIN = pygame.display.set_mode( (const.WINDOW_WIDTH, const.WINDOW_HEIGHT) )

	CLOCK = pygame.time.Clock()

	HMK = pyHook.HookManager()
	HMK.KeyDown = KeyDown
	HMK.KeyUp = KeyUp
	HMK.HookKeyboard()

	PA = pyaudio.PyAudio()

	ONGOING_FUNCTIONS = []
	ONGOING_AUDIO = []

	tk.NoDefaultRoot()

	MOUSE_CLICKED = False
	RMOUSE_CLICKED = False
	WHEEL_UP = False
	WHEEL_DOWN = False

	KEYS_PRESSED = []

	KEY_LISTENER = None #function that will recive all key events

	LOADER_FILE = loader_file()
	load()



	for setting in LOADER_FILE.profiles:
		if setting == user_settings:
			settings = user_settings()
		for kb in setting.key_binds:
			if hasattr(kb, "volume_adjust") == False:
				kb.volume_adjust = 0

	BOUND_KEYS = []
	for kb in LOADER_FILE.settings.key_binds:
		for key in kb.keybind:
			BOUND_KEYS.append(key)

	# HMM = pyHook.HookManager()
	# HMM.MouseAllButtons = OnMouseEvent
	# HMM.HookMouse()

def quit():
	global ONGOING_FUNCTIONS
	save()
	
	for func in ONGOING_FUNCTIONS:
		func.end()

	for func in ONGOING_AUDIO:
		func.end()

	pygame.quit()
	exit(0)

def save():
	global LOADER_FILE
	with gzip.open('Save.cfg', 'wb') as file:
		pickle.dump(LOADER_FILE, file)

def load():
	global LOADER_FILE
	try:
		with gzip.open('Save.cfg', 'rb') as file:
			LOADER_FILE = pickle.load(file)
	except IOError:
		#save file not found
		message_box(const.First_time_message)
		pass


def KeyDown(event):
	# if keys are hooked this will be called whenever a KeyDown event takes place, regardless of what window is focused


	global KEYS_PRESSED
	# print 'MessageName:',event.MessageName
	# print 'Message:',event.Message
	# print 'Time:',event.Time
	# print 'Window:',event.Window
	# print 'WindowName:',event.WindowName
	# print 'Ascii:', event.Ascii, chr(event.Ascii)
	# print 'Key Down:', event.Key
	# print 'KeyID:', event.KeyID
	# print 'ScanCode:', event.ScanCode
	# print 'Extended:', event.Extended
	# print 'Injected:', event.Injected
	# print 'Alt', event.Alt
	# print 'Transition', event.Transition
	# print '---'	

	if KEY_LISTENER:
		KEY_LISTENER(event)

	else:
		found = False
		for key in BOUND_KEYS:
			if event.KeyID == key:
				found = True
				break

		if found == True: #key is bound to something

			found = False
			for key in KEYS_PRESSED:
				if key == event.KeyID:
					found = True
					break 

			if found == False: #key is not in pressed key list
				KEYS_PRESSED.append(event.KeyID)

def KeyUp(event):
	# if keys are hooked this will be called whenever a KeyUp event takes place, regardless of what window is focused
	global KEYS_PRESSED
	for key in BOUND_KEYS:
		if event.KeyID == key:
			if not key_event(KEYS_PRESSED):
				try:
					KEYS_PRESSED.remove(event.KeyID)
				except ValueError:
					#key is not in list, ignore it
					pass

			else:
				KEYS_PRESSED = []

			break
	pass

def handle_input():
	"""
	hnadles mouse clicks and quit event
	"""
	global MOUSE_CLICKED, RMOUSE_CLICKED, WHEEL_UP, WHEEL_DOWN
	try:
		events_list = pygame.event.get()

		for event in events_list:

			if event.type == pygame.QUIT:
				return "QUIT"
				#quit()

			if event.type == pygame.MOUSEBUTTONUP:
				if event.button == 1:
					if len(ONGOING_FUNCTIONS) == 0:
						MOUSE_CLICKED = True
					return ("CLICK")

				elif event.button == 3:
					RMOUSE_CLICKED = True

				elif event.button == 4:
					WHEEL_UP = True

				elif event.button == 5:
					WHEEL_DOWN = True



	except TypeError:
		pass

class ui_button:
	"""
	class used to make ui buttons, needs to be updated every frame by calling ui_button.draw() 
	"""

	def __init__(self, surface, coords, size, text, click_function = None, click_function_params = None,
	 text_color = const.COLOR_WHITE, color_box = const.COLOR_GREY,
	  color_mouseover = const.COLOR_LIGHT_GREY_2, pos_from_center = False, font = "FONT_MENU", sprite = None, flip = False):

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
		self.flip = flip

		

		self.rect = pygame.Rect(coords, size)

		if self.pos_from_center == True:
			self.rect.center = coords

			w, h = self.size
			x, y = self.rect.center
			x -= w/2
			y -= h/2

			self.coords = (x,y)


	@property
	def is_highlighted(self):

		x, y = self.coords
		w,h = self.size

		return (util.mouse_in_window(x, y, w, h) != None)

	def center(self, coords):

		x,y = coords

		x += const.WINDOW_WIDTH/2
		y += const.WINDOW_HEIGHT/2

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

			d_x -= const.GAME_TILE_SIZE/2
			d_y -= const.GAME_TILE_SIZE/2

			d_coords = (d_x, d_y)

			pygame.draw.rect(self.surface, color, self.rect)
			if self.flip:
				self.sprite = pygame.transform.flip(self.sprite)
			self.surface.blit(self.sprite, d_coords)
		else:

			pygame.draw.rect(self.surface, color, self.rect)
			util.draw_text(self.surface, self.text, self.rect.center, self.text_color, center = True, font = self.font, flip = self.flip)

		if self.is_highlighted == True:
			if MOUSE_CLICKED == True:

				MOUSE_CLICKED = False

				if self.click_function:
					
					if self.click_function == "RETURN":

						return "END"

					elif self.click_function_params:
						val = self.click_function(*self.click_function_params)


					else:
						val = self.click_function()

					if val:
						return val
					else:
						return "END"
				else:
					return "END"




		return None

if __name__ == '__main__':

	main_loop()