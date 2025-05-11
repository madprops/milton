import os
import time
import random
import threading
import json
import tkinter as tk
from typing import Any
from pathlib import Path
from PIL import Image, ImageTk  # type: ignore
from tkinter import ttk, filedialog


class State:
    source: str = ""
    speed: str = "Normal"


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
        self.wid_pad_x = 5
        self.wid_pad_y = 3
        self.pady_1 = 10
        self.padx_1 = 5
        self.img_width = 300
        self.img_height = 200
        self.stop_refresh = False
        self.state_file = Path("state.json")

        self.root = root
        self.root.configure(bg=self.bg_color)
        self.root.title("Milton")
        self.root.geometry("600x400")
        self.root.configure(bg="grey")

        self.load_state()
        self.create_main()
        self.create_top()
        self.create_image()
        self.create_bottom()

        self.noun_list = self.read_noun_list()

        self.current_image = None
        self.image_list: list[Path] = []
        self.supported_formats = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff")

        self.init_source()
        self.start()

    def start(self) -> None:
        self.scan_for_images()
        self.root.after(100, self.refresh)
        self.start_refresh_thread()

    def start_refresh_thread(self) -> None:
        self.refresh_thd = threading.Thread(target=self.refresh_thread, daemon=True)
        self.refresh_thd.start()

    def create_main(self) -> None:
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)

        self.top_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.top_frame.pack(fill="x", pady=self.pady_1)  # Increased padding

        self.middle_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.middle_frame.pack(fill="both", expand=True)

        self.bottom_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.bottom_frame.pack(fill="x", pady=1)

        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.pack_propagate(False)

    def create_top(self) -> None:
        labels = tk.Frame(self.top_frame, bg=self.bg_color, pady=3)
        labels.pack(expand=True)

        self.label_1 = tk.Label(
            labels,
            text="---",
            font=("Arial", self.font_size),
            height=self.button_height,
            padx=self.wid_pad_x,
            pady=self.wid_pad_y,
        )

        self.label_2 = tk.Label(
            labels,
            text="---",
            font=("Arial", self.font_size),
            height=self.button_height,
            padx=self.wid_pad_x,
            pady=self.wid_pad_y,
        )

        self.label_3 = tk.Label(
            labels,
            text="---",
            font=("Arial", self.font_size),
            height=self.button_height,
            padx=self.wid_pad_x,
            pady=self.wid_pad_y,
        )

        self.label_1.pack(side=tk.LEFT, padx=self.padx_1)
        self.label_2.pack(side=tk.LEFT, padx=self.padx_1)
        self.label_3.pack(side=tk.LEFT, padx=self.padx_1)

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
        combo_style = ttk.Style()

        combo_style.configure(
            "Custom.TCombobox",
            selectbackground=combo_style.lookup("TCombobox", "fieldbackground"),
            selectforeground=combo_style.lookup("TCombobox", "foreground"),
            padding=(5, self.button_height * 5),
        )

        self.select_source_btn = tk.Button(
            self.bottom_frame,
            text="Source",
            command=self.select_source,
            height=self.button_height,
            font=("Arial", self.font_size_2),
            bd=0,
        )

        self.refresh_button = tk.Button(
            self.bottom_frame,
            text="Refresh >",
            command=self.refresh,
            height=self.button_height,
            font=("Arial", self.font_size_2),
            bd=0,
        )

        self.close_button = tk.Button(
            self.bottom_frame,
            text="Close",
            command=self.close,
            height=self.button_height,
            font=("Arial", self.font_size_2),
            bd=0,
        )

        self.speed_var = tk.StringVar(value="normal")

        self.speed_combo = ttk.Combobox(
            self.bottom_frame,
            width=8,
            values=["Off", "Fast", "Normal", "Slow"],
            textvariable=self.speed_var,
            font=("Arial", self.font_size_2),
            style="Custom.TCombobox",
            state="readonly",
        )

        self.speed_combo.set(self.state.speed)
        self.speed_combo.bind("<<ComboboxSelected>>", self.on_speed_change)

        self.select_source_btn = tk.Button(
            self.bottom_frame,
            text="Source",
            command=self.select_source,
            height=self.button_height,
            font=("Arial", self.font_size_2),
            bd=0,
        )

        self.refresh_button = tk.Button(
            self.bottom_frame,
            text="Refresh",
            command=self.refresh,
            height=self.button_height,
            font=("Arial", self.font_size_2),
            bd=0,
        )

        self.close_button = tk.Button(
            self.bottom_frame,
            text="Close",
            command=self.close,
            height=self.button_height,
            font=("Arial", self.font_size_2),
            bd=0,
        )

        self.select_source_btn.pack(side=tk.LEFT, padx=self.padx_1, pady=self.pady_1)
        self.speed_combo.pack(side=tk.LEFT, padx=self.padx_1, pady=self.pady_1)
        self.refresh_button.pack(side=tk.LEFT, padx=self.padx_1, pady=self.pady_1)
        self.close_button.pack(side=tk.RIGHT, padx=(5, 10), pady=self.pady_1)

        self.select_source_btn.pack(side=tk.LEFT, padx=(10, 5), pady=self.pady_1)
        self.refresh_button.pack(side=tk.LEFT, padx=self.padx_1, pady=self.pady_1)
        self.close_button.pack(side=tk.RIGHT, padx=(5, 10), pady=self.pady_1)

    def close(self) -> None:
        """Close the application."""
        self.root.quit()

    def log(self, message: str) -> None:
        """Log messages to the console."""
        print(message)  # noqa

    def read_noun_list(self) -> list[str]:
        """Read the noun list from file."""
        try:
            with Path("nouns.txt").open("r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            self.log(f"Error reading nouns.txt: {e}")
            return ["Error", "Loading", "Words"]

    def select_words(self) -> None:
        """Update all three labels with random words."""
        try:
            if len(self.noun_list) >= 3:
                selected_words = random.sample(self.noun_list, 3)
            else:
                selected_words = random.choices(self.noun_list, k=3)

            self.label_1.config(text=selected_words[0])
            self.label_2.config(text=selected_words[1])
            self.label_3.config(text=selected_words[2])
        except Exception as e:
            self.log(f"Error updating labels: {e}")

    def refresh_thread(self) -> None:
        """Thread function to update labels every x minutes."""
        while not self.stop_refresh:
            time.sleep(self.refresh_delay * 60)
            # Use after() to safely update UI from a non-main thread
            if not self.stop_refresh:  # Check again after the sleep
                self.root.after(0, self.refresh)

    def select_source(self) -> None:
        directory = filedialog.askdirectory(title="Select Source Directory")

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
        except Exception as e:
            self.log(f"Error loading state file: {e}")

    def init_source(self) -> None:
        """Initialize the image source from the loaded state."""
        self.load_state()

        if self.state.source:
            self.scan_for_images()
            self.refresh()

    def save_state(self) -> None:
        """Save application state to state.json file."""
        try:
            state = {"source": self.state.source}

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

    def refresh(self) -> None:
        self.show_random_image()
        self.select_words()

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

    def on_speed_change(self, event: Any = None) -> None:
        self.state.speed = self.speed_var.get()

        if self.state.speed == "Off":
            self.refresh_delay = self.rd_off
        elif self.state.speed == "Fast":
            self.refresh_delay = self.rd_fast
        elif self.state.speed == "Normal":
            self.refresh_delay = self.rd_normal
        elif self.state.speed == "Slow":
            self.refresh_delay = self.rd_slow

        self.restart_refresh_thread()
        self.root.focus_set()
        self.save_state()

    def restart_refresh_thread(self) -> None:
        """Restart the refresh thread with the current delay."""
        if self.refresh_thd and self.refresh_thd.is_alive():
            self.stop_refresh = True

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
            max_height = int(frame_height * 0.9)  # Use only 90% of available height
            if new_height > max_height:
                new_height = max_height
                new_width = int(max_height * image_aspect)

            # Resize the image using LANCZOS for good quality
            resized_image = pil_image.resize((new_width, new_height), Image.LANCZOS)

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


def main() -> None:
    manifest_path = Path("manifest.json")

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as f:
            f_manifest = f.read()
            manifest = json.loads(f_manifest)
            root = tk.Tk(className=manifest["program"])
            app = Dashboard(root)
            root.configure(bg=app.bg_color)
            root.mainloop()


if __name__ == "__main__":
    main()
