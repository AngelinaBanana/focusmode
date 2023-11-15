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


def restart_application():
    save_settings(current_settings)  # Save current_settings to app_settings.json
    # Restart
    python = sys.executable
    os.execl(python, python, *sys.argv)


def on_closing():
    if tkinter.messagebox.askokcancel(
        "Quit", "Do you want to quit?"
    ):  # Check if user wants to quit
        stop_timer()
        save_settings(current_settings)  # Save current_settings to app_settings.json
        window.destroy()


def play_sound(sound_file):
    if sound_file:

        def thread_function(file):
            play_obj = sa.WaveObject.from_wave_file(file).play()
            current_play_objects[sound_file] = play_obj
            play_obj.wait_done()  # Wait for the sound to finish playing
            del current_play_objects[
                sound_file
            ]  # Remove the play object from the dictionary

        threading.Thread(target=thread_function, args=(sound_file,)).start()


# Functions for settings
def save_settings(settings=None):
    if settings is None:
        settings = default_settings
    with open(settings_file, "w") as f:  # Write to app_settings.json
        json.dump(settings, f, indent=4)


def load_settings():
    if not os.path.exists(settings_file):
        # If the settings file doesn't exist, create it with the default settings
        save_settings(default_settings)
        return default_settings
    with open(settings_file, "r") as f:  # Read from app_settings.json
        settings = json.load(f)
    # Make sure all expected settings are present, use default if any are missing
    for key, value in default_settings.items():
        settings.setdefault(key, value)
    return settings


def apply_settings(settings):
    # Apply current app settings
    customtkinter.set_appearance_mode(
        settings.get("appearance_mode", default_settings["appearance_mode"])
    )
    customtkinter.set_default_color_theme(
        settings.get("color_theme", default_settings["color_theme"])
    )
    noise_selection = settings.get(
        "background_noise", default_settings["background_noise"]
    )
    if noise_selection:  # If a noise is selected
        noise_var.set(noise_selection)
        pomodoro_timer.selected_noise_path = noise_options[noise_selection]

    # Apply Pomodoro timer settings
    pomodoro_timer.update_work_time(
        settings.get("work_time", default_settings["work_time"])
    )
    pomodoro_timer.update_short_break(
        settings.get("short_break", default_settings["short_break"])
    )
    pomodoro_timer.update_long_break(
        settings.get("long_break", default_settings["long_break"])
    )
    pomodoro_timer.update_cycles_before_long_break(
        settings.get(
            "cycles_before_long_break", default_settings["cycles_before_long_break"]
        )
    )

    # Update the slider positions and labels if they exist
    if "work_time_slider" in globals() and "work_time_value_label" in globals():
        work_time_slider.set(settings.get("work_time", default_settings["work_time"]))
        work_time_value_label.configure(
            text=f"{settings.get('work_time', default_settings['work_time'])} minutes"
        )
    # Repeat for other sliders and labels
    if "short_break_slider" in globals() and "short_break_value_label" in globals():
        short_break_slider.set(
            settings.get("short_break", default_settings["short_break"])
        )
        short_break_value_label.configure(
            text=f"{settings.get('short_break', default_settings['short_break'])} minutes"
        )
    if "long_break_slider" in globals() and "long_break_value_label" in globals():
        long_break_slider.set(
            settings.get("long_break", default_settings["long_break"])
        )
        long_break_value_label.configure(
            text=f"{settings.get('long_break', default_settings['long_break'])} minutes"
        )
    if "cycles_slider" in globals() and "cycles_value_label" in globals():
        cycles_slider.set(
            settings.get(
                "cycles_before_long_break", default_settings["cycles_before_long_break"]
            )
        )
        cycles_value_label.configure(
            text=str(
                settings.get(
                    "cycles_before_long_break",
                    default_settings["cycles_before_long_break"],
                )
            )
        )


# Functions for widget events
def change_appearance_mode(new_appearance_mode):
    global current_settings, sidebar_canvas
    customtkinter.set_appearance_mode(new_appearance_mode)
    current_settings["appearance_mode"] = new_appearance_mode.lower()

    # Set the canvas background color based on the appearance mode
    canvas_color = appearance_mode_colors.get(
        new_appearance_mode.capitalize(), "#2b2b2b"
    )
    sidebar_canvas.configure(bg=canvas_color)  # Update the canvas background color

    save_settings(current_settings)  # Save current_settings to app_settings.json


