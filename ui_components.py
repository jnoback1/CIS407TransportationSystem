"""Reusable UI Components"""

import tkinter as tk
from tkinter import ttk
import config


class NavigationSidebar(tk.Frame):
    """Left sidebar navigation with tab buttons"""
    
    def __init__(self, parent, on_tab_change=None):
        super().__init__(parent, bg=config.BG_DARK)
        self.on_tab_change = on_tab_change
        self.active_tab = None
        self.tab_buttons = {}
        self._create_header()
        self._create_tab_buttons()
        if config.TABS:
            self.select_tab(config.TABS[0])
    
    def _create_header(self):
        """Create sidebar header with app title"""
        header_frame = tk.Frame(self, bg=config.BG_DARK, height=80)
        header_frame.pack(fill="x", padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, text=config.APP_TITLE,
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
            bg=config.BG_DARK, fg=config.TEXT_WHITE,
            wraplength=config.SIDEBAR_WIDTH - 40, justify="left"
        )
        title_label.pack(anchor="w")
        
        version_label = tk.Label(
            header_frame, text=f"v{config.APP_VERSION}",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_DARK, fg=config.TEXT_LIGHT
        )
        version_label.pack(anchor="w")
    
    def _create_tab_buttons(self):
        """Create navigation buttons for each tab"""
        for tab_name in config.TABS:
            button = tk.Button(
                self, text=tab_name,
                font=(config.FONT_FAMILY, config.FONT_SIZE_MEDIUM, "bold"),
                bg=config.BG_DARK, fg="#000000",
                activebackground=config.BG_MEDIUM,
                activeforeground="#000000",
                relief="flat", cursor="hand2", anchor="w",
                padx=config.PADDING_LARGE, pady=config.PADDING_MEDIUM,
                command=lambda t=tab_name: self.select_tab(t)
            )
            button.pack(fill="x", padx=config.PADDING_MEDIUM, pady=2)
            self.tab_buttons[tab_name] = button
    
    def select_tab(self, tab_name):
        """Select a tab and update button states"""
        self.active_tab = tab_name
        for name, button in self.tab_buttons.items():
            if name == tab_name:
                button.configure(bg=config.PRIMARY_COLOR, fg="#000000")
            else:
                button.configure(bg=config.BG_DARK, fg="#000000")
        if self.on_tab_change:
            self.on_tab_change(tab_name)


class StatusIndicator(tk.Frame):
    """Connection status indicator"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_WHITE)
        self.status_label = None
        self.status_dot = None
        self._create_ui()
    
    def _create_ui(self):
        """Create status indicator UI"""
        self.status_dot = tk.Canvas(
            self, width=12, height=12,
            bg=config.BG_WHITE, highlightthickness=0
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        
        self.status_label = tk.Label(
            self, text="Checking connection...",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY
        )
        self.status_label.pack(side="left")
        self._draw_dot(config.TEXT_LIGHT)
    
    def _draw_dot(self, color):
        """Draw status dot with given color"""
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline="")
    
    def set_connected(self):
        """Set status to connected"""
        self._draw_dot(config.SUCCESS_COLOR)
        self.status_label.configure(text=config.MSG_DB_CONNECTED, fg=config.SUCCESS_COLOR)
    
    def set_disconnected(self):
        """Set status to disconnected"""
        self._draw_dot(config.ERROR_COLOR)
        self.status_label.configure(text=config.MSG_DB_DISCONNECTED, fg=config.ERROR_COLOR)
    
    def set_error(self, message=None):
        """Set status to error"""
        self._draw_dot(config.ERROR_COLOR)
        text = message if message else config.MSG_DB_ERROR
        self.status_label.configure(text=text, fg=config.ERROR_COLOR)


class MetricCard(tk.Frame):
    """Card displaying a metric value with label"""
    
    def __init__(self, parent, title, value="—", subtitle=""):
        super().__init__(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        self.configure(highlightbackground=config.BORDER_COLOR, highlightthickness=1)
        
        inner_frame = tk.Frame(self, bg=config.BG_WHITE)
        inner_frame.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        title_label = tk.Label(
            inner_frame, text=title,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY, anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 5))
        
        self.value_label = tk.Label(
            inner_frame, text=value,
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_WHITE, fg=config.TEXT_PRIMARY, anchor="w"
        )
        self.value_label.pack(fill="x", pady=(0, 5))
        
        if subtitle:
            subtitle_label = tk.Label(
                inner_frame, text=subtitle,
                font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
                bg=config.BG_WHITE, fg=config.TEXT_LIGHT, anchor="w"
            )
            subtitle_label.pack(fill="x")
    
    def update_value(self, value):
        """Update the metric value"""
        self.value_label.configure(text=value)
    
    def update_value(self, new_value):
        """Update the displayed value"""
        self.value_label.config(text=new_value)


class SectionHeader(tk.Frame):
    """Section header with title and optional action button"""
    
    def __init__(self, parent, title, button_text=None, button_command=None):
        super().__init__(parent, bg=config.BG_LIGHT)
        
        title_label = tk.Label(
            self, text=title,
            font=(config.FONT_FAMILY, config.FONT_SIZE_TITLE, "bold"),
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY, anchor="w"
        )
        title_label.pack(side="left")
        
        if button_text and button_command:
            action_button = tk.Button(
                self, text=button_text,
                font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
                bg=config.PRIMARY_COLOR, fg="#000000",
                activebackground=config.PRIMARY_DARK,
                activeforeground="#000000",
                relief="flat", cursor="hand2",
                padx=config.PADDING_LARGE, pady=config.PADDING_SMALL,
                command=button_command
            )
            action_button.pack(side="right")


class NotificationItem(tk.Frame):
    """Notification list item"""
    
    def __init__(self, parent, message, timestamp, severity="info"):
        super().__init__(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        self.configure(highlightbackground=config.BORDER_COLOR, highlightthickness=1)
        
        color_map = {
            "info": config.INFO_COLOR,
            "warning": config.WARNING_COLOR,
            "error": config.ERROR_COLOR,
            "success": config.SUCCESS_COLOR
        }
        severity_color = color_map.get(severity, config.INFO_COLOR)
        
        stripe = tk.Frame(self, bg=severity_color, width=4)
        stripe.pack(side="left", fill="y")
        
        content_frame = tk.Frame(self, bg=config.BG_WHITE)
        content_frame.pack(side="left", fill="both", expand=True, padx=config.PADDING_MEDIUM, pady=config.PADDING_MEDIUM)
        
        message_label = tk.Label(
            content_frame, text=message,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE, fg=config.TEXT_PRIMARY,
            anchor="w", justify="left"
        )
        message_label.pack(fill="x")
        
        timestamp_label = tk.Label(
            content_frame, text=timestamp,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE, fg=config.TEXT_LIGHT, anchor="w"
        )
        timestamp_label.pack(fill="x")
