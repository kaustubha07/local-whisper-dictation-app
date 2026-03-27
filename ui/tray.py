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
        vocab_items = []
        
        def make_action(n):
            return lambda icon, item: self._set_vocab_profile(n)
            
        def make_checked(n):
            return lambda item: self.config.active_profile == n

        for name in self.config.vocab_profiles.keys():
            vocab_items.append(
                pystray.MenuItem(
                    name,
                    make_action(name),
                    checked=make_checked(name),
                    radio=True
                )
            )

        return pystray.Menu(
            pystray.MenuItem("✦ Dictation App", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Status: {self.state.capitalize()}", lambda: None, enabled=False),
            pystray.MenuItem(f"Model: {self.config.model_size}", lambda: None, enabled=False),
            pystray.MenuItem(f"Vocab: {self.config.active_profile}", pystray.Menu(*vocab_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._open_settings),
            pystray.MenuItem("View History", self._open_history),
            pystray.MenuItem("Quit", self.on_quit)
        )

    def _set_vocab_profile(self, name: str):
        if self.config.apply_profile(name):
            self.config.save()
            self.set_state(self.state)

    def set_state(self, state: str):
        self.state = state
        colors = {"idle": "grey", "recording": "red", "processing": "yellow"}
        self.icon.icon = self._create_image(colors.get(state, "grey"))
        self.icon.menu = self._create_menu()

    def _open_settings(self):
        """Open settings window in a new thread to avoid blocking."""
        threading.Thread(target=self._show_settings_window, daemon=True).start()

    def _open_history(self):
        """Open history window in a new thread."""
        threading.Thread(target=self._show_history_window, daemon=True).start()

    def _show_history_window(self):
        from engine.history import HistoryLogger
        history = HistoryLogger()
        entries = history.get_recent(50)
        
        # Following the same daemon thread pattern as the settings window
        root = tk.Tk()
        root.title("Transcription History")
        root.geometry("500x400")
        root.attributes("-topmost", True)
        
        text_widget = tk.Text(root, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)

        for entry in entries:
            text_widget.insert(tk.END, entry + "\n")
        text_widget.config(state=tk.DISABLED)

        def copy_last():
            if entries:
                last = entries[0]
                if last.startswith("[") and "]" in last:
                    last = last.split("]", 1)[1].strip()
                root.clipboard_clear()
                root.clipboard_append(last)
                messagebox.showinfo("Copied", "Last transcription copied to clipboard!", parent=root)

        btn_copy = ttk.Button(root, text="Copy Last", command=copy_last)
        btn_copy.pack(pady=10)
        
        root.mainloop()

    def _show_settings_window(self):
        root = tk.Tk()
        root.title("Dictation App Settings")
        root.geometry("450x700")
        root.attributes("-topmost", True)
        
        # Style
        style = ttk.Style()
        style.configure("TLabel", padding=5)
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Settings categories
        ttk.Label(main_frame, text="General Settings", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
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
        ttk.Checkbutton(main_frame, text="Prepend space", variable=space_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        cap_var = tk.BooleanVar(value=self.config.capitalize_first)
        ttk.Checkbutton(main_frame, text="Auto-capitalize first word", variable=cap_var).grid(row=5, column=0, columnspan=2, sticky=tk.W)
        
        # Advanced Settings Header
        ttk.Label(main_frame, text="Advanced Settings", font=("TkDefaultFont", 10, "bold")).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        
        # Model Size
        ttk.Label(main_frame, text="Model Size:").grid(row=7, column=0, sticky=tk.W)
        model_var = tk.StringVar(value=self.config.model_size)
        model_combo = ttk.Combobox(main_frame, textvariable=model_var, values=["tiny", "base", "small", "medium"])
        model_combo.grid(row=7, column=1, sticky=tk.EW)
        
        # Initial Prompt
        ttk.Label(main_frame, text="Initial Prompt:").grid(row=8, column=0, sticky=tk.W)
        prompt_var = tk.StringVar(value=self.config.initial_prompt)
        prompt_entry = ttk.Entry(main_frame, textvariable=prompt_var, width=25)
        prompt_entry.grid(row=8, column=1, sticky=tk.EW)
        
        # Gain Boost
        ttk.Label(main_frame, text="Gain Boost (1.0-3.0):").grid(row=9, column=0, sticky=tk.W)
        gain_var = tk.DoubleVar(value=self.config.gain_boost)
        gain_spin = ttk.Spinbox(main_frame, from_=1.0, to=3.0, increment=0.1, textvariable=gain_var, width=5)
        gain_spin.grid(row=9, column=1, sticky=tk.W)
        
        # Vocabulary Profiles Header
        ttk.Label(main_frame, text="Vocabulary Profiles", font=("TkDefaultFont", 10, "bold")).grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(15, 5))
        
        prof_list_var = tk.StringVar(value=list(self.config.vocab_profiles.keys()))
        prof_list = tk.Listbox(main_frame, listvariable=prof_list_var, height=4)
        prof_list.grid(row=11, column=0, columnspan=2, sticky=tk.EW)
        
        ttk.Label(main_frame, text="Profile Name:").grid(row=12, column=0, sticky=tk.W)
        prof_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=prof_name_var).grid(row=12, column=1, sticky=tk.EW)
        
        ttk.Label(main_frame, text="Prompt:").grid(row=13, column=0, sticky=tk.W)
        prof_prompt_var = tk.StringVar(value=self.config.initial_prompt)
        ttk.Entry(main_frame, textvariable=prof_prompt_var).grid(row=13, column=1, sticky=tk.EW)

        def on_prof_select(event):
            selection = prof_list.curselection()
            if selection:
                name = prof_list.get(selection[0])
                prof_name_var.set(name)
                prof_prompt_var.set(self.config.vocab_profiles.get(name, ""))
        prof_list.bind('<<ListboxSelect>>', on_prof_select)

        def save_profile():
            name = prof_name_var.get().strip()
            prompt = prof_prompt_var.get().strip()
            if name:
                self.config.vocab_profiles[name] = prompt
                self.config.apply_profile(name)
                prof_list_var.set(list(self.config.vocab_profiles.keys()))
                messagebox.showinfo("Success", f"Profile '{name}' saved.", parent=root)
                self.set_state(self.state)

        def delete_profile():
            name = prof_name_var.get().strip()
            if len(self.config.vocab_profiles) <= 1:
                messagebox.showwarning("Warning", "Cannot delete the last profile.", parent=root)
                return
            if name in self.config.vocab_profiles:
                del self.config.vocab_profiles[name]
                if self.config.active_profile == name:
                    self.config.active_profile = list(self.config.vocab_profiles.keys())[0]
                prof_list_var.set(list(self.config.vocab_profiles.keys()))
                self.set_state(self.state)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=14, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save Profile", command=save_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Profile", command=delete_profile).pack(side=tk.LEFT, padx=5)

        def save():
            self.config.model_size = model_var.get()
            self.config.language = lang_var.get()
            self.config.hotkey = hotkey_var.get()
            self.config.device = device_var.get()
            self.config.prepend_space = space_var.get()
            self.config.capitalize_first = cap_var.get()
            # Update currently typing initial prompt without necessarily saving a profile config under it if one wasn't selected
            self.config.initial_prompt = prompt_var.get()
            try:
                self.config.gain_boost = float(gain_var.get())
            except ValueError:
                self.config.gain_boost = 1.0
                
            self.config.save()
            messagebox.showinfo("Success", "Settings saved. Restart the app for changes to take effect.", parent=root)
            self.set_state(self.state)
            root.destroy()
            
        ttk.Button(main_frame, text="Save All Settings", command=save).grid(row=15, column=0, columnspan=2, pady=10)
        
        root.mainloop()

    def run(self):
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()