def change_color_theme(new_color_theme):
    global current_settings

    # Convert to lowercase for internal use
    new_color_theme = new_color_theme.lower()

    # Check if the new color theme is different from the current one
    if new_color_theme != current_settings["color_theme"]:
        # Prompt the user to restart the application
        if tkinter.messagebox.askyesno(
            "Restart Required",
            "The application must restart for the theme change to take effect. Restart now?",
        ):
            # If the user confirms, save the new settings and restart
            current_settings["color_theme"] = new_color_theme
            save_settings(
                current_settings
            )  # Save current_settings to app_settings.json
            restart_application()
        else:
            # If the user cancels, reset the OptionMenu to the previous value
            # Use capitalize() to match the OptionMenu display format
            color_theme_optionmenu.set(current_settings["color_theme"].capitalize())
    else:
        # If the new theme is the same as the current, do nothing and ensure OptionMenu reflects this
        color_theme_optionmenu.set(current_settings["color_theme"].capitalize())


def change_noise_selection(noise_name):
    global current_settings, noise_options
    selected_noise_path = noise_options[noise_name]
    current_settings["background_noise"] = noise_name

    pomodoro_timer.stop_background_noise()

    # If "None" is selected, stop any playing noise
    if selected_noise_path is None:
        pomodoro_timer.set_noise("None")
    else:
        # Set the new noise path in the PomodoroTimer instance
        pomodoro_timer.set_noise(selected_noise_path)

    save_settings(current_settings)  # Save current_settings to app_settings.json


# Functions for pomodoro timer
def update_work_time(value):
    int_value = round(float(value))
    work_time_value_label.configure(text=f"{int_value} minutes")

    pomodoro_timer.update_work_time(int_value)
    update_timer_display()

    current_settings["work_time"] = int_value
    save_settings(current_settings)  # Save current_settings to app_settings.json


def update_short_break(value):
    int_value = round(float(value))
    short_break_value_label.configure(text=f"{int_value} minutes")

    pomodoro_timer.update_short_break(int_value)
    update_timer_display()

    current_settings["short_break"] = int_value
    save_settings(current_settings)  # Save current_settings to app_settings.json


def update_long_break(value):
    int_value = round(float(value))
    long_break_value_label.configure(text=f"{int_value} minutes")

    pomodoro_timer.update_long_break(int_value)
    update_timer_display()

    current_settings["long_break"] = int_value
    save_settings(current_settings)  # Save current_settings to app_settings.json


def update_cycles_before_long_break(value):
    int_value = round(float(value))
    cycles_value_label.configure(text=str(int_value))

    pomodoro_timer.update_cycles_before_long_break(int_value)
    update_timer_display()

    current_settings["cycles_before_long_break"] = int_value
    save_settings(current_settings)  # Save current_settings to app_settings.json


def update_timer_display():
    # This function updates the timer's display label with the current time left
    minutes, seconds = divmod(pomodoro_timer.time_left, 60)
    timer_display.configure(text=f"{minutes:02d}:{seconds:02d}")
    # If the timer is running, keep updating the label every second
    if pomodoro_timer.is_running:
        window.after(1000, update_timer_display)


def update_timer_button_states():
    if pomodoro_timer.is_running:
        start_button.configure(state="disabled")
        stop_button.configure(state="normal")
        reset_button.configure(state="normal")
    else:
        start_button.configure(state="normal")
        stop_button.configure(state="disabled")
        # Only enable the reset button if the timer is not at the default value
        if pomodoro_timer.is_default:
            reset_button.configure(state="disabled")
        else:
            reset_button.configure(state="normal")


def start_or_resume_timer():
    if not pomodoro_timer.is_running:
        pomodoro_timer.start()  # This should handle both starting and resuming
        if pomodoro_timer.selected_noise_path:
            pomodoro_timer.start_background_noise()
        update_timer_display()
        update_timer_button_states()
        play_sound("sounds/timerstart.wav")
        noise_optionmenu.configure(state="disabled")
        # Disable sliders while the timer is running
        disable_sliders()


def stop_timer():
    pomodoro_timer.stop()
    pomodoro_timer.stop_background_noise()
    update_timer_button_states()
    play_sound("sounds/timerstop.wav")
    noise_optionmenu.configure(state="normal")
    # Enable sliders when the timer is stopped
    enable_sliders()


def reset_timer():
    pomodoro_timer.reset()
    pomodoro_timer.stop_background_noise()
    update_timer_display()
    update_timer_button_states()
    play_sound("sounds/timerreset.wav")
    noise_optionmenu.configure(state="normal")
    # Enable sliders when the timer is reset
    enable_sliders()


def disable_sliders():
    work_time_slider.configure(state="disabled")
    short_break_slider.configure(state="disabled")
    long_break_slider.configure(state="disabled")
    cycles_slider.configure(state="disabled")


def enable_sliders():
    work_time_slider.configure(state="normal")
    short_break_slider.configure(state="normal")
    long_break_slider.configure(state="normal")
    cycles_slider.configure(state="normal")


pomodoro_timer = PomodoroTimer()

appearance_mode_colors = {
    "Dark": "#2b2b2b",  # Dark mode background color
    "Light": "#dbdbdb",  # Light mode background color
}

