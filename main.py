# Copyright 2023 Kai Townsend

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pomodoro import PomodoroTimer
import threading
import simpleaudio as sa
import tkinter
import tkinter.messagebox
import customtkinter
import json
import os
import sys
import time


class SoundManager:
    def __init__(self):
        self.current_play_objects = {}
        self.play_objects_lock = threading.Lock()

    def play_sound(self, sound_file):
        if sound_file and sound_file != "None":

            def thread_function(file):
                play_obj = sa.WaveObject.from_wave_file(file).play()
                with self.play_objects_lock:
                    self.current_play_objects[file] = play_obj
                play_obj.wait_done()
                with self.play_objects_lock:
                    if file in self.current_play_objects:
                        del self.current_play_objects[file]

            threading.Thread(target=thread_function, args=(sound_file,)).start()


class FocusModeApp:
    def __init__(self):
        # Initialize the PomodoroTimer
        self.timer = PomodoroTimer(transition_callback=self.on_timer_transition)
        # Initialize the SoundManager
        self.sound_manager = SoundManager()
        # Initialize main window
        self.window = customtkinter.CTk()
        # Path to the icon file
        if os.name == "nt":
            # Windows
            self.window.iconbitmap("icons/icon.ico")
        else:
            # Other operating systems (untested)
            icon_image = tk.PhotoImage(file="icons/icon.png")
            self.window.iconphoto(True, icon_image)
        # Default settings
        self.default_settings = {
            "appearance_mode": "Dark",
            "color_theme": "blue",
            "work_time": 25,
            "short_break": 5,
            "long_break": 15,
            "cycles_before_long_break": 3,
            "background_noise": "None",
        }
        # Appearance mode options
        self.appearance_mode_colors = {
            "Dark": "#2b2b2b",
            "Light": "#dbdbdb",
        }
        # Background noise options
        self.noise_options = {
            "None": None,  # No sound
            "White Noise": "sounds/whitenoise.wav",
        }
        # Initialize with default noise value
        self.noise_var = customtkinter.StringVar(value="None")
        # Set settings file
        self.settings_file = "app_settings.json"
        # Load settings
        self.current_settings = self.load_settings()
        # Apply settings
        self.apply_settings(self.current_settings)
        # Initialize the UI
        self.initialize_ui()

    def initialize_ui(self):
        # Configure main window
        self.window.title("Focus Mode")
        self.window.geometry("1100x580")
        self.window.resizable(False, False)

        # Configure grid layout
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure((2, 3), weight=0)
        self.window.grid_rowconfigure((0, 1, 2), weight=1)

        self.setup_sidebar()
        self.setup_main_area()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.update_scrollregion()
        self.update_timer_display()

    def setup_sidebar(self):
        # Create the sidebar canvas
        self.sidebar_width = 200
        self.sidebar_bg_color = "#2b2b2b"

        self.sidebar_canvas = tkinter.Canvas(
            self.window,
            bg=self.sidebar_bg_color,
            highlightthickness=0,
            width=self.sidebar_width,
        )
        self.sidebar_canvas.pack(side="left", fill="y", expand=False)

        # Create the scrollbar for the sidebar
        self.sidebar_scrollbar = customtkinter.CTkScrollbar(
            self.window, command=self.sidebar_canvas.yview
        )
        self.sidebar_scrollbar.pack(side="left", fill="y")

        # Configure the canvas scroll command
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)

        # Create the frame to hold sidebar contents
        self.sidebar_frame = customtkinter.CTkFrame(
            master=self.sidebar_canvas,
            width=self.sidebar_width,
            bg_color=self.sidebar_bg_color,
            corner_radius=0,
        )
        frame_id = self.sidebar_canvas.create_window(
            (0, 0), window=self.sidebar_frame, anchor="nw", width=200
        )

        # Bind the sidebar frame configure event to update the scroll region
        self.sidebar_frame.bind("<Configure>", self.update_scrollregion)

        # Create sidebar widgets
        self.sidebar_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Settings",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.sidebar_label.pack(padx=20, pady=(20, 10))

        # Appearance Mode Dropdown
        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.appearance_mode_label.pack(padx=20, pady=(10, 0), fill="x")

        self.appearance_mode_optionmenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark"],
            command=self.change_appearance_mode,
        )
        self.appearance_mode_optionmenu.set(
            self.current_settings["appearance_mode"].capitalize()
        )
        self.appearance_mode_optionmenu.pack(padx=20, pady=(10, 0), fill="x")

        # Color Theme Dropdown
        self.color_theme_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Color Theme:", anchor="w"
        )
        self.color_theme_label.pack(padx=20, pady=(20, 0), fill="x")

        self.color_theme_optionmenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Blue", "Green"],
            command=self.change_color_theme,
        )
        self.color_theme_optionmenu.set(
            self.current_settings["color_theme"].capitalize()
        )
        self.color_theme_optionmenu.pack(padx=20, pady=(10, 10), fill="x")

        # Background Noise Dropdown
        self.noise_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Background Noise:", anchor="w"
        )
        self.noise_label.pack(padx=20, pady=(20, 0), fill="x")

        self.noise_optionmenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            variable=self.noise_var,
            values=list(self.noise_options.keys()),
            command=self.change_noise_selection,
        )
        self.noise_optionmenu.set(self.current_settings["background_noise"])
        self.noise_optionmenu.pack(padx=20, pady=(10, 10), fill="x")

        # Sliders for the Pomodoro settings
        # Work Time Slider
        self.work_time_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Work Time (minutes):"
        )
        self.work_time_label.pack(padx=20, pady=(10, 0))

        self.work_time_slider = customtkinter.CTkSlider(
            self.sidebar_frame, from_=3, to=60, command=self.update_work_time
        )
        self.work_time_slider.set(self.timer.work_time // 60)
        self.work_time_slider.pack(padx=20, pady=(5, 0))

        self.work_time_value_label = customtkinter.CTkLabel(self.sidebar_frame)
        self.work_time_value_label.pack(padx=20, pady=(0, 10))
        self.work_time_value_label.configure(
            text=f"{self.timer.work_time // 60} minutes"
        )

        # Short Break Slider
        self.short_break_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Short Break (minutes):"
        )
        self.short_break_label.pack(padx=20, pady=(10, 0))

        self.short_break_slider = customtkinter.CTkSlider(
            self.sidebar_frame, from_=1, to=25, command=self.update_short_break
        )
        self.short_break_slider.set(self.timer.short_break // 60)
        self.short_break_slider.pack(padx=20, pady=(5, 0))

        self.short_break_value_label = customtkinter.CTkLabel(self.sidebar_frame)
        self.short_break_value_label.pack(padx=20, pady=(0, 10))
        self.short_break_value_label.configure(
            text=f"{self.timer.short_break // 60} minutes"
        )

        # Long Break Slider
        self.long_break_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Long Break (minutes):"
        )
        self.long_break_label.pack(padx=20, pady=(10, 0))

        self.long_break_slider = customtkinter.CTkSlider(
            self.sidebar_frame, from_=3, to=60, command=self.update_long_break
        )
        self.long_break_slider.set(self.timer.long_break // 60)
        self.long_break_slider.pack(padx=20, pady=(5, 0))

        self.long_break_value_label = customtkinter.CTkLabel(self.sidebar_frame)
        self.long_break_value_label.pack(padx=20, pady=(0, 10))
        self.long_break_value_label.configure(
            text=f"{self.timer.long_break // 60} minutes"
        )

        # Cycles Before Long Break Slider
        self.cycles_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Cycles Before Long Break:"
        )
        self.cycles_label.pack(padx=20, pady=(10, 0))

        self.cycles_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=2,
            to=8,
            command=self.update_cycles_before_long_break,
        )
        self.cycles_slider.set(self.timer.cycles_before_long_break)
        self.cycles_slider.pack(padx=20, pady=(5, 0))

        self.cycles_value_label = customtkinter.CTkLabel(self.sidebar_frame)
        self.cycles_value_label.pack(padx=20, pady=(0, 10))
        self.cycles_value_label.configure(text=f"{self.timer.cycles_before_long_break}")

    def setup_main_area(self):
        # Get the current width and height of the window and calculate the content width
        self.window_width = self.window.winfo_width()
        self.content_width = (
            self.window_width - self.sidebar_width
        )  # Width excluding the sidebar
        self.button_width = 200
        self.button_height = 80
        self.button_spacing = 20
        self.vertical_center = 0.4
        self.total_buttons_width = (3 * self.button_width) + (2 * self.button_spacing)

        # Calculate the horizontal center of the content area for the timer and buttons
        self.content_center_x = self.sidebar_width + (self.content_width / 2)

        # Timer Display
        self.timer_display = customtkinter.CTkLabel(
            self.window, text="25:00", font=("Courier", 200)
        )
        self.timer_display.place(
            relx=0.5,
            x=(self.sidebar_width / 2),
            rely=self.vertical_center,
            anchor="center",
        )

        # Label to display the cycles count
        self.timer_state_label = customtkinter.CTkLabel(
            self.window,
            text=f"Work Time | Cycle: {self.timer.current_cycle}",
            font=("Courier", 32),
        )
        self.timer_state_label.place(
            relx=0.4925, x=(self.sidebar_width / 2), rely=0.2, anchor="center"
        )

        # Control Buttons
        # Start Button
        self.start_button = customtkinter.CTkButton(
            self.window,
            text="Start",
            font=("Courier", 36),
            command=self.start_or_resume_timer,
            width=self.button_width,
            height=self.button_height,
        )
        self.start_button_x = self.content_center_x - (self.total_buttons_width / 2)
        self.start_button.place(
            x=self.start_button_x, rely=self.vertical_center + 0.25, anchor="w"
        )

        # Stop Button
        self.stop_button = customtkinter.CTkButton(
            self.window,
            text="Stop",
            font=("Courier", 36),
            command=self.stop_timer,
            width=self.button_width,
            height=self.button_height,
            state="disabled",  # default for startup
        )
        self.stop_button.place(
            x=self.start_button_x + self.button_width + self.button_spacing,
            rely=self.vertical_center + 0.25,
            anchor="w",
        )

        # Reset Button
        self.reset_button = customtkinter.CTkButton(
            self.window,
            text="Reset",
            font=("Courier", 36),
            command=self.reset_timer,
            width=self.button_width,
            height=self.button_height,
            state="disabled",  # default for startup
        )
        self.reset_button.place(
            x=self.start_button_x + 2 * (self.button_width + self.button_spacing),
            rely=self.vertical_center + 0.25,
            anchor="w",
        )

        # Cycle Counter Reset Button
        self.cycle_reset_button = customtkinter.CTkButton(
            self.window,
            text="Reset Cycles",
            font=("Courier", 36),
            command=self.reset_cycles,
            width=1.57 * self.button_width,
            height=self.button_height,
            state="disabled",  # default for startup
        )
        self.cycle_reset_button.place(
            x=self.start_button_x, rely=self.vertical_center + 0.42, anchor="w"
        )

        # Skip Current Timer Button
        self.skip_timer_button = customtkinter.CTkButton(
            self.window,
            text="Skip Timer",
            font=("Courier", 36),
            command=self.skip_timer,
            width=1.55 * self.button_width,
            height=self.button_height,
        )
        self.skip_timer_button.place(
            x=self.start_button_x + 1.65 * self.button_width,
            rely=self.vertical_center + 0.42,
            anchor="w",
        )

    def update_scrollregion(self, event=None):
        self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))

    def run(self):
        # Start the Tkinter event loop
        self.window.mainloop()

    def on_closing(self):
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_timer()
            self.save_settings(self.current_settings)  # Save settings before closing
            self.window.destroy()  # Close the application window

            # Make sure script ends (Temporary fix for script not ending)
            time.sleep(0.5)
            os._exit(0)

    def restart_application(self):
        self.save_settings(self.current_settings)  # Save the current settings
        os.execl(sys.executable, sys.executable, *sys.argv)

    # Settings management functions
    def save_settings(self, settings=None):
        if settings is None:
            settings = self.default_settings
        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            self.save_settings(self.default_settings)
            return self.default_settings

        with open(self.settings_file, "r") as f:
            settings = json.load(f)

        # Ensure all expected settings are present
        for key, value in self.default_settings.items():
            settings.setdefault(key, value)

        return settings

    def apply_settings(self, settings):
        # Apply appearance and color theme settings
        customtkinter.set_appearance_mode(
            settings.get("appearance_mode", self.default_settings["appearance_mode"])
        )
        customtkinter.set_default_color_theme(
            settings.get("color_theme", self.default_settings["color_theme"])
        )

        # Apply Pomodoro timer settings
        self.timer.update_work_time(
            settings.get("work_time", self.default_settings["work_time"])
        )
        self.timer.update_short_break(
            settings.get("short_break", self.default_settings["short_break"])
        )
        self.timer.update_long_break(
            settings.get("long_break", self.default_settings["long_break"])
        )
        self.timer.update_cycles_before_long_break(
            settings.get(
                "cycles_before_long_break",
                self.default_settings["cycles_before_long_break"],
            )
        )

        # Apply background noise setting
        noise_selection = settings.get(
            "background_noise", self.default_settings["background_noise"]
        )
        if noise_selection:  # If a noise is selected
            self.noise_var.set(noise_selection)  # Update the StringVar for the UI
            selected_noise_path = self.noise_options.get(noise_selection, None)
            self.timer.selected_noise_path = (
                selected_noise_path  # Set the noise path in the PomodoroTimer
            )

    # UI event handling functions
    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self.current_settings["appearance_mode"] = new_appearance_mode.lower()

        # Canvas background color set to appearance mode
        canvas_color = self.appearance_mode_colors.get(
            new_appearance_mode.capitalize(), "#2b2b2b"
        )
        if hasattr(self, "sidebar_canvas"):  # If sidebar_canvas exists
            self.sidebar_canvas.configure(bg=canvas_color)

        self.save_settings(self.current_settings)

    def change_color_theme(self, new_color_theme):
        new_color_theme = new_color_theme.lower()

        if new_color_theme != self.current_settings["color_theme"]:
            if tkinter.messagebox.askyesno(
                "Restart Required",
                "The application must restart for the theme change to take effect. Restart now?",
            ):
                self.current_settings["color_theme"] = new_color_theme
                self.save_settings(self.current_settings)
                self.restart_application()
            else:
                # Reset the OptionMenu to the previous value, if necessary
                self.color_theme_optionmenu.set(
                    self.current_settings["color_theme"].capitalize()
                )

    def change_noise_selection(self, noise_name):
        selected_noise_path = self.noise_options.get(noise_name, None)
        self.current_settings["background_noise"] = noise_name

        self.timer.stop_background_noise()

        if selected_noise_path is None:
            self.timer.set_noise(None)
        else:
            self.timer.set_noise(selected_noise_path)

        self.save_settings(self.current_settings)

    # Pomodoro timer interaction functions
    def update_work_time(self, value):
        int_value = round(float(value))
        self.timer.update_work_time(
            int_value
        )  # Update the work time in the Pomodoro timer
        self.work_time_value_label.configure(
            text=f"{int_value} minutes"
        )  # Update the label
        self.update_timer_display()
        self.current_settings["work_time"] = int_value  # Update the current settings
        self.save_settings(self.current_settings)  # Save the updated settings

    def update_short_break(self, value):
        int_value = round(float(value))
        self.timer.update_short_break(int_value)
        self.short_break_value_label.configure(text=f"{int_value} minutes")
        self.update_timer_display()
        self.current_settings["short_break"] = int_value
        self.save_settings(self.current_settings)

    def update_long_break(self, value):
        int_value = round(float(value))
        self.timer.update_long_break(int_value)
        self.long_break_value_label.configure(text=f"{int_value} minutes")
        self.update_timer_display()
        self.current_settings["long_break"] = int_value
        self.save_settings(self.current_settings)

    def update_cycles_before_long_break(self, value):
        int_value = round(float(value))
        self.timer.update_cycles_before_long_break(int_value)
        self.cycles_value_label.configure(text=str(int_value))
        self.update_timer_display()
        self.current_settings["cycles_before_long_break"] = int_value
        self.save_settings(self.current_settings)

    def update_timer_display(self):
        # Calculate the minutes and seconds from the time left
        minutes, seconds = divmod(self.timer.time_left, 60)
        # Update the timer display label
        self.timer_display.configure(text=f"{minutes:02d}:{seconds:02d}")
        # If the timer is running, keep updating the label every second
        if self.timer.is_running:
            self.window.after(1000, self.update_timer_display)

    def update_timer_button_states(self):
        if self.timer.is_running:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.reset_button.configure(state="normal")
        else:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            # Enable the reset button only if the timer is not at its default state
            if not self.timer.is_default:
                self.reset_button.configure(state="normal")
            else:
                self.reset_button.configure(state="disabled")

    def update_timer_state_label(self):
        self.current_cycle_len = len(str(self.timer.current_cycle))
        self.timer_state_char_width = 0.009

        if self.timer.on_break:
            if self.timer.time_left == self.timer.long_break:
                self.timer_state_label.place(
                    relx=0.4832
                    + self.timer_state_char_width * (self.current_cycle_len - 1),
                    x=(self.sidebar_width / 2),
                    rely=0.2,
                    anchor="center",
                )
                self.timer_state_label.configure(
                    text=f"Long Break | Cycle: {self.timer.current_cycle}"
                )
            else:
                self.timer_state_label.place(
                    relx=0.475
                    + self.timer_state_char_width * (self.current_cycle_len - 1),
                    x=(self.sidebar_width / 2),
                    rely=0.2,
                    anchor="center",
                )
                self.timer_state_label.configure(
                    text=f"Short Break | Cycle: {self.timer.current_cycle}"
                )
        else:
            self.timer_state_label.place(
                relx=0.4925
                + self.timer_state_char_width * (self.current_cycle_len - 1),
                x=(self.sidebar_width / 2),
                rely=0.2,
                anchor="center",
            )
            self.timer_state_label.configure(
                text=f"Work Time | Cycle: {self.timer.current_cycle}"
            )

        if self.timer.current_cycle <= 1 and not self.timer.on_break:
            self.cycle_reset_button.configure(state="disabled")
        else:
            self.cycle_reset_button.configure(state="normal")

    def update_ui_for_timer_transition(self):
        # Updates the UI when the timer transitions from one type of timer to another
        self.update_timer_display()
        self.update_timer_button_states()

    def on_timer_transition(self):
        # Check if the application is running in the main thread
        if threading.current_thread() == threading.main_thread():
            self.update_ui_for_timer_transition()
        else:
            # Schedule the update to be run in the main thread
            self.window.after(0, self.update_ui_for_timer_transition)

        self.update_timer_state_label()
        self.sound_manager.play_sound("sounds/timerstop.wav")

    def start_or_resume_timer(self):
        if not self.timer.is_running:
            self.timer.start()  # Start or resume the Pomodoro timer
            if self.timer.selected_noise_path:
                self.timer.start_background_noise()
            self.update_timer_display()
            self.update_timer_button_states()
            self.update_timer_controls_state()
            self.sound_manager.play_sound("sounds/timerstart.wav")
            if not self.timer.on_break:
                self.noise_optionmenu.configure(state="disabled")

    def stop_timer(self, playnoise=None):
        self.timer.stop()
        self.timer.stop_background_noise()
        self.update_timer_button_states()
        self.update_timer_controls_state()
        if playnoise:
            self.sound_manager.play_sound("sounds/timerstop.wav")
        self.noise_optionmenu.configure(state="normal")

    def reset_timer(self):
        self.timer.reset()
        self.timer.stop_background_noise()
        self.update_timer_display()
        self.update_timer_button_states()
        self.update_timer_state_label()
        self.update_timer_controls_state()
        self.sound_manager.play_sound("sounds/timerreset.wav")
        self.noise_optionmenu.configure(state="normal")

    def reset_cycles(self):
        # Reset the cycle counter and the timer.
        self.reset_timer()
        self.timer.current_cycle = 1
        self.timer.on_break = False
        self.timer.time_left = self.timer.work_time

        self.update_timer_display()
        self.update_timer_state_label()
        self.update_timer_controls_state()
        self.reset_button.configure(state="disabled")  # hard coded for now

    def skip_timer(self):
        # End the current cycle and move to the next one.
        self.timer.transition()
        self.stop_timer(playnoise=False)
        self.reset_button.configure(state="disabled")  # hard coded for now

    def update_timer_controls_state(self):
        # Enable controls only if the timer is in the default state
        if self.timer.is_default and self.timer.current_cycle == 1:
            self.work_time_slider.configure(state="normal")
            self.short_break_slider.configure(state="normal")
            self.long_break_slider.configure(state="normal")
            self.cycles_slider.configure(state="normal")
        else:
            self.work_time_slider.configure(state="disabled")
            self.short_break_slider.configure(state="disabled")
            self.long_break_slider.configure(state="disabled")
            self.cycles_slider.configure(state="disabled")


# Main loop
if __name__ == "__main__":
    app = FocusModeApp()
    app.run()
