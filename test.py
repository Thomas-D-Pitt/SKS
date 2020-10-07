class settings_menu():

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
            self.root.wm_attributes("-topmost", 1)
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
            self.delayvar.set(SETTINGS.delay)
            self.delay_Text = tk.Entry(self.mainframe, textvariable = self.delayvar)

            self.delay_lbl.grid(row = 1, column = 1)
            self.delay_Text.grid(row = 1, column = 2)

            #delay settings
            self.chunk_lbl = tk.Label(self.mainframe, text = "Chunk Size")
            CreateToolTip(self.chunk_lbl, "The amount of audio (in ms) processed each frame, if this is shorter than your time between frames audio tearing will occur, large numbers may cause the program to lag, (1/fps ~ chunk size/1000)")
            self.chunkvar = tk.StringVar(self.mainframe)
            self.chunkvar.set(SETTINGS.audio_chunk_size)
            self.chunk_Text = tk.Entry(self.mainframe, textvariable = self.chunkvar)

            self.chunk_lbl.grid(row = 2, column = 1)
            self.chunk_Text.grid(row = 2, column = 2)

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

                    if PA.get_device_info_by_index(i)["name"] == SETTINGS.output_device:
                        self.dropdown_output_var.set(PA.get_device_info_by_index(i)["name"])

                    if PA.get_device_info_by_index(i)["name"] == SETTINGS.local_audio_device:
                        self.dropdown_local_var.set(PA.get_device_info_by_index(i)["name"])

                except IOError:
                    #print "Invalid Output Device"
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
            self.output_menu.grid(row = 3, column = 2)

            self.local_lbl.grid(row = 4, column = 1)
            self.local_menu.grid(row = 4, column = 2)

            choices = ["Queue", "Stack", "Replace"]
            self.dropdown_queue = tk.StringVar(self.mainframe)
            self.dropdown_queue.trace('w', self.change_dropdown_queue)
            self.dropdown_queue.set(SETTINGS.queue)
            self.queue_lbl = tk.Label(self.mainframe, text = "Audio Queue Setting")
            CreateToolTip(self.queue_lbl, "Queue: audio will play one after another in the order pressed, Stack: Audio files will play as soon as they are pressed, overtop of other files as necessary, Replace: Audio files will be played immediately removing other files as necessary")
            self.queue_menu = tk.OptionMenu(self.mainframe, self.dropdown_queue, *choices)
            self.queue_lbl.grid(row = 5, column = 1)
            self.queue_menu.grid(row = 5, column = 2)

            self.equalize_toggle_var = tk.IntVar(self.mainframe)
            self.equalize_toggle_var.set(int(SETTINGS.equalize_audio))
            self.equalize_toggle = tk.Checkbutton(self.mainframe, text = "Equalize Audio", variable = self.equalize_toggle_var)
            CreateToolTip(self.equalize_toggle, "If checked audio volume will be equalized to target volume")
            self.equalize_toggle.grid(row = 6, column = 1, columnspan = 2)

            self.equalize_slider_lbl = tk.Label(self.mainframe, text = "Equalize Target")
            self.equalize_var = tk.IntVar(self.mainframe)
            self.equalize_var.set(SETTINGS.equalize_target)
            self.equalize_slider = tk.Scale(self.mainframe, from_ = -100, to = 50, orient = tk.HORIZONTAL, variable = self.equalize_var, showvalue = False)
            self.equalize_slider.set(SETTINGS.equalize_target)

            self.equalize_slider_lbl.grid(row = 7, column = 1)
            self.equalize_slider.grid(row = 7, column = 2)

            self.play_local_toggle_var = tk.IntVar(self.mainframe)
            self.play_local_toggle_var.set(int(SETTINGS.play_local))
            self.play_local_toggle = tk.Checkbutton(self.mainframe, text = "Play Audio Locally", variable = self.play_local_toggle_var)
            CreateToolTip(self.play_local_toggle, "If checked audio will be played on local device as well as Output device")
            self.play_local_toggle.grid(row = 8, column = 1, columnspan = 2)

            self.volume_slider_lbl = tk.Label(self.mainframe, text = "Volume")
            self.volume_var = tk.IntVar(self.mainframe)
            self.volume_var.set(SETTINGS.out_volume)
            self.volume_slider = tk.Scale(self.mainframe, from_ = -50, to = 50, orient = tk.HORIZONTAL, variable = self.volume_var, showvalue = False)
            CreateToolTip(self.volume_slider_lbl, "Volume adjustment for files being played into Output device")

            self.local_volume_slider_lbl = tk.Label(self.mainframe, text = "Local Volume")
            self.local_volume_var = tk.IntVar(self.mainframe)
            self.local_volume_var.set(SETTINGS.local_volume)
            self.local_volume_slider = tk.Scale(self.mainframe, from_ = -50, to = 50, orient = tk.HORIZONTAL, variable = self.local_volume_var, showvalue = False)
            CreateToolTip(self.local_volume_slider_lbl, "Volume adjustment for files being played into Local device")

            self.volume_slider_lbl.grid(row = 9, column = 1)
            self.volume_slider.grid(row = 9, column = 2)
            self.local_volume_slider_lbl.grid(row = 10, column = 1)
            self.local_volume_slider.grid(row = 10, column = 2)

            self.quit_btn = tk.Button(self.mainframe, width = 15, text = "Close", command = self.end)
            self.quit_btn.grid(row = 11, column = 2, columnspan = 2)

            SETTINGS.toggle_HM(False)
            self.run()

    def refocus(self, event):
        self.root.after(200, self.root.wm_attributes("-topmost", 0))
        # if (self.created_time + 500) < pygame.time.get_ticks():
        #   self.root.bell()
        # self.root.focus_force()
  #       #

    def change_dropdown_output(self, *args):
        SETTINGS.output_device = self.dropdown_output_var.get()

    def change_dropdown_local(self, *args):
        SETTINGS.local_audio_device = self.dropdown_local_var.get()

    def change_dropdown_queue(self, *args):
        SETTINGS.queue = self.dropdown_queue.get()
        stop_all_audio()

    def toggle_queue(self):
        toggle_queue_audio()
        if SETTINGS.queue == True:
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
        
        try:
            SETTINGS.delay = int(self.delayvar.get())
        except ValueError:
            print "Delay must be an integer"

        try:
            SETTINGS.audio_chunk_size = int(self.chunkvar.get())
        except ValueError:
            print "Chunk size must be an integer"

        SETTINGS.output_device = self.dropdown_output_var.get()
        SETTINGS.queue = self.dropdown_queue.get()

        SETTINGS.equalize_audio = self.equalize_toggle_var.get()
        SETTINGS.equalize_target = self.equalize_var.get()

        SETTINGS.play_local = bool(self.play_local_toggle_var.get())
        SETTINGS.out_volume = self.volume_var.get()
        SETTINGS.local_volume = self.local_volume_var.get()

        SETTINGS.toggle_HM()
        ONGOING_FUNCTIONS.remove(self)

        self.root.destroy()
