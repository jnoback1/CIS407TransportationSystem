"""Authentication Module - Login Screen"""

import tkinter as tk
from tkinter import messagebox
import config


class LoginWindow:
    """Login window for user authentication"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{config.APP_TITLE} - Login")
        self.success_callback = None
        self.authenticated_user = None
        self._setup_window()
        self._create_ui()
        
    def _setup_window(self):
        """Configure window size and position"""
        self.root.geometry(f"{config.LOGIN_WINDOW_WIDTH}x{config.LOGIN_WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - config.LOGIN_WINDOW_WIDTH) // 2
        y = (screen_height - config.LOGIN_WINDOW_HEIGHT) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.configure(bg=config.BG_WHITE)
        
    def _create_ui(self):
        """Create login form UI elements"""
        # Main container
        main_frame = tk.Frame(self.root, bg=config.BG_WHITE)
        main_frame.pack(expand=True, fill="both", padx=60, pady=60)
        
        # Logo/Icon area
        icon_frame = tk.Frame(main_frame, bg=config.BG_WHITE)
        icon_frame.pack(pady=(10, 30))
        
        icon_label = tk.Label(
            icon_frame, text="🚛",
            font=("Arial", 64),
            bg=config.BG_WHITE
        )
        icon_label.pack()
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="Transportation System",
            font=("Arial", 26, "bold"),
            bg=config.BG_WHITE, 
            fg=config.TEXT_PRIMARY
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame, 
            text="Management Portal",
            font=("Arial", 16),
            bg=config.BG_WHITE, 
            fg=config.TEXT_SECONDARY
        )
        subtitle_label.pack(pady=(0, 50))
        
        # Username field
        username_label = tk.Label(
            main_frame, 
            text="Username",
            font=("Arial", 13, "bold"),
            bg=config.BG_WHITE, 
            fg=config.TEXT_PRIMARY, 
            anchor="w"
        )
        username_label.pack(fill="x", pady=(0, 10))
        
        self.username_entry = tk.Entry(
            main_frame, 
            font=("Arial", 16),
            bg=config.BG_WHITE, 
            fg=config.TEXT_PRIMARY,
            relief="solid", 
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=config.BORDER_COLOR,
            highlightcolor=config.PRIMARY_COLOR
        )
        self.username_entry.pack(fill="x", pady=(0, 25), ipady=15)
        self.username_entry.focus()
        
        # Password field
        password_label = tk.Label(
            main_frame, 
            text="Password",
            font=("Arial", 13, "bold"),
            bg=config.BG_WHITE, 
            fg=config.TEXT_PRIMARY, 
            anchor="w"
        )
        password_label.pack(fill="x", pady=(0, 10))
        
        self.password_entry = tk.Entry(
            main_frame, 
            font=("Arial", 16),
            bg=config.BG_WHITE, 
            fg=config.TEXT_PRIMARY,
            relief="solid", 
            borderwidth=2, 
            show="●",
            highlightthickness=1,
            highlightbackground=config.BORDER_COLOR,
            highlightcolor=config.PRIMARY_COLOR
        )
        self.password_entry.pack(fill="x", pady=(0, 40), ipady=15)
        
        # Login button
        login_button = tk.Button(
            main_frame, 
            text="LOGIN",
            font=("Arial", 16, "bold"),
            bg=config.PRIMARY_COLOR, 
            fg="#000000",
            activebackground=config.PRIMARY_DARK,
            activeforeground="#000000",
            relief="flat", 
            cursor="hand2",
            command=self._handle_login,
            borderwidth=0
        )
        login_button.pack(fill="x", ipady=16)
        
        # Hint text at bottom
        hint_label = tk.Label(
            main_frame, 
            text="Default credentials: admin / password123",
            font=("Arial", 11),
            bg=config.BG_WHITE, 
            fg=config.TEXT_LIGHT
        )
        hint_label.pack(pady=(30, 0))
        
        self.root.bind("<Return>", lambda e: self._handle_login())
        
    def _handle_login(self):
        """Handle login button click"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Login Error", "Please enter both username and password")
            return
        
        if username == config.DEFAULT_USERNAME and password == config.DEFAULT_PASSWORD:
            self.authenticated_user = {
                "username": username,
                "role": "admin",
                "full_name": "Administrator"
            }
            self.root.destroy()
            if self.success_callback:
                self.success_callback(self.authenticated_user)
        else:
            messagebox.showerror("Login Failed", config.MSG_LOGIN_FAILED)
            self.password_entry.delete(0, tk.END)
            self.username_entry.focus()
    
    def set_success_callback(self, callback):
        """Set callback function to execute after successful login"""
        self.success_callback = callback
    
    def show(self):
        """Display login window and start event loop"""
        self.root.mainloop()