noise_options = {
    "None": None,  # No sound
    "White Noise": "sounds/whitenoise.wav",
}

# This dictionary will store the 'play object' returned by simpleaudio when a sound is played
current_play_objects = {}

current_settings = {}

# Default settings
default_settings = {
    "appearance_mode": "Dark",
    "color_theme": "blue",
    "work_time": 25,
    "short_break": 5,
    "long_break": 15,
    "cycles_before_long_break": 4,
    "background_noise": "None",
}

settings_file = "app_settings.json"

# Initialize main window
window = customtkinter.CTk()

# Configure window
window.title("Focus Mode")
window.geometry(f"{1100}x{580}")
window.resizable(False, False)

# Configure grid layout (4x4)
window.grid_columnconfigure(1, weight=1)
window.grid_columnconfigure((2, 3), weight=0)
window.grid_rowconfigure((0, 1, 2), weight=1)

window.protocol("WM_DELETE_WINDOW", on_closing)

noise_var = customtkinter.StringVar(value="None")  # Default value is "None"

# Set default appearance and color theme if no settings file is found
current_settings = load_settings()
apply_settings(current_settings)

sidebar_width = 200
sidebar_bg_color = "#2b2b2b"

# Create the canvas and a scrollbar within the main window
sidebar_canvas = tkinter.Canvas(
    window, bg=sidebar_bg_color, highlightthickness=0, width=sidebar_width
)
sidebar_canvas.pack(side="left", fill="y", expand=False)

sidebar_scrollbar = customtkinter.CTkScrollbar(window, command=sidebar_canvas.yview)
sidebar_scrollbar.pack(side="left", fill="y")

sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

# Create the frame for the sidebar contents
sidebar_frame = customtkinter.CTkFrame(
    master=sidebar_canvas,
    width=sidebar_width,
    bg_color=sidebar_bg_color,
    corner_radius=0,
)
frame_id = sidebar_canvas.create_window(
    (0, 0), window=sidebar_frame, anchor="nw", width=sidebar_width
)


# Function to update the canvas's scrollregion when its contents change size
def update_scrollregion(event=None):  # Allow calling with no arguments
    sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))


sidebar_frame.bind("<Configure>", update_scrollregion)

# Sidebar widgets
sidebar_label = customtkinter.CTkLabel(
    sidebar_frame, text="Settings", font=customtkinter.CTkFont(size=20, weight="bold")
)
sidebar_label.pack(padx=20, pady=(20, 10))

# Set the canvas color based on the current appearance mode
change_appearance_mode(current_settings["appearance_mode"])

# Sidebar appearance dropdown
appearance_mode_label = customtkinter.CTkLabel(
    sidebar_frame, text="Appearance Mode:", anchor="w"
)
appearance_mode_label.pack(padx=20, pady=(10, 0), fill="x")
appearance_mode_optionmenu = customtkinter.CTkOptionMenu(
    sidebar_frame, values=["Light", "Dark"], command=change_appearance_mode
)
appearance_mode_optionmenu.set(current_settings["appearance_mode"].capitalize())
appearance_mode_optionmenu.pack(padx=20, pady=(10, 0), fill="x")

# Sidebar color theme dropdown
color_theme_label = customtkinter.CTkLabel(
    sidebar_frame, text="Color Theme:", anchor="w"
)
color_theme_label.pack(padx=20, pady=(20, 0), fill="x")
color_theme_optionmenu = customtkinter.CTkOptionMenu(
    sidebar_frame, values=["Blue", "Green"], command=change_color_theme
)
color_theme_optionmenu.set(current_settings["color_theme"].capitalize())
color_theme_optionmenu.pack(padx=20, pady=(10, 10), fill="x")
# Add a selection menu for noise options
noise_label = customtkinter.CTkLabel(
    sidebar_frame, text="Background Noise:", anchor="w"
)
noise_label.pack(padx=20, pady=(20, 0), fill="x")
noise_optionmenu = customtkinter.CTkOptionMenu(
    sidebar_frame,
    variable=noise_var,
    values=list(noise_options.keys()),
    command=change_noise_selection,
)
noise_optionmenu.set(current_settings["background_noise"])
noise_optionmenu.pack(padx=20, pady=(10, 10), fill="x")

# Sliders for the Pomodoro settings
# Labels for the sliders
work_time_label = customtkinter.CTkLabel(sidebar_frame, text="Work Time (minutes):")
short_break_label = customtkinter.CTkLabel(sidebar_frame, text="Short Break (minutes):")
long_break_label = customtkinter.CTkLabel(sidebar_frame, text="Long Break (minutes):")
cycles_label = customtkinter.CTkLabel(sidebar_frame, text="Cycles Before Long Break:")

