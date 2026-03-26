import pystray
from PIL import Image, ImageDraw
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from config import Config
from typing import Callable, Optional

class TrayIcon:
    def __init__(self, config: Config, on_toggle: Callable, on_quit: Callable):
        self.config = config
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self.icon: Optional[pystray.Icon] = None
        self.state = "idle"
        
        # Create initial icon
        self.icon = pystray.Icon(
            "Dictation App",
            self._create_image("grey"),
            menu=self._create_menu()
        )

    def _create_image(self, color: str) -> Image.Image:
        """Create a simple colored circle icon."""
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse((8, 8, 56, 56), fill=color)
        return image

    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("✦ Dictation App", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Status: {self.state.capitalize()}", lambda: None, enabled=False),
            pystray.MenuItem(f"Model: {self.config.model_size}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._open_settings),
            pystray.MenuItem("Quit", self.on_quit)
        )

    def set_state(self, state: str):
        self.state = state
        colors = {"idle": "grey", "recording": "red", "processing": "yellow"}
        self.icon.icon = self._create_image(colors.get(state, "grey"))
        self.icon.menu = self._create_menu()

    def _open_settings(self):
        """Open settings window in a new thread to avoid blocking."""
        threading.Thread(target=self._show_settings_window, daemon=True).start()

    def _show_settings_window(self):
        root = tk.Tk()
        root.title("Dictation App Settings")
        root.geometry("400x450")
        root.attributes("-topmost", True)
        
        # Style
        style = ttk.Style()
        style.configure("TLabel", padding=5)
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Model Size
        ttk.Label(main_frame, text="Model Size:").grid(row=0, column=0, sticky=tk.W)
        model_var = tk.StringVar(value=self.config.model_size)
        model_combo = ttk.Combobox(main_frame, textvariable=model_var, values=["tiny", "base", "small", "medium"])
        model_combo.grid(row=0, column=1, sticky=tk.EW)
        
        # Language
        ttk.Label(main_frame, text="Language (en, hi, etc.):").grid(row=1, column=0, sticky=tk.W)
        lang_var = tk.StringVar(value=self.config.language)
        ttk.Entry(main_frame, textvariable=lang_var).grid(row=1, column=1, sticky=tk.EW)
        
        # Hotkey
        ttk.Label(main_frame, text="Hotkey (pynput format):").grid(row=2, column=0, sticky=tk.W)
        hotkey_var = tk.StringVar(value=self.config.hotkey)
        ttk.Entry(main_frame, textvariable=hotkey_var).grid(row=2, column=1, sticky=tk.EW)
        
        # Device
        ttk.Label(main_frame, text="Device:").grid(row=3, column=0, sticky=tk.W)
        device_var = tk.StringVar(value=self.config.device)
        device_combo = ttk.Combobox(main_frame, textvariable=device_var, values=["cpu", "cuda"])
        device_combo.grid(row=3, column=1, sticky=tk.EW)
        
        # Options
        space_var = tk.BooleanVar(value=self.config.prepend_space)
        ttk.Checkbutton(main_frame, text="Prepend space", variable=space_var).grid(row=4, column=0, columnspan=2, sticky=tk.W)
        
        cap_var = tk.BooleanVar(value=self.config.capitalize_first)
        ttk.Checkbutton(main_frame, text="Auto-capitalize first word", variable=cap_var).grid(row=5, column=0, columnspan=2, sticky=tk.W)
        
        def save():
            self.config.model_size = model_var.get()
            self.config.language = lang_var.get()
            self.config.hotkey = hotkey_var.get()
            self.config.device = device_var.get()
            self.config.prepend_space = space_var.get()
            self.config.capitalize_first = cap_var.get()
            self.config.save()
            messagebox.showinfo("Success", "Settings saved. Restart the app for changes to take effect.")
            root.destroy()
            
        ttk.Button(main_frame, text="Save Settings", command=save).grid(row=6, column=0, columnspan=2, pady=20)
        
        root.mainloop()

    def run(self):
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()
