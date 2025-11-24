"""
Active Routes View - Real-time delivery tracking and management
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

class ActiveRoutesView(tk.Frame):
    """Active Routes - Real-time delivery tracking and management"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.selected_route = None
        self.auto_refresh = True
        self.refresh_interval = 30000  # 30 seconds
        self._create_ui()
        self.after(100, self._load_active_routes)
    
    def _create_ui(self):
        """Create active routes UI with real-time tracking"""
        # Main container
        main_container = tk.Frame(self, bg=config.BG_LIGHT)
        main_container.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        # Header section
        self._create_header(main_container)
        
        # Summary metrics
        self._create_summary_metrics(main_container)
        
        # Main content area (split view)
        content_container = tk.Frame(main_container, bg=config.BG_LIGHT)
        content_container.pack(fill="both", expand=True, pady=(config.PADDING_MEDIUM, 0))
        
        # Left panel: Routes list
        self._create_routes_list_panel(content_container)
        
        # Right panel: Route details
        self._create_route_details_panel(content_container)
    
    def _create_header(self, parent):
        """Create header with title and controls"""
        header_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Active Delivery Routes",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, 
            fg=config.TEXT_PRIMARY, 
            anchor="w"
        )
        title_label.pack(side="left")
        
        # Last updated
        self.last_updated_label = tk.Label(
            header_frame,
            text="Last updated: Never",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_SECONDARY
        )
        self.last_updated_label.pack(side="left", padx=(20, 0))
        
        # Control buttons
        controls_frame = tk.Frame(header_frame, bg=config.BG_LIGHT)
        controls_frame.pack(side="right")
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_cb = tk.Checkbutton(
            controls_frame,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            command=self._toggle_auto_refresh
        )
        auto_refresh_cb.pack(side="left", padx=10)
        
        # Refresh button
        refresh_button = tk.Button(
            controls_frame, 
            text="Refresh Now",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BUTTON_BG, 
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            activeforeground=config.BUTTON_TEXT,
            relief="flat", 
            cursor="hand2",
            padx=15, 
            pady=5,
            command=self._load_active_routes
        )
        refresh_button.pack(side="left", padx=5)
    
    def _create_summary_metrics(self, parent):
        """Create summary metrics cards"""
        metrics_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        metrics_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)
        
        self.total_active_card = MetricCard(
            metrics_frame, 
            "Active Routes", 
            value="—", 
            subtitle="Currently in transit"
        )
        self.total_active_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.on_time_card = MetricCard(
            metrics_frame, 
            "On-Time Routes", 
            value="—", 
            subtitle="Meeting schedule"
        )
        self.on_time_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.delayed_card = MetricCard(
            metrics_frame, 
            "Delayed Routes", 
            value="—", 
            subtitle="Behind schedule"
        )
        self.delayed_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.avg_progress_card = MetricCard(
            metrics_frame, 
            "Avg Progress", 
            value="—", 
            subtitle="% Complete"
        )
        self.avg_progress_card.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    
    def _create_routes_list_panel(self, parent):
        """Create left panel with routes list"""
        left_panel = tk.Frame(parent, bg=config.BG_LIGHT)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, config.PADDING_SMALL))
        
        # Panel header
        list_header = tk.Frame(left_panel, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        list_header.pack(fill="x")
        
        tk.Label(
            list_header,
            text="Active Routes List",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left", padx=15, pady=10)
        
        # Filter controls
        filter_frame = tk.Frame(list_header, bg=config.BG_WHITE)
        filter_frame.pack(side="right", padx=15)
        
        tk.Label(
            filter_frame,
            text="Filter:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        self.route_filter = ttk.Combobox(
            filter_frame,
            values=["All Routes", "On Time", "Delayed", "Critical"],
            state="readonly",
            width=12,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL)
        )
        self.route_filter.set("All Routes")
        self.route_filter.pack(side="left")
        self.route_filter.bind("<<ComboboxSelected>>", lambda e: self._filter_routes())
        
        # Routes table
        table_frame = tk.Frame(left_panel, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        table_frame.pack(fill="both", expand=True, pady=(config.PADDING_SMALL, 0))
        
        # Treeview for routes
        columns = ("Route ID", "Vehicle", "Status", "Progress", "ETA")
        self.routes_tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings", 
            height=15,
            selectmode="browse"
        )
        
        # Configure columns
        column_config = {
            "Route ID": 80,
            "Vehicle": 80,
            "Status": 100,
            "Progress": 80,
            "ETA": 100
        }
        
        for col in columns:
            self.routes_tree.heading(col, text=col)
            self.routes_tree.column(col, width=column_config.get(col, 100), anchor="center")
        
        # Scrollbars
        tree_scroll_y = tk.Scrollbar(table_frame, orient="vertical", command=self.routes_tree.yview)
        tree_scroll_x = tk.Scrollbar(table_frame, orient="horizontal", command=self.routes_tree.xview)
        self.routes_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.routes_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Row colors and selection
        # Using darker text for better contrast on light backgrounds
        self.routes_tree.tag_configure('on_time', background='#D4EDDA', foreground='#000000')
        self.routes_tree.tag_configure('delayed', background='#FFF3CD', foreground='#000000')
        self.routes_tree.tag_configure('critical', background='#F8D7DA', foreground='#000000')
        self.routes_tree.tag_configure('selected', background=config.PRIMARY_COLOR, foreground='#FFFFFF')
        
        # Configure Treeview style for better contrast
        style = ttk.Style()
        style.configure("Treeview", 
            background="#FFFFFF",
            foreground="#000000",
            fieldbackground="#FFFFFF",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL)
        )
        style.configure("Treeview.Heading", 
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            background="#E9ECEF",
            foreground="#000000"
        )
        style.map("Treeview", 
            background=[('selected', config.PRIMARY_COLOR)],
            foreground=[('selected', '#FFFFFF')]
        )
        self.routes_tree.bind("<<TreeviewSelect>>", self._on_route_selected)
    
    def _create_route_details_panel(self, parent):
        """Create right panel with route details"""
        right_panel = tk.Frame(parent, bg=config.BG_LIGHT)
        right_panel.pack(side="left", fill="both", expand=True, padx=(config.PADDING_SMALL, 0))
        
        # Panel header
        details_header = tk.Frame(right_panel, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        details_header.pack(fill="x")
        
        tk.Label(
            details_header,
            text="Route Details",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left", padx=15, pady=10)
        
        # Action buttons
        actions_frame = tk.Frame(details_header, bg=config.BG_WHITE)
        actions_frame.pack(side="right", padx=15)
        
        self.complete_btn = tk.Button(
            actions_frame,
            text="Mark Complete",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg="#28A745",
            fg=config.BG_WHITE,
            activebackground="#218838",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
            state="disabled",
            command=self._mark_route_complete
        )
        self.complete_btn.pack(side="left", padx=3)
        
        self.alert_btn = tk.Button(
            actions_frame,
            text="Report Issue",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg="#FFC107",
            fg="#000000",
            activebackground="#E0A800",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5,
            state="disabled",
            command=self._report_issue
        )
        self.alert_btn.pack(side="left", padx=3)
        
        # Scrollable details area
        canvas = tk.Canvas(right_panel, bg=config.BG_LIGHT, highlightthickness=0)
        scrollbar = tk.Scrollbar(right_panel, orient="vertical", command=canvas.yview)
        self.details_frame = tk.Frame(canvas, bg=config.BG_WHITE)
        
        self.details_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.details_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, pady=(config.PADDING_SMALL, 0))
        scrollbar.pack(side="right", fill="y", pady=(config.PADDING_SMALL, 0))
        
        # Initial empty state
        self._show_empty_details()
    
    def _show_empty_details(self):
        """Show empty state when no route is selected"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        empty_label = tk.Label(
            self.details_frame,
            text="Select a route to view details",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        empty_label.pack(expand=True, pady=100)
    
    def _load_active_routes(self):
        """Load active routes from database"""
        try:
            if not self.repo:
                self.repo = AzureSqlRepository()
            
            # Fetch active routes (deliveries in transit)
            # Note: Using Status='In Transit' or Delivery_Time IS NULL for active routes
            routes = self.repo.fetch_all("""
                SELECT 
                    dl.Order_ID,
                    dl.VehicleID,
                    dl.Order_Date,
                    dl.Pickup_Time,
                    dl.Delivery_Time,
                    DATEDIFF(MINUTE, '00:00:00', CAST(dl.Pickup_Time AS TIME)) AS Pickup_Minutes,
                    v.Model AS Vehicle_Type,
                    v.Year AS Vehicle_Year
                FROM DeliveryLog dl
                LEFT JOIN Vehicles v ON dl.VehicleID = v.VehicleID
                WHERE dl.Status = 'In Transit' 
                   OR (dl.Pickup_Time IS NOT NULL AND dl.Delivery_Time IS NULL)
                ORDER BY dl.Order_Date DESC
            """)
            
            # Update summary metrics
            total_active = len(routes) if routes else 0
            self.total_active_card.update_value(str(total_active))
            
            # Calculate on-time vs delayed (example logic)
            if routes:
                # Assume routes taking > 60 min pickup time are delayed
                on_time = len([r for r in routes if r['Pickup_Minutes'] and r['Pickup_Minutes'] <= 60])
                delayed = total_active - on_time
                
                self.on_time_card.update_value(str(on_time))
                self.delayed_card.update_value(str(delayed))
                
                # Average progress (assume 50% if pickup done but not delivered)
                self.avg_progress_card.update_value("50%")
            else:
                self.on_time_card.update_value("0")
                self.delayed_card.update_value("0")
                self.avg_progress_card.update_value("—")
            
            # Populate routes table
            self._populate_routes_table(routes)
            
            # Update timestamp
            self.last_updated_label.config(
                text=f"Last updated: {datetime.now().strftime('%I:%M:%S %p')}"
            )
            
            logging.info(f"Loaded {total_active} active routes")
            
            # Schedule next refresh if auto-refresh is enabled
            if self.auto_refresh_var.get():
                self.after(self.refresh_interval, self._load_active_routes)
            
        except Exception as e:
            logging.error(f"Error loading active routes: {e}")
            messagebox.showerror("Error", f"Failed to load routes:\n{str(e)[:150]}")
    
    def _populate_routes_table(self, routes):
        """Populate the routes table with data"""
        # Clear existing data
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)
        
        if not routes:
            return
        
        for route in routes:
            order_id = route['Order_ID']
            vehicle_id = route['VehicleID'] if route['VehicleID'] else "N/A"
            pickup_min = route['Pickup_Minutes']
            
            # Determine status based on pickup time
            if pickup_min and pickup_min > 60:
                status = "Delayed"
                tag = 'delayed'
            elif pickup_min and pickup_min > 90:
                status = "Critical"
                tag = 'critical'
            else:
                status = "On Time"
                tag = 'on_time'
            
            # Progress (assume 50% for in-transit)
            progress = "50%"
            
            # ETA (example: add 30 min to pickup time)
            eta = "30 min" if pickup_min else "—"
            
            self.routes_tree.insert("", "end", values=(
                order_id, vehicle_id, status, progress, eta
            ), tags=(tag,), iid=str(order_id))
    
    def _filter_routes(self):
        """Filter routes based on selected filter"""
        # Re-load and apply filter
        # This is a simplified version - enhance as needed
        self._load_active_routes()
    
    def _on_route_selected(self, event):
        """Handle route selection"""
        selection = self.routes_tree.selection()
        if not selection:
            self._show_empty_details()
            self.complete_btn.config(state="disabled")
            self.alert_btn.config(state="disabled")
            return
        
        route_id = selection[0]
        self._show_route_details(route_id)
        self.complete_btn.config(state="normal")
        self.alert_btn.config(state="normal")
    
    def _show_route_details(self, route_id):
        """Show detailed information for selected route"""
        try:
            # Fetch detailed route info
            # Note: Order_ID is nvarchar, so it needs quotes in the query
            details = self.repo.fetch_all(f"""
                SELECT 
                    dl.*,
                    v.Model AS Vehicle_Type,
                    v.Year AS Vehicle_Year,
                    v.Miles AS Vehicle_Miles,
                    v.Area AS Vehicle_Area,
                    DATEDIFF(MINUTE, '00:00:00', CAST(dl.Pickup_Time AS TIME)) AS Pickup_Minutes
                FROM DeliveryLog dl
                LEFT JOIN Vehicles v ON dl.VehicleID = v.VehicleID
                WHERE dl.Order_ID = '{route_id}'
            """)
            
            if not details or len(details) == 0:
                self._show_empty_details()
                return
            
            route = details[0]
            
            # Clear existing details
            for widget in self.details_frame.winfo_children():
                widget.destroy()
            
            # Route information sections
            self._add_detail_section("Route Information", [
                ("Order ID", route['Order_ID']),
                ("Order Date", str(route['Order_Date'])[:19] if route['Order_Date'] else "N/A"),
                ("Status", route.get('Status', 'Unknown'))
            ])
            
            self._add_detail_section("Vehicle Information", [
                ("Vehicle ID", route['VehicleID'] if route['VehicleID'] else "Not Assigned"),
                ("Model", route.get('Vehicle_Type', 'N/A')),
                ("Year", route.get('Vehicle_Year', 'N/A')),
                ("Area", route.get('Vehicle_Area', 'N/A'))
            ])
            
            self._add_detail_section("Timing Information", [
                ("Pickup Time", f"{round(route['Pickup_Minutes'], 1)} minutes" if route.get('Pickup_Minutes') else "Not picked up"),
                ("Estimated Delivery", "30 minutes (example)"),
                ("Elapsed Time", f"{round(route['Pickup_Minutes'], 1)} min" if route.get('Pickup_Minutes') else "—")
            ])
            
            # Progress bar
            progress_frame = tk.Frame(self.details_frame, bg=config.BG_WHITE)
            progress_frame.pack(fill="x", padx=20, pady=15)
            
            tk.Label(
                progress_frame,
                text="Delivery Progress",
                font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
                bg=config.BG_WHITE,
                fg=config.TEXT_PRIMARY
            ).pack(anchor="w")
            
            # Simple progress bar using canvas
            progress_canvas = tk.Canvas(progress_frame, height=30, bg="#E0E0E0", highlightthickness=0)
            progress_canvas.pack(fill="x", pady=5)
            
            # Draw progress (50% for in-transit)
            progress_canvas.create_rectangle(0, 0, progress_canvas.winfo_reqwidth() * 0.5, 30, fill=config.PRIMARY_COLOR, outline="")
            tk.Label(progress_canvas, text="50%", bg=config.PRIMARY_COLOR, fg=config.BG_WHITE).place(relx=0.5, rely=0.5, anchor="center")
            
        except Exception as e:
            logging.error(f"Error showing route details: {e}")
            self._show_empty_details()
    
    def _add_detail_section(self, title, items):
        """Add a detail section with title and items"""
        section_frame = tk.Frame(self.details_frame, bg=config.BG_WHITE)
        section_frame.pack(fill="x", padx=20, pady=10)
        
        # Section title
        tk.Label(
            section_frame,
            text=title,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 5))
        
        # Section items
        for label, value in items:
            item_frame = tk.Frame(section_frame, bg=config.BG_WHITE)
            item_frame.pack(fill="x", pady=2)
            
            tk.Label(
                item_frame,
                text=f"{label}:",
                font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
                bg=config.BG_WHITE,
                fg=config.TEXT_SECONDARY,
                width=20,
                anchor="w"
            ).pack(side="left")
            
            tk.Label(
                item_frame,
                text=str(value),
                font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
                bg=config.BG_WHITE,
                fg=config.TEXT_PRIMARY,
                anchor="w"
            ).pack(side="left")
        
        # Separator
        tk.Frame(section_frame, height=1, bg="#E0E0E0").pack(fill="x", pady=(10, 0))
    
    def _toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        if self.auto_refresh_var.get():
            logging.info("Auto-refresh enabled")
            self._load_active_routes()
        else:
            logging.info("Auto-refresh disabled")
    
    def _mark_route_complete(self):
        """Mark selected route as complete"""
        selection = self.routes_tree.selection()
        if not selection:
            return
        
        route_id = selection[0]
        
        if messagebox.askyesno("Confirm", f"Mark route {route_id} as complete?"):
            try:
                # Update delivery time to current time
                # Note: Order_ID is nvarchar, so it needs quotes
                self.repo.execute(f"""
                    UPDATE DeliveryLog
                    SET Delivery_Time = DATEDIFF(MINUTE, '00:00:00', CAST(GETDATE() AS TIME))
                    WHERE Order_ID = '{route_id}'
                """)
                
                messagebox.showinfo("Success", f"Route {route_id} marked as complete!")
                self._load_active_routes()
                self._show_empty_details()
                
            except Exception as e:
                logging.error(f"Error completing route: {e}")
                messagebox.showerror("Error", f"Failed to complete route:\n{str(e)}")
    
    def _report_issue(self):
        """Report an issue with selected route"""
        selection = self.routes_tree.selection()
        if not selection:
            return
        
        route_id = selection[0]
        
        # Simple issue reporting dialog
        issue_window = tk.Toplevel(self)
        issue_window.title(f"Report Issue - Route {route_id}")
        issue_window.geometry("400x300")
        issue_window.configure(bg=config.BG_WHITE)
        
        tk.Label(
            issue_window,
            text=f"Report Issue for Route {route_id}",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(pady=20)
        
        tk.Label(
            issue_window,
            text="Issue Description:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w", padx=20)
        
        issue_text = tk.Text(issue_window, height=8, width=40, font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL))
        issue_text.pack(padx=20, pady=10)
        
        def submit_issue():
            issue_desc = issue_text.get("1.0", "end-1c")
            if issue_desc.strip():
                messagebox.showinfo("Issue Reported", f"Issue reported for route {route_id}:\n{issue_desc[:100]}...")
                logging.info(f"Issue reported for route {route_id}: {issue_desc}")
                issue_window.destroy()
            else:
                messagebox.showwarning("Empty Issue", "Please describe the issue")
        
        tk.Button(
            issue_window,
            text="Submit Issue",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#DC3545",
            fg=config.BG_WHITE,
            activebackground="#C82333",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=submit_issue
        ).pack(pady=10)
    
    def destroy(self):
        """Clean up resources"""
        if self.repo:
            try:
                self.repo.close()
                logging.info("Active routes repository connection closed")
            except Exception as e:
                logging.error(f"Error closing repository: {e}")
        super().destroy()