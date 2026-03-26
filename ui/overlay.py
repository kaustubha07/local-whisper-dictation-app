import tkinter as tk
from threading import Thread
import logging
from typing import Optional

class StatusOverlay:
    def __init__(self):
        self.root: Optional[tk.Tk] = None
        self.label: Optional[tk.Label] = None
        self.dot: Optional[tk.Canvas] = None
        self.thread: Optional[Thread] = None
        self.active = False
        
        # Start in separate thread
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True) # No title bar
        self.root.attributes("-topmost", True) # Always on top
        self.root.attributes("-alpha", 0.85) # Semi-transparent
        
        # Position at bottom-right
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width, height = 280, 50
        x = screen_width - width - 20
        y = screen_height - height - 60 # Above taskbar
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        self.root.configure(bg="#1a1a1a")
        
        self.dot = tk.Canvas(self.root, width=20, height=20, bg="#1a1a1a", highlightthickness=0)
        self.dot.pack(side=tk.LEFT, padx=10)
        self.dot_id = self.dot.create_oval(2, 2, 18, 18, fill="grey")
        
        self.label = tk.Label(self.root, text="Dictation Ready", fg="white", bg="#1a1a1a", font=("Courier", 10))
        self.label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.root.withdraw() # Start hidden
        self.root.mainloop()

    def _update_ui(self, text, color, show=True):
        if not self.root: return
        
        def update():
            self.label.config(text=text)
            self.dot.itemconfig(self.dot_id, fill=color)
            if show:
                self.root.deiconify()
            else:
                self.root.withdraw()
                
        self.root.after(0, update)

    def show_recording(self):
        self._update_ui("● Recording...", "red")
        self.active = True
        self._pulse()

    def _pulse(self, state=True):
        if not self.active or not self.root: return
        color = "red" if state else "#400000"
        self.root.after(0, lambda: self.dot.itemconfig(self.dot_id, fill=color))
        self.root.after(500, lambda: self._pulse(not state))

    def show_processing(self):
        self.active = False
        self._update_ui("↺ Transcribing...", "yellow")

    def show_success(self, text: str):
        self.active = False
        display_text = text[:25] + "..." if len(text) > 25 else text
        self._update_ui(f"✓ {display_text}", "green")
        self.root.after(2000, self.hide)

    def show_error(self, msg: str):
        self.active = False
        self._update_ui(f"⚠ {msg}", "#ff4444")
        self.root.after(3000, self.hide)

    def hide(self):
        self.active = False
        if self.root:
            self.root.after(0, self.root.withdraw)
