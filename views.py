"""View Modules - All Tab Content"""

import tkinter as tk
from tkinter import ttk, messagebox
import config
from ui_components import MetricCard, SectionHeader, NotificationItem


class OverviewView(tk.Frame):
    """Overview Dashboard - First tab"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self._create_ui()
    
    def _create_ui(self):
        """Create overview dashboard UI"""
        canvas = tk.Canvas(self, bg=config.BG_LIGHT, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=config.BG_LIGHT)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = tk.Frame(scrollable_frame, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        self._create_greeting_section(content)
        self._create_metrics_section(content)
        self._create_notifications_section(content)
    
    def _create_greeting_section(self, parent):
        """Create greeting section with user welcome message"""
        greeting_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        greeting_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        welcome_text = f"Welcome back, {self.user_info.get('full_name', 'User')}"
        welcome_label = tk.Label(
            greeting_frame, text=welcome_text,
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY, anchor="w"
        )
        welcome_label.pack(fill="x")
        
        role_text = f"Role: {self.user_info.get('role', 'Unknown').title()}"
        role_label = tk.Label(
            greeting_frame, text=role_text,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_LIGHT, fg=config.TEXT_SECONDARY, anchor="w"
        )
        role_label.pack(fill="x", pady=(5, 0))
    
    def _create_metrics_section(self, parent):
        """Create key metrics dashboard"""
        header = SectionHeader(parent, "Delivery Statistics")
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        metrics_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        metrics_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)
        metrics_frame.columnconfigure(3, weight=1)
        
        self.active_card = MetricCard(metrics_frame, "Active Deliveries", value="—", subtitle="Currently in transit")
        self.active_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.today_card = MetricCard(metrics_frame, "Today's Deliveries", value="—", subtitle="Completed today")
        self.today_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.pending_card = MetricCard(metrics_frame, "Pending Deliveries", value="—", subtitle="Awaiting dispatch")
        self.pending_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.vehicles_card = MetricCard(metrics_frame, "Active Vehicles", value="—", subtitle="Currently on route")
        self.vehicles_card.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    
    def _create_notifications_section(self, parent):
        """Create notifications/alerts section"""
        header = SectionHeader(parent, "Recent Notifications", button_text="View All", button_command=self._view_all_notifications)
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        notifications_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1, height=150)
        notifications_frame.pack(fill="x")
        notifications_frame.pack_propagate(False)
        
        placeholder_label = tk.Label(
            notifications_frame,
            text="No notifications available",
            font=(config.FONT_FAMILY, config.FONT_SIZE_MEDIUM),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY
        )
        placeholder_label.pack(expand=True)
    
    def _view_all_notifications(self):
        """Handle View All button click"""
        messagebox.showinfo("Notifications", "Full notifications view - Backend integration required")


class AnalyticsView(tk.Frame):
    """Analytics Dashboard - Second tab"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_LIGHT)
        self._create_ui()
    
    def _create_ui(self):
        """Create analytics dashboard UI"""
        content = tk.Frame(self, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        title_label = tk.Label(
            content, text="Analytics & Reports",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY, anchor="w"
        )
        title_label.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        placeholder_frame = tk.Frame(content, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        placeholder_frame.pack(fill="both", expand=True)
        
        placeholder_label = tk.Label(
            placeholder_frame, 
            text="Analytics content will be displayed here",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY
        )
        placeholder_label.pack(expand=True)


class ActiveRoutesView(tk.Frame):
    """Active Routes - Third tab"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_LIGHT)
        self._create_ui()
    
    def _create_ui(self):
        """Create active routes UI"""
        content = tk.Frame(self, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        header_frame = tk.Frame(content, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        title_label = tk.Label(
            header_frame, text="Active Delivery Routes",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY, anchor="w"
        )
        title_label.pack(side="left")
        
        refresh_button = tk.Button(
            header_frame, text="🔄 Refresh",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.PRIMARY_COLOR, fg="#000000",
            activebackground=config.PRIMARY_DARK,
            activeforeground="#000000",
            relief="flat", cursor="hand2",
            padx=config.PADDING_LARGE, pady=config.PADDING_SMALL,
            command=self._refresh_routes
        )
        refresh_button.pack(side="right")
        
        list_frame = tk.Frame(content, bg=config.BG_LIGHT)
        list_frame.pack(fill="both", expand=True)
        
        placeholder_frame = tk.Frame(list_frame, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        placeholder_frame.pack(fill="both", expand=True)
        
        placeholder_label = tk.Label(
            placeholder_frame, 
            text="Active routes will be displayed here",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY
        )
        placeholder_label.pack(expand=True)
    
    def _refresh_routes(self):
        """Refresh active routes data"""
        messagebox.showinfo("Refresh", "Routes refreshed")


class NewRoutesView(tk.Frame):
    """New Routes - Fourth tab"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_LIGHT)
        self._create_ui()
    
    def _create_ui(self):
        """Create new route planning UI"""
        canvas = tk.Canvas(self, bg=config.BG_LIGHT, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=config.BG_LIGHT)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = tk.Frame(scrollable_frame, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        title_label = tk.Label(
            content, text="Create New Delivery Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY, anchor="w"
        )
        title_label.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        form_frame = tk.Frame(content, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        form_frame.pack(fill="both", expand=True)
        
        placeholder_label = tk.Label(
            form_frame, 
            text="Route planning form will be displayed here",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY
        )
        placeholder_label.pack(expand=True)


class MapVisualizerView(tk.Frame):
    """Map Visualizer - Fifth tab"""
    
    def __init__(self, parent):
        super().__init__(parent, bg=config.BG_LIGHT)
        self._create_ui()
    
    def _create_ui(self):
        """Create map visualization UI"""
        content = tk.Frame(self, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        header_frame = tk.Frame(content, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        title_label = tk.Label(
            header_frame, text="Route Map Visualizer",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, fg=config.TEXT_PRIMARY
        )
        title_label.pack(side="left")
        
        controls_frame = tk.Frame(header_frame, bg=config.BG_LIGHT)
        controls_frame.pack(side="right")
        
        tk.Checkbutton(controls_frame, text="Show Stores", font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL), bg=config.BG_LIGHT).pack(side="left", padx=5)
        tk.Checkbutton(controls_frame, text="Show Vehicles", font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL), bg=config.BG_LIGHT).pack(side="left", padx=5)
        tk.Checkbutton(controls_frame, text="Show Routes", font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL), bg=config.BG_LIGHT).pack(side="left", padx=5)
        
        map_frame = tk.Frame(content, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        map_frame.pack(fill="both", expand=True)
        
        placeholder_label = tk.Label(
            map_frame, 
            text="Map visualization will be displayed here",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
            bg=config.BG_WHITE, fg=config.TEXT_SECONDARY
        )
        placeholder_label.pack(expand=True)


VIEW_CLASSES = {
    "Overview": OverviewView,
    "Analytics": AnalyticsView,
    "Active Routes": ActiveRoutesView,
    "New Routes": NewRoutesView,
    "Map Visualizer": MapVisualizerView
}
