"""Main Application Controller"""

import tkinter as tk
from tkinter import messagebox
import config
from auth import LoginWindow
from ui_components import NavigationSidebar, StatusIndicator
from views import VIEW_CLASSES
from backend.db_connector import connect_with_token


class TransportationApp:
    def __init__(self, user_info):
        self.user_info = user_info
        self.root = tk.Tk()
        self.current_view = None
        self.content_frame = None
        self._setup_window()
        self._create_layout()
        self._check_database_connection()
    
    def _setup_window(self):
        self.root.title(config.APP_TITLE)
        self.root.geometry(f"{config.MAIN_WINDOW_WIDTH}x{config.MAIN_WINDOW_HEIGHT}")
        self.root.minsize(config.MAIN_WINDOW_MIN_WIDTH, config.MAIN_WINDOW_MIN_HEIGHT)
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - config.MAIN_WINDOW_WIDTH) // 2
        y = (screen_height - config.MAIN_WINDOW_HEIGHT) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.configure(bg=config.BG_LIGHT)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_layout(self):
        main_container = tk.Frame(self.root, bg=config.BG_LIGHT)
        main_container.pack(fill="both", expand=True)
        self.sidebar = NavigationSidebar(main_container, on_tab_change=self._switch_view)
        self.sidebar.pack(side="left", fill="y")
        right_container = tk.Frame(main_container, bg=config.BG_LIGHT)
        right_container.pack(side="left", fill="both", expand=True)
        self._create_header(right_container)
        self.content_frame = tk.Frame(right_container, bg=config.BG_LIGHT)
        self.content_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Load Overview tab after window is fully rendered
        self.root.after(100, lambda: self._switch_view("Overview"))
    
    def _create_header(self, parent):
        header = tk.Frame(parent, bg=config.BG_WHITE, height=60, relief="solid", borderwidth=1)
        header.pack(fill="x")
        header.pack_propagate(False)
        left_frame = tk.Frame(header, bg=config.BG_WHITE)
        left_frame.pack(side="left", padx=config.PADDING_LARGE, pady=config.PADDING_MEDIUM)
        self.status_indicator = StatusIndicator(left_frame)
        self.status_indicator.pack()
        right_frame = tk.Frame(header, bg=config.BG_WHITE)
        right_frame.pack(side="right", padx=config.PADDING_LARGE, pady=config.PADDING_MEDIUM)
        user_name = self.user_info.get('full_name', 'User')
        user_label = tk.Label(right_frame, text=f"{user_name}", font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL), bg=config.BG_WHITE, fg=config.TEXT_PRIMARY)
        user_label.pack(side="left", padx=(0, 15))
        logout_button = tk.Button(right_frame, text="Logout", font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"), bg=config.BUTTON_BG, fg=config.BUTTON_TEXT, activebackground=config.BUTTON_HOVER, activeforeground=config.BUTTON_TEXT, relief="flat", cursor="hand2", padx=config.PADDING_MEDIUM, pady=config.PADDING_SMALL, command=self._logout)
        logout_button.pack(side="left")
    
    def _switch_view(self, tab_name):
        if self.current_view:
            self.current_view.destroy()
        view_class = VIEW_CLASSES.get(tab_name)
        if not view_class:
            messagebox.showerror("Error", f"View not found for tab: {tab_name}")
            return
        
        # Always pass user_info to all views
        self.current_view = view_class(self.content_frame, self.user_info)
        self.current_view.pack(fill="both", expand=True)
    
    def _check_database_connection(self):
        try:
            conn = connect_with_token()
            if conn:
                self.status_indicator.set_connected()
                conn.close()
            else:
                self.status_indicator.set_disconnected()
        except Exception as e:
            self.status_indicator.set_error(f"Connection error: {str(e)[:30]}")
    
    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            start_application()
    
    def _on_close(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()


def start_application():
    def on_login_success(user_info):
        app = TransportationApp(user_info)
        app.run()
    login = LoginWindow()
    login.set_success_callback(on_login_success)
    login.show()


if __name__ == "__main__":
    start_application()