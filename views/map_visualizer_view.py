"""
Map Visualizer View - Interactive route and delivery mapping
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from ui_components import MetricCard, SectionHeader
from backend.repository import AzureSqlRepository
from datetime import datetime


class MapVisualizerView(tk.Frame):
    """Map Visualizer - Fifth tab"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
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