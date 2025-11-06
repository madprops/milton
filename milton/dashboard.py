# Standard
import os
import time
import json
import random
import threading
from typing import Any
from pathlib import Path
from tkinter import ttk, filedialog
import tkinter as tk

# Libraries
from PIL import Image, ImageTk  # type: ignore

# Modules
from .state import State


class Dashboard:
    def __init__(self, root: tk.Tk) -> None:
        self.rd_off = 999
        self.rd_fast = 1
        self.rd_normal = 5
        self.rd_slow = 10
        self.refresh_delay = self.rd_normal
        self.bg_color = "#808080"
        self.button_height = 1
        self.font_size = 14
        self.font_size_2 = 13
        self.wid_pad_x = 8
        self.wid_pad_y = 3
        self.pady_1 = 10
        self.padx_1 = 5
        self.img_width = 300
        self.img_height = 200
        self.stop_refresh = False
        self.state_file = Path(__file__).parent / Path("state.json")
        self.image_padding = 0.8
        self.button_color = "#d9d9d9"
        self.button_color_hover = "#cecece"
        self.button_text = "#000000"

        self.root = root
        self.root.configure(bg=self.bg_color)
        self.root.title("Milton")
        self.root.geometry("600x400")
        self.root.configure(bg="grey")

        self.load_state()
        self.create_main()
        self.create_image()
        self.create_bottom()

        self.noun_list = self.read_noun_list()

        self.current_image = None
        self.image_list: list[Path] = []
        self.supported_formats = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")

        self.init_source()
        self.update_speed()
        self.start()

    def start(self) -> None:
        self.scan_for_images()
        self.root.after(100, self.do_start)

    def do_start(self) -> None:
        self.do_refresh()
        self.start_refresh_thread()

    def start_refresh_thread(self) -> None:
        self.refresh_thd = threading.Thread(target=self.refresh_thread, daemon=True)
        self.refresh_thd.start()

    def create_main(self) -> None:
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)

        self.top_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.top_frame.pack(fill="x", pady=(10, 0))  # Increased padding

        self.middle_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.middle_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.bottom_frame.pack(fill="x", pady=(0, 10))

        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.pack_propagate(False)

    def create_top(self) -> None:
        for widget in self.top_frame.winfo_children():
            widget.destroy()

        # Create a frame that contains the canvas
        container = tk.Frame(self.top_frame, bg=self.bg_color)
        container.pack(fill="both", expand=True)

        # Create a canvas that will hold the labels
        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0, height=38)
        canvas.pack(fill="both", expand=True)

        # Create a frame inside the canvas to hold the labels
        labels = tk.Frame(canvas, bg=self.bg_color, pady=3)

        # Convert nouns setting to int and ensure it's at least 1
        num_nouns = max(1, int(self.state.nouns))

        # Create a list to store all noun labels
        self.noun_labels = []

        # Dynamically create the specified number of labels
        for _i in range(num_nouns):
            label = tk.Label(
                labels,
                text="---",
                font=("Arial", self.font_size),
                height=self.button_height,
                padx=self.wid_pad_x,
                pady=self.wid_pad_y,
            )

            label.pack(side=tk.LEFT, padx=self.padx_1)
            self.noun_labels.append(label)

        # Create a window in the canvas to display the labels frame
        canvas_window = canvas.create_window((0, 0), window=labels, anchor="nw")

        # Function to precisely center the labels
        def center_labels() -> None:
            # Get the exact width of both containers
            labels_width = labels.winfo_width()
            container_width = container.winfo_width()

            # Calculate the center position
            center_position = (container_width - labels_width) / 2

            # Update the window position with the exact center
            canvas.coords(canvas_window, center_position, 0)

            # Update scroll region to reflect the full width of labels
            canvas.configure(scrollregion=(0, 0, labels_width, labels.winfo_height()))

        # Update function that handles both scrolling and centering
        def update_scroll_and_center(event: Any = None) -> None:
            # Force geometry update
            labels.update_idletasks()
            center_labels()

        # Bind events to update centering when sizes change
        labels.bind("<Configure>", update_scroll_and_center)
        container.bind("<Configure>", update_scroll_and_center)

        # Add mousewheel scrolling (horizontal scroll with mousewheel)
        def _on_mousewheel(event: Any) -> None:
            # Only scroll if the content is wider than the container
            if labels.winfo_width() > container.winfo_width():
                # Scroll horizontally with the mousewheel
                if hasattr(event, "delta"):  # Windows
                    if event.delta < 0:  # Scroll right
                        canvas.xview_scroll(1, "units")
                    else:  # Scroll left
                        canvas.xview_scroll(-1, "units")
                elif hasattr(event, "num"):  # Linux
                    if event.num == 5:  # Scroll right
                        canvas.xview_scroll(1, "units")
                    elif event.num == 4:  # Scroll left
                        canvas.xview_scroll(-1, "units")

        # Bind mousewheel event to canvas
        canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
        canvas.bind("<Button-4>", _on_mousewheel)  # Linux scroll up
        canvas.bind("<Button-5>", _on_mousewheel)  # Linux scroll down

        # Force the frame to take the width it needs and update centering
        labels.update_idletasks()
        center_labels()

    def create_image(self) -> None:
        self.image_frame = tk.Frame(
            self.middle_frame,
            width=self.img_width,
            height=self.img_height,
            bg=self.bg_color,
            bd=0,
        )

        self.image_label = tk.Label(
            self.image_frame, anchor="center", bg=self.bg_color, bd=0
        )

        self.image_label.pack(fill="both", expand=True)
        self.image_frame.pack(padx=10, pady=(0, 0), fill="both", expand=True)

    def create_bottom(self) -> None:
        button_style = ttk.Style()

        button_style.configure(
            "Normal.TButton",
            background=self.button_color,
            foreground=self.button_text,
            padding=(self.wid_pad_x, self.wid_pad_y),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", self.font_size_2),
            height=self.button_height,
            bd=0,
        )

        button_style.map(
            "Normal.TButton",
            background=[("active", self.button_color_hover)],
            relief=[("active", "flat")],
        )

        combo_style = ttk.Style()

        combo_style.layout(
            "TCombobox",
            [
                (
                    "Combobox.padding",
                    {
                        "children": [
                            ("Combobox.textarea", {"sticky": "nswe"}),
                        ]
                    },
                )
            ],
        )

        combo_style.configure(
            "Normal.TCombobox",
            background=self.button_color,
            foreground=self.button_text,  # Fixed the typo from 'oreground' to 'foreground'
            padding=(5, self.button_height * 5),
            fieldbackground=self.button_color,  # Add this line to fix the issue
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )

        combo_style.configure(
            "Hover.TCombobox",
            background=self.button_color_hover,
            foreground=self.button_text,
            padding=(5, self.button_height * 5),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )

        # Configure the dropdown listbox appearance
        self.root.option_add("*TCombobox*Listbox.background", self.button_color)
        self.root.option_add("*TCombobox*Listbox.foreground", self.button_text)

        self.root.option_add(
            "*TCombobox*Listbox.selectBackground", self.button_color_hover
        )

        self.root.option_add("*TCombobox*Listbox.selectForeground", self.button_text)

        # Replace the current combobox event handlers with these:
        def on_combobox_enter(event: Any) -> None:
            widget = event.widget
            # Use configure to set style-specific properties
            widget.configure(style="Hover.TCombobox")

        def on_combobox_leave(event: Any) -> None:
            widget = event.widget
            widget.configure(style="Normal.TCombobox")

        self.root.option_add("*TCombobox*Listbox.font", ("Arial", self.font_size_2))
        self.speed_var = tk.StringVar(value="normal")

        self.speed_combo = ttk.Combobox(
            self.bottom_frame,
            width=6,
            values=["Pause", "Fast", "Normal", "Slow"],
            textvariable=self.speed_var,
            font=("Arial", self.font_size_2),
            style="Normal.TCombobox",
            state="readonly",
            justify=tk.CENTER,
        )

        self.speed_combo.bind("<Enter>", on_combobox_enter)
        self.speed_combo.bind("<Leave>", on_combobox_leave)

        self.speed_combo.set(self.state.speed)
        self.speed_combo.bind("<<ComboboxSelected>>", self.on_speed_change)

        self.select_source_btn = ttk.Button(
            self.bottom_frame,
            text="Source",
            command=self.select_source,
            style="Normal.TButton",
        )

        self.refresh_button = ttk.Button(
            self.bottom_frame,
            text="Refresh",
            command=self.refresh,
            style="Normal.TButton",
        )

        self.nouns_var = tk.StringVar(value="3")

        self.nouns_combo = ttk.Combobox(
            self.bottom_frame,
            width=3,
            values=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            textvariable=self.nouns_var,
            font=("Arial", self.font_size_2),
            style="Normal.TCombobox",
            justify=tk.CENTER,
            state="readonly",
        )

        self.nouns_combo.bind("<Enter>", on_combobox_enter)
        self.nouns_combo.bind("<Leave>", on_combobox_leave)

        self.nouns_combo.set(self.state.nouns)
        self.nouns_combo.bind("<<ComboboxSelected>>", self.on_nouns_change)

        self.close_button = ttk.Button(
            self.bottom_frame,
            text="Close",
            command=self.close,
            style="Normal.TButton",
        )

        self.select_source_btn.pack(
            side=tk.LEFT, padx=(10, self.wid_pad_x), pady=self.wid_pad_y
        )

        self.speed_combo.pack(
            side=tk.LEFT, padx=(0, self.wid_pad_x), pady=self.wid_pad_y
        )

        self.nouns_combo.pack(
            side=tk.LEFT, padx=(0, self.wid_pad_x), pady=self.wid_pad_y
        )

        self.refresh_button.pack(
            side=tk.LEFT, padx=(0, self.wid_pad_x), pady=self.wid_pad_y
        )

        self.close_button.pack(side=tk.RIGHT, padx=(5, 10), pady=self.wid_pad_y)

    def close(self) -> None:
        """Close the application."""
        self.root.quit()

    def log(self, message: str) -> None:
        """Log messages to the console."""
        print(message)  # noqa

    def read_noun_list(self) -> list[str]:
        """Read the noun list from file."""
        try:
            # Construct the path to nouns.txt relative to this file's location
            nouns_path = Path(__file__).parent / "nouns.txt"

            with nouns_path.open("r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.log(f"Error reading nouns.txt: {e}")
            return ["Error", "Loading", "Words"]

    def select_words(self) -> None:
        """Update labels with random words based on the number specified in settings."""
        try:
            num_nouns = len(self.noun_labels)

            # Select words from the noun list
            if len(self.noun_list) >= num_nouns:
                selected_words = random.sample(self.noun_list, num_nouns)
            else:
                selected_words = random.choices(self.noun_list, k=num_nouns)

            # Update each label with a selected word
            for i, label in enumerate(self.noun_labels):
                label.config(text=selected_words[i])
        except Exception as e:
            self.log(f"Error updating labels: {e}")

    def refresh_thread(self) -> None:
        """Thread function to update labels every x minutes."""
        thread_id = threading.get_ident()

        while not self.stop_refresh:
            # Sleep in smaller increments to check stop_refresh more frequently
            for _ in range(int(self.refresh_delay * 60)):
                if self.stop_refresh:
                    self.log(f"Thread {thread_id}: Stopping early")
                    return

                time.sleep(1)

            # Use after() to safely update UI from a non-main thread
            if not self.stop_refresh:
                # Pass a flag to indicate this was scheduled from background thread
                self.root.after(0, lambda: self.refresh(from_thread=True))

    def get_default_source(self) -> str:
        default_dir = Path(__file__).parent / "img" / "birds"
        return self.state.source or str(default_dir)

    def select_source(self) -> None:
        # Default to <cwd>/img/birds when no source is set
        try:
            initial_dir = self.get_default_source()
        except Exception:
            # Fallback to root if anything goes wrong resolving default path
            initial_dir = "/"

        directory = filedialog.askdirectory(
            title="Select Source Directory", initialdir=initial_dir
        )

        if directory:
            self.state.source = directory
            self.scan_for_images()
            self.refresh()
            self.save_state()

    def load_state(self) -> None:
        """Load application state from state.json file."""
        self.state_json = {}
        self.state = State()

        try:
            if self.state_file.exists():
                with self.state_file.open("r", encoding="utf-8") as f:
                    self.state_json = json.load(f)

            self.state.source = self.state_json.get("source", "")
            self.state.speed = self.state_json.get("speed", "Normal")
            self.state.nouns = self.state_json.get("nouns", "3")

            if not self.state.source:
                self.state.source = self.get_default_source()
        except Exception as e:
            self.log(f"Error loading state file: {e}")

    def init_source(self) -> None:
        """Initialize the image source from the loaded state."""
        self.load_state()

        if self.state.source:
            self.scan_for_images()

    def save_state(self) -> None:
        """Save application state to state.json file."""
        try:
            state = {
                "source": self.state.source,
                "speed": self.state.speed,
            }

            with self.state_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log(f"Error saving state file: {e}")

    def scan_for_images(self) -> None:
        if not self.state.source:
            return

        self.image_list = []

        for root, _, files in os.walk(self.state.source):
            for file in files:
                if file.lower().endswith(self.supported_formats):
                    self.image_list.append(Path(root) / file)

    def do_refresh(self) -> None:
        self.create_top()
        self.show_random_image()
        self.select_words()

    def refresh(self, from_thread: bool = False) -> None:
        """Update the display with new image and words."""
        self.do_refresh()

        # Only restart the thread if this was triggered manually (not from the background thread)
        # and if we're not in Pause mode
        if not from_thread and (self.state.speed != "Pause"):
            self.restart_refresh_thread()

    def show_random_image(self) -> None:
        if not self.image_list:
            return

        random_image_path = random.choice(self.image_list)
        self.load_image(random_image_path)

    def validate_number(self, p: str) -> bool:
        """Validate input to only allow numbers"""
        if p == "":  # Allow empty field
            return True

        return p.isdigit()

    def update_speed(self) -> None:
        # Set the appropriate delay based on the selected speed
        if self.state.speed == "Pause":
            self.refresh_delay = self.rd_off
        elif self.state.speed == "Fast":
            self.refresh_delay = self.rd_fast
        elif self.state.speed == "Normal":
            self.refresh_delay = self.rd_normal
        elif self.state.speed == "Slow":
            self.refresh_delay = self.rd_slow

    def on_speed_change(self, event: Any = None) -> None:
        """Handle speed change events from the combobox."""
        self.state.speed = self.speed_var.get()
        self.update_speed()

        # Restart thread with new delay
        self.restart_refresh_thread()

        def reset() -> None:
            self.root.focus_set()
            event.widget.configure(style="Normal.TCombobox")
            event.widget.selection_clear()

        self.root.after(100, lambda: reset())
        self.save_state()

    def on_nouns_change(self, event: Any = None) -> None:
        """Handle nouns change events from the combobox."""
        self.state.nouns = self.nouns_var.get()
        self.root.focus_set()
        self.save_state()

    def restart_refresh_thread(self) -> None:
        """Safely stop and restart the refresh thread with the current delay."""
        # Signal the existing thread to stop
        self.stop_refresh = True

        # If a thread exists and is running, wait for it to terminate
        if (
            hasattr(self, "refresh_thd")
            and self.refresh_thd
            and self.refresh_thd.is_alive()
        ):
            self.log(f"Waiting for thread {self.refresh_thd.ident} to terminate...")
            # Wait for the thread to exit
            self.refresh_thd.join(timeout=5.0)

            # If thread is still alive after timeout
            if self.refresh_thd.is_alive():
                self.log(
                    f"Warning: Thread {self.refresh_thd.ident} didn't terminate properly"
                )

                # Don't create a new thread if old one is stuck
                return

        # Reset the flag and start a new thread only if we're not in "Pause" mode
        if self.state.speed != "Pause":
            self.stop_refresh = False
            self.start_refresh_thread()

    def load_image(self, file_path: Path) -> None:
        """Load and display an image with proper resizing after the window is fully rendered."""
        try:
            # Store the file path for later use
            self.pending_image_path = file_path

            # Check if the window is fully rendered
            if (
                self.image_frame.winfo_width() <= 1
                or self.image_frame.winfo_height() <= 1
            ):
                # If not, schedule this to run after the window is updated
                self.root.after(100, lambda: self.load_image(file_path))
                return

            pil_image = Image.open(file_path)
            img_width, img_height = pil_image.size
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()

            # Calculate aspect ratios
            image_aspect = img_width / img_height
            frame_aspect = frame_width / frame_height

            # Determine resizing dimensions based on aspect ratios
            if image_aspect > frame_aspect:
                # Image is wider than the frame, fit to width
                new_width = frame_width
                new_height = int(frame_width / image_aspect)
            else:
                # Image is taller than the frame, fit to height
                new_height = frame_height
                new_width = int(frame_height * image_aspect)

            # Add a margin to ensure bottom controls are visible
            max_height = int(
                frame_height * self.image_padding
            )  # Use only 90% of available height

            if new_height > max_height:
                new_height = max_height
                new_width = int(max_height * image_aspect)

            # Resize the image using LANCZOS for good quality
            resized_image = pil_image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

            # Create a new image with the frame dimensions and paste the resized image in the center
            final_image = Image.new("RGB", (frame_width, frame_height), self.bg_color)

            x_offset = (frame_width - new_width) // 2
            y_offset = (frame_height - new_height) // 2
            final_image.paste(resized_image, (x_offset, y_offset))

            # Convert PIL image to tkinter-compatible photo image
            tk_image = ImageTk.PhotoImage(final_image)

            # Update the image label
            self.image_label.configure(image=tk_image)
            self.current_image = tk_image
        except Exception as e:
            self.log(f"Error loading image: {e}")