# Value display labels for the sliders
work_time_value_label = customtkinter.CTkLabel(sidebar_frame)
short_break_value_label = customtkinter.CTkLabel(sidebar_frame)
long_break_value_label = customtkinter.CTkLabel(sidebar_frame)
cycles_value_label = customtkinter.CTkLabel(sidebar_frame)

# Sliders
work_time_label.pack(padx=20, pady=(10, 0))
work_time_slider = customtkinter.CTkSlider(
    sidebar_frame, from_=15, to=60, command=update_work_time
)
work_time_slider.set(pomodoro_timer.work_time // 60)
work_time_slider.pack(padx=20, pady=(5, 0))
work_time_slider.configure(command=update_work_time)  # Bind update function to slider
work_time_value_label.pack(padx=20, pady=(0, 10))

short_break_label.pack(padx=20, pady=(10, 0))
short_break_slider = customtkinter.CTkSlider(
    sidebar_frame, from_=1, to=15, command=update_short_break
)
short_break_slider.set(pomodoro_timer.short_break // 60)
short_break_slider.pack(padx=20, pady=(5, 0))
short_break_slider.configure(
    command=update_short_break
)  # Bind update function to slider
short_break_value_label.pack(padx=20, pady=(0, 10))

long_break_label.pack(padx=20, pady=(10, 0))
long_break_slider = customtkinter.CTkSlider(
    sidebar_frame, from_=10, to=30, command=update_long_break
)
long_break_slider.set(pomodoro_timer.long_break // 60)
long_break_slider.pack(padx=20, pady=(5, 0))
long_break_slider.configure(command=update_long_break)  # Bind update function to slider
long_break_value_label.pack(padx=20, pady=(0, 10))

cycles_label.pack(padx=20, pady=(10, 0))
cycles_slider = customtkinter.CTkSlider(
    sidebar_frame, from_=2, to=8, command=update_cycles_before_long_break
)
cycles_slider.set(pomodoro_timer.cycles_before_long_break)
cycles_slider.pack(padx=20, pady=(5, 0))
cycles_slider.configure(
    command=update_cycles_before_long_break
)  # Bind update function to slider
cycles_value_label.pack(padx=20, pady=(0, 10))

# Update the value display labels with the initial values
work_time_value_label.configure(text=f"{pomodoro_timer.work_time // 60} minutes")
short_break_value_label.configure(text=f"{pomodoro_timer.short_break // 60} minutes")
long_break_value_label.configure(text=f"{pomodoro_timer.long_break // 60} minutes")
cycles_value_label.configure(text=f"{pomodoro_timer.cycles_before_long_break}")

# Label to display the timer
timer_display = customtkinter.CTkLabel(window, text="25:00", font=("Courier", 200))
timer_display.place(relx=0.5, rely=0.2, anchor="center")


button_width = 200
button_height = 80
button_spacing = 20
vertical_center = 0.4

# Calculate the total buttons width including the spacing
total_buttons_width = (3 * button_width) + (2 * button_spacing)

start_button = customtkinter.CTkButton(
    window,
    text="Start",
    font=("Courier", 36),
    command=start_or_resume_timer,
    width=button_width,
    height=button_height,
)
stop_button = customtkinter.CTkButton(
    window,
    text="Stop",
    font=("Courier", 36),
    command=stop_timer,
    width=button_width,
    height=button_height,
)
reset_button = customtkinter.CTkButton(
    window,
    text="Reset",
    font=("Courier", 36),
    command=reset_timer,
    width=button_width,
    height=button_height,
)


# Function to update the positions of the timer and buttons
def update_timer_and_button_positions():
    # Get the current width and height of the window and calculate the content width
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    content_width = window_width - sidebar_width  # Width excluding the sidebar

    # Calculate the horizontal center of the content area for the timer and buttons
    content_center_x = sidebar_width + (content_width / 2)

    # Center the timer display within the content area both horizontally and vertically
    timer_display.place(
        relx=0.5, x=(sidebar_width / 2), rely=vertical_center, anchor="center"
    )

    # Calculate the starting x position for the first button
    start_button_x = content_center_x - (total_buttons_width / 2)

    # Place the start button
    start_button.place(
        x=start_button_x, rely=vertical_center + 0.25, anchor="w"
    )  # Offset rely for each button

    # Place the stop button to the right of the start button with spacing
    stop_button.place(
        x=start_button_x + button_width + button_spacing,
        rely=vertical_center + 0.25,
        anchor="w",
    )

    # Place the reset button to the right of the stop button with spacing
    reset_button.place(
        x=start_button_x + 2 * (button_width + button_spacing),
        rely=vertical_center + 0.25,
        anchor="w",
    )


# Call the function to set the initial positions of the timer and buttons
update_timer_and_button_positions()

# Bind the function to the window's configure event
window.bind("<Configure>", lambda event: update_timer_and_button_positions())

update_scrollregion()
update_timer_display()

# Start the Tkinter event loop
window.mainloop()
