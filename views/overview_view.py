"""
Overview View - Dashboard home screen with key metrics and notifications
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from ui_components import MetricCard, SectionHeader, NotificationItem
from backend.repository import AzureSqlRepository
from datetime import datetime


# IMPORTANT TO DO:
# --CREATE STATUS TABLE AND POPULATE
# --UPDATE STATUS INDICATOR IN MAIN.PY BASED ON DB CONNECTION STATUS
# UPDATE OVERVIEW WITH NEW STATUS TABLE DATA ONCE COMPLETED

class OverviewView(tk.Frame):
    """Overview Dashboard - First tab"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.notifications_cache = []  # Cache for instant "View All"
        self.cache_timestamp = None
        self._create_ui()
        self.after(100, self._load_data)
    
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
        """Create notifications section with View All button"""
        header = SectionHeader(parent, "Recent Notifications",
                            button_text="View All",
                            button_command=self.on_view_all_notifications)
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
    
        # Notification container
        notifications_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1, height=150)
        notifications_frame.pack(fill="x")
        notifications_frame.pack_propagate(False)
    
        # Listbox for notifications
        self.notification_list = tk.Listbox(
            notifications_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY,
            activestyle="none",
            highlightthickness=0,
            borderwidth=0
        )
        self.notification_list.pack(fill="both", expand=True, padx=10, pady=10)
        
    def _load_data(self):
        """Load data from repository and update UI"""
        try:
            # Create repository once and keep it alive
            if not self.repo:
                self.repo = AzureSqlRepository()

            # Active deliveries → Status is 'In Transit'
            active = self.repo.fetch_all(
                "SELECT COUNT(*) AS Total FROM DeliveryLog WHERE Status = 'In Transit'"
            )
            self.active_card.update_value(str(active[0]['Total']) if active else "0")

            # Today's deliveries → Status is 'Delivered' and Date is Today
            today = self.repo.fetch_all(
                """
                SELECT COUNT(*) AS Total
                FROM DeliveryLog
                WHERE Status = 'Delivered'
                AND CAST(Order_Date AS DATE) = CAST(GETDATE() AS DATE)
                """
            )
            self.today_card.update_value(str(today[0]['Total']) if today else "0")

            # Pending deliveries → Status is 'Pending' or 'Ordered'
            pending = self.repo.fetch_all(
                "SELECT COUNT(*) AS Total FROM DeliveryLog WHERE Status IN ('Pending', 'Ordered')"
            )
            self.pending_card.update_value(str(pending[0]['Total']) if pending else "0")

            # Active vehicles → vehicles currently on delivery (Status is 'In Transit')
            vehicles = self.repo.fetch_all(
                "SELECT COUNT(DISTINCT VehicleID) AS Total FROM DeliveryLog WHERE Status = 'In Transit'"
            )
            self.vehicles_card.update_value(str(vehicles[0]['Total']) if vehicles else "0")
            
            # Fetch and cache ALL notifications once
            self.notifications_cache = self.repo.fetch_all("""
                SELECT TOP 500
                    Order_ID,
                    Order_Date,
                    Delivery_Time,
                    'Delivery completed for order ' + CAST(Order_ID AS NVARCHAR(50)) AS Message
                FROM dbo.DeliveryLog
                WHERE Status = 'Delivered'
                ORDER BY Order_Date DESC
            """)
            
            self.cache_timestamp = datetime.now()

            # Show recent 5 notifications in list
            recent_notifications = self.notifications_cache[:5] if self.notifications_cache else []
            messages = [n['Message'] for n in recent_notifications] if recent_notifications else ["No recent deliveries found"]

            self.notification_list.delete(0, 'end')
            for msg in messages:
                self.notification_list.insert('end', msg)

            logging.info("Overview data loaded successfully")

        except Exception as e:
            logging.error(f"Error loading overview data: {e}")
            # Show error in cards
            self.active_card.update_value("Error")
            self.today_card.update_value("Error")
            self.pending_card.update_value("Error")
            self.vehicles_card.update_value("Error")
            # Show error in notifications
            self.notification_list.delete(0, 'end')
            self.notification_list.insert('end', f"Error loading notifications: {str(e)}")
        
        # Keep repository connection alive - don't close it
        # It will be closed in destroy() method
            
    def on_view_all_notifications(self):
        """Open a new window showing all notifications - INSTANT using cache"""
        
        # Use cached data - no database query needed!
        if self.notifications_cache:
            self._show_notifications_window(self.notifications_cache)
        else:
            messagebox.showinfo(
                "No Notifications",
                "No notifications have been loaded yet.\n\nPlease wait for the overview data to load."
            )
            
    def _show_notifications_window(self, notifications):
        """Display all notifications in a popup window (batched to avoid UI freezing)"""
        win = tk.Toplevel(self)
        win.title("All Notifications")
        win.geometry("700x500")
        win.configure(bg=config.BG_LIGHT)
    
        # Header
        header = tk.Frame(win, bg=config.BG_WHITE, height=70, relief="solid", borderwidth=1)
        header.pack(fill="x")
        header.pack_propagate(False)
    
        title = tk.Label(
            header,
            text=f"📬 All Notifications ({len(notifications)})",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        )
        title.pack(side="left", padx=config.PADDING_LARGE, pady=15)
    
        # Cache age indicator
        if self.cache_timestamp:
            age_seconds = (datetime.now() - self.cache_timestamp).seconds
            age_text = f"Updated {age_seconds}s ago" if age_seconds < 60 else f"Updated {age_seconds // 60}m ago"
            tk.Label(
                header,
                text=age_text,
                font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
                bg=config.BG_WHITE,
                fg=config.TEXT_SECONDARY
            ).pack(side="left", padx=5)
    
        # Scrollable content (created early so render_batch can reference it)
        canvas = tk.Canvas(win, bg=config.BG_LIGHT, highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=config.BG_LIGHT)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_MEDIUM)
        scrollbar.pack(side="right", fill="y", pady=config.PADDING_MEDIUM)

        # Initialize batching variables for incremental rendering
        index = 0
        batch_size = 50

        def render_batch():
            nonlocal index
            end = min(index + batch_size, len(notifications))
            for note in notifications[index:end]:
                card = tk.Frame(scroll_frame, bg=config.BG_WHITE, relief="solid", borderwidth=1)
                card.pack(fill="x", pady=config.PADDING_SMALL)

                tk.Label(
                    card,
                    text=note['Message'],
                    font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
                    bg=config.BG_WHITE,
                    fg=config.TEXT_PRIMARY,
                    anchor="w",
                    justify="left"
                ).pack(fill="x", padx=config.PADDING_MEDIUM, pady=(config.PADDING_SMALL, 2))

                time_text = f"📅 {note['Order_Date']} | ⏰ Delivery Time: {note['Delivery_Time']} min"
                tk.Label(
                    card,
                    text=time_text,
                    font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
                    bg=config.BG_WHITE,
                    fg=config.TEXT_SECONDARY,
                    anchor="w"
                ).pack(fill="x", padx=config.PADDING_MEDIUM, pady=(2, config.PADDING_SMALL))

            index = end
            if index < len(notifications):
                # Schedule next batch to render
                win.after(10, render_batch)

        # If there are notifications, render them in batches; otherwise show empty message
        if notifications:
            render_batch()
        else:
            empty_label = tk.Label(
                scroll_frame,
                text="No notifications to display",
                font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
                bg=config.BG_LIGHT,
                fg=config.TEXT_SECONDARY
            )
            empty_label.pack(expand=True, pady=50)
        
        # Refresh button
        def refresh_and_reopen():
            win.destroy()
            self._load_data()  # Reload cache from database
            self.after(500, self.on_view_all_notifications)  # Reopen window
        
        refresh_btn = tk.Button(
            header,
            text="🔄 Refresh",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=refresh_and_reopen
        )
        refresh_btn.pack(side="right", padx=config.PADDING_MEDIUM)
        
        # Close button
        close_btn = tk.Button(
            header,
            text="✕ Close",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#E74C3C",
            fg=config.BG_WHITE,
            activebackground="#C0392B",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=win.destroy
        )
        close_btn.pack(side="right", padx=5)
            
    def destroy(self):
        """Clean up resources when view is destroyed"""
        # Close repository connection when view is destroyed
        if self.repo:
            try:
                self.repo.close()
                logging.info("Repository connection closed")
            except Exception as e:
                logging.error(f"Error closing repository: {e}")
        super().destroy()