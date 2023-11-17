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

import threading
import simpleaudio as sa
import time


class PomodoroTimer:
    # A Pomodoro timer that uses a separate thread to count down time.

    def __init__(self, transition_callback=None):
        # Initialize the timer with default work time and no active thread.
        
        self.work_time = 25 * 60  # Default work time set to 25 minutes (in seconds).
        self.short_break = 5 * 60  # Default short break in seconds
        self.long_break = 15 * 60  # Default long break in seconds
        
        self.cycles_before_long_break = 4 # Default cycles
        self.current_cycle = 1 # Cycle counter
        
        self.on_break = False # Check if on break
        self.is_running = False  # Flag to indicate if the timer is running.
        self.time_left = (
            self.work_time
        )  # Time remaining is initialized to the full work time.
        
        self.transition_callback = transition_callback
        self.thread = None  # Thread object for the timer's countdown.
        self.playback_active = (
            threading.Event()
        )  # Event flag for managing audio playback.
        self.selected_noise_path = None  # Path to the selected background noise file.
        self.currently_playing_wave_object = (
            None  # Reference to the audio playback object.
        )

    @property
    def is_default(self):
        # Check if the timer is at its default state.
        return self.time_left == self.work_time and not self.is_running

    def start(self):
        # Start the timer if it's not already running.
        if not self.is_running:
            self.is_running = True
            print("Starting timer...")  # Debug print
            self.thread = threading.Thread(target=self.run_timer)
            self.thread.start()

    def run_timer(self):
        # Handle the timer countdown logic.
        end_time = time.time() + self.time_left
        while self.is_running and time.time() < end_time:
            self.time_left = round(end_time - time.time())
            time.sleep(0.1)  # Short sleep to allow for frequent checks.
        if self.is_running:
            self.is_running = False
            self.transition()
            
    def transition(self):
        print("Transitioning timer...")  # Debug print
        if self.on_break:
            # Transition from break to work
            self.time_left = self.work_time
            self.on_break = False
            self.current_cycle += 1
        else:
            # Transition from work to break
            if self.current_cycle % self.cycles_before_long_break == 0 and self.current_cycle != 0:
                self.time_left = self.long_break
            else:
                self.time_left = self.short_break
            self.on_break = True

        self.start()  # Automatically start the next period
        
        if self.transition_callback:
            self.transition_callback()

    def stop(self):
        # Stop the timer and wait for the timer thread to finish.
        self.is_running = False
        if self.thread:
            self.thread.join()

    def reset(self):
        # Reset the timer to its default time based on current timer type
        self.stop()
        if self.on_break:
            # Reset to the appropriate break length
            if self.current_cycle >= self.cycles_before_long_break:
                self.time_left = self.long_break
            else:
                self.time_left = self.short_break
        else:
            # Reset to the work time length
            self.time_left = self.work_time

    def update_work_time(self, minutes):
        # Update the work time and reset the timer if it's not running.
        self.work_time = minutes * 60
        if not self.is_running:
            self.reset()

    def update_short_break(self, minutes):
        # Update the duration of short breaks.
        self.short_break = minutes * 60

    def update_long_break(self, minutes):
        # Update the duration of long breaks.
        self.long_break = minutes * 60

    def update_cycles_before_long_break(self, cycles):
        # Update the number of cycles before taking a long break.
        self.cycles_before_long_break = cycles

    def set_noise(self, noise_path):
        # Set the file path for the background noise.
        self.selected_noise_path = noise_path

    def play_sound_loop(self):
        # Loop to play the selected background noise continuously.
        try:
            if self.selected_noise_path:
                wave_obj = sa.WaveObject.from_wave_file(self.selected_noise_path)
                while self.playback_active.is_set():
                    self.currently_playing_wave_object = wave_obj.play()
                    self.currently_playing_wave_object.wait_done()
        except Exception as e:
            print(f"Error playing sound: {e}")

    def start_background_noise(self):
        # Start playing the background noise if a file path is set.
        if self.selected_noise_path:
            self.playback_active.set()
            threading.Thread(target=self.play_sound_loop).start()

    def stop_background_noise(self):
        # Stop any currently playing background noise.
        if self.currently_playing_wave_object:
            self.currently_playing_wave_object.stop()
        self.playback_active.clear()
