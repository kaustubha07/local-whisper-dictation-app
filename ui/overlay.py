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
        self.streaming_var: Optional[tk.StringVar] = None
        self._dynamic_widgets = []
        self._confirm_guard = False
        
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
        
        self._static_widgets = [self.dot, self.label]
        self.streaming_var = tk.StringVar()
        
        self.root.withdraw() # Start hidden
        self.root.mainloop()

    def _clear_dynamic_widgets(self):
        """Clean up buttons, additional labels and unbind keys."""
        for widget in self._dynamic_widgets:
            try: widget.destroy()
            except: pass
        self._dynamic_widgets = []
        self.root.unbind("<Return>")
        self.root.unbind("<Escape>")
        self._confirm_guard = False

    def _update_ui(self, text, color, show=True):
        if not self.root: return
        
        def update():
            self._clear_dynamic_widgets()
            self.label.config(text=text)
            self.dot.itemconfig(self.dot_id, fill=color)
            
            # Reset window size to default
            self.root.geometry("280x50")
            
            if show:
                self.root.deiconify()
            else:
                self.root.withdraw()
                
        self.root.after(0, update)

    def show_streaming(self, text: str):
        """Update live partial results."""
        if not self.root: return
        self.active = True
        
        def update():
            self._clear_dynamic_widgets()
            self.label.config(text="") # Hide default label text
            self.dot.itemconfig(self.dot_id, fill="blue")
            
            # Resize for text
            width, height = 420, 80
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+{sw - width - 20}+{sh - height - 60}")
            
            self.streaming_var.set(f"🎙 {text}")
            stream_label = tk.Label(
                self.root, 
                textvariable=self.streaming_var, 
                fg="#00d4ff", bg="#1a1a1a", 
                font=("Courier", 10, "bold"),
                wraplength=350, justify=tk.LEFT
            )
            stream_label.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
            self._dynamic_widgets.append(stream_label)
            self.root.deiconify()
            
        self.root.after(0, update)

    def show_pending_confirm(self, text: str, on_confirm, on_cancel):
        """Show final text with Confirm/Cancel actions."""
        if not self.root: return
        self.active = False
        self._confirm_guard = False
        
        def update():
            self._clear_dynamic_widgets()
            self.label.config(text="")
            self.dot.itemconfig(self.dot_id, fill="yellow")
            
            # Resize for content
            width, height = 420, 120
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{width}x{height}+{sw - width - 20}+{sh - height - 60}")
            
            content_frame = tk.Frame(self.root, bg="#1a1a1a")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self._dynamic_widgets.append(content_frame)
            
            txt_label = tk.Label(content_frame, text=text, fg="white", bg="#1a1a1a", 
                                font=("Courier", 10), wraplength=380, justify=tk.LEFT)
            txt_label.pack(fill=tk.X)
            
            btn_frame = tk.Frame(content_frame, bg="#1a1a1a")
            btn_frame.pack(pady=10)
            
            def handle_confirm(e=None):
                if not self._confirm_guard:
                    self._confirm_guard = True
                    on_confirm()
            
            def handle_cancel(e=None):
                if not self._confirm_guard:
                    self._confirm_guard = True
                    on_cancel()

            btn_yes = tk.Button(btn_frame, text="✅ Inject [Enter]", command=handle_confirm,
                               bg="#2D6A4F", fg="white", font=("Arial", 9, "bold"), 
                               padx=10, relief=tk.FLAT)
            btn_yes.pack(side=tk.LEFT, padx=10)
            
            btn_no = tk.Button(btn_frame, text="❌ Cancel [Esc]", command=handle_cancel,
                              bg="#6B2737", fg="white", font=("Arial", 9, "bold"), 
                              padx=10, relief=tk.FLAT)
            btn_no.pack(side=tk.LEFT, padx=10)
            
            self.root.bind("<Return>", handle_confirm)
            self.root.bind("<Escape>", handle_cancel)
            self.root.deiconify()
            self.root.focus_force()

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

    def hide_immediately(self):
        """Withdraw the window instantly — no animation, no delay."""
        if self.root:
            self.root.after(0, self.root.withdraw)
