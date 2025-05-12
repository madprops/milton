# Standard
import json
from pathlib import Path

# Libraries
import tkinter as tk

# Modules
from dashboard import Dashboard


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
