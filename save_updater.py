import gzip, pickle

class loader_file():

	def __init__(self):

		self.profiles = []
		self.current_profile = 0

		for n in range(5):
			self.profiles.append(user_settings())

	@property
	def settings(self):
		return self.profiles[self.current_profile]
	

	def next_profile(self):
		self.current_profile += 1
		if self.current_profile > 5:
			self.current_profile = 0

class user_settings():

	def __init__(self):
		self.key_binds = []
		self.delay = 5
		self.target_fps = None
		self.audio_chunk_size = 25
		self.double_tap_speed = 500
		self.hook_keys = True
		self.mute = False
		self.output_device = None
		self.local_audio_device = None
		self.equalize_audio = True
		self.equalize_target = -25
		self.out_volume = 0
		self.local_volume = 0
		self.play_local = False
		self.queue = "Queue"

		self.old_hook = None

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

class key_bind():

	name = "Untitled"
	keybind_desc = ""
	keybind_readable = ""
	keybind = []
	audio_paths = []
	cycle = False #if multiple file in audio paths and not cycle then a random file will be picked
	cycle_pos = 0
	cycle_reset_timer = 0 #in ms/ticks
	last_played = None

	volume_adjust = 0

	call_function = None
	double_call_func = None

	@property
	def desc(self):
		if self.keybind_desc:
			return self.keybind_desc
		else:
			return str(self.keybind_readable).replace("[", "").replace("]", "").replace("'", "")
	

	def get_track(self):
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
			play_audio(self.get_track())

 


global SETTINGS
try:
	with gzip.open('Save.cfg', 'rb') as file:
		SETTINGS = pickle.load(file)
except IOError:
	pass



with gzip.open('Save.cfg', 'wb') as file:
	pickle.dump(LOADER, file)

LOADER = loader_file()
LOADER.profiles[0] = SETTINGS
