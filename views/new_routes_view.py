"""
New Routes View - Create and schedule new delivery routes
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
from datetime import datetime, date, timedelta


class NewRoutesView(tk.Frame):
    """New Routes - Route creation and planning"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.vehicles_data = []
        self.stores_data = []
        self.drivers_data = []
        self.products_data = []
        self.drop_locations_data = []
        self._create_ui()
        self.after(100, self._load_form_data)
    
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
        
        # Header
        self._create_header(content)
        
        # Main form container
        form_container = tk.Frame(content, bg=config.BG_LIGHT)
        form_container.pack(fill="both", expand=True, pady=(config.PADDING_MEDIUM, 0))
        
        # Left panel: Route form
        self._create_route_form(form_container)
        
        # Right panel: Preview/Summary
        self._create_route_summary(form_container)
    
    def _create_header(self, parent):
        """Create header section"""
        header_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        title_label = tk.Label(
            header_frame, 
            text="Create New Delivery Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, 
            fg=config.TEXT_PRIMARY
        )
        title_label.pack(side="left")
        
        subtitle = tk.Label(
            header_frame,
            text="Plan and schedule new delivery routes",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_SECONDARY
        )
        subtitle.pack(side="left", padx=(15, 0))
    
    def _create_route_form(self, parent):
        """Create route details form"""
        left_panel = tk.Frame(parent, bg=config.BG_LIGHT)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, config.PADDING_SMALL))
        
        # Form card
        form_card = tk.Frame(left_panel, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        form_card.pack(fill="both", expand=True)
        
        # Form header
        form_header = tk.Frame(form_card, bg=config.BG_WHITE)
        form_header.pack(fill="x", padx=20, pady=15)
        
        tk.Label(
            form_header,
            text="Route Information",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left")
        
        # Form fields container
        fields_frame = tk.Frame(form_card, bg=config.BG_WHITE)
        fields_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Order ID
        self._create_form_field(fields_frame, "Order ID:", 0)
        self.order_id_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.order_id_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Start Location (Depot)
        self._create_form_field(fields_frame, "Start Location:", 1)
        self.start_location_var = tk.StringVar(value="Central Depot")
        self.start_location_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.start_location_var,
            values=["Central Depot", "North Warehouse", "South Distribution Center"],
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL)
        )
        self.start_location_combo.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Vehicle Selection
        self._create_form_field(fields_frame, "Assign Vehicle:", 2)
        self.vehicle_var = tk.StringVar()
        self.vehicle_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.vehicle_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL)
        )
        self.vehicle_combo.grid(row=2, column=1, sticky="ew", pady=5, padx=(10, 0))
        self.vehicle_combo.bind("<<ComboboxSelected>>", self._on_vehicle_selected)
        
        # Driver Selection
        self._create_form_field(fields_frame, "Assign Driver:", 3)
        self.driver_var = tk.StringVar()
        self.driver_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.driver_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL)
        )
        self.driver_combo.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Product Selection
        self._create_form_field(fields_frame, "Product:", 4)
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.product_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL)
        )
        self.product_combo.grid(row=4, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Store Selection (Single store - origin)
        self._create_form_field(fields_frame, "Pickup Store:", 5)
        self.store_var = tk.StringVar()
        self.store_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.store_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL)
        )
        self.store_combo.grid(row=5, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Drop Location Selection (with search)
        self._create_form_field(fields_frame, "Drop Location:", 6)
        drop_container = tk.Frame(fields_frame, bg=config.BG_WHITE)
        drop_container.grid(row=6, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        self.drop_search_var = tk.StringVar()
        self.drop_search_entry = tk.Entry(
            drop_container,
            textvariable=self.drop_search_var,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            relief="solid",
            borderwidth=1
        )
        self.drop_search_entry.pack(side="left", fill="x", expand=True)
        self.drop_search_entry.bind('<KeyRelease>', self._filter_drop_locations)
        
        self.drop_location_var = tk.StringVar()
        self.drop_location_combo = ttk.Combobox(
            drop_container,
            textvariable=self.drop_location_var,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            width=30
        )
        self.drop_location_combo.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Order Date
        self._create_form_field(fields_frame, "Order Date:", 7)
        self.order_date_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.order_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.order_date_entry.grid(row=7, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Priority
        self._create_form_field(fields_frame, "Priority:", 8)
        self.priority_var = tk.StringVar(value="Normal")
        priority_frame = tk.Frame(fields_frame, bg=config.BG_WHITE)
        priority_frame.grid(row=8, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        for priority in ["Low", "Normal", "High", "Urgent"]:
            tk.Radiobutton(
                priority_frame,
                text=priority,
                variable=self.priority_var,
                value=priority,
                font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
                bg=config.BG_WHITE,
                activebackground=config.BG_WHITE
            ).pack(side="left", padx=5)
        
        # Estimated Pickup Time
        self._create_form_field(fields_frame, "Est. Pickup Time (min):", 9)
        self.pickup_time_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.pickup_time_entry.insert(0, "30")
        self.pickup_time_entry.grid(row=9, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Estimated Delivery Time
        self._create_form_field(fields_frame, "Est. Delivery Time (min):", 10)
        self.delivery_time_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.delivery_time_entry.insert(0, "45")
        self.delivery_time_entry.grid(row=10, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Notes
        self._create_form_field(fields_frame, "Notes (Optional):", 11, align_top=True)
        self.notes_text = tk.Text(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            height=4,
            relief="solid",
            borderwidth=1,
            wrap="word"
        )
        self.notes_text.grid(row=11, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        
        # Action buttons
        buttons_frame = tk.Frame(form_card, bg=config.BG_WHITE)
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        tk.Button(
            buttons_frame,
            text="Clear Form",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg="#6C757D",
            fg=config.BG_WHITE,
            activebackground="#5A6268",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._clear_form
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            buttons_frame,
            text="Optimize",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#17A2B8",
            fg=config.BG_WHITE,
            activebackground="#138496",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._optimize_route
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            buttons_frame,
            text="Create Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.PRIMARY_COLOR,
            fg=config.BG_WHITE,
            activebackground=config.BUTTON_HOVER,  # Changed from PRIMARY_HOVER
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=8,
            command=self._create_route
        ).pack(side="right")
    
    def _create_form_field(self, parent, label_text, row, align_top=False):
        """Helper to create form field label"""
        label = tk.Label(
            parent,
            text=label_text,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY,
            anchor="w"
        )
        sticky = "nw" if align_top else "w"
        label.grid(row=row, column=0, sticky=sticky, pady=5, padx=(0, 10))
    
    def _create_route_summary(self, parent):
        """Create route summary/preview panel"""
        right_panel = tk.Frame(parent, bg=config.BG_LIGHT)
        right_panel.pack(side="left", fill="both", expand=True, padx=(config.PADDING_SMALL, 0))
        
        # Summary card
        summary_card = tk.Frame(right_panel, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        summary_card.pack(fill="both", expand=True)
        
        # Summary header
        summary_header = tk.Frame(summary_card, bg=config.BG_WHITE)
        summary_header.pack(fill="x", padx=20, pady=15)
        
        tk.Label(
            summary_header,
            text="Route Summary",
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left")
        
        # Summary content
        summary_content = tk.Frame(summary_card, bg=config.BG_WHITE)
        summary_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Vehicle info section
        vehicle_section = tk.Frame(summary_content, bg="#F8F9FA", relief="solid", borderwidth=1)
        vehicle_section.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            vehicle_section,
            text="Assigned Vehicle",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#F8F9FA",
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.vehicle_info_label = tk.Label(
            vehicle_section,
            text="No vehicle selected",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg="#F8F9FA",
            fg=config.TEXT_SECONDARY,
            anchor="w",
            justify="left"
        )
        self.vehicle_info_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Stores section
        stores_section = tk.Frame(summary_content, bg="#F8F9FA", relief="solid", borderwidth=1)
        stores_section.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(
            stores_section,
            text="Delivery Stops",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#F8F9FA",
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.stores_count_label = tk.Label(
            stores_section,
            text="0 stores selected",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg="#F8F9FA",
            fg=config.TEXT_SECONDARY
        )
        self.stores_count_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Time estimates section
        time_section = tk.Frame(summary_content, bg="#F8F9FA", relief="solid", borderwidth=1)
        time_section.pack(fill="x")
        
        tk.Label(
            time_section,
            text="Time Estimates",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#F8F9FA",
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.time_estimate_label = tk.Label(
            time_section,
            text="Total: -- minutes\nPickup: -- min | Delivery: -- min",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg="#F8F9FA",
            fg=config.TEXT_SECONDARY,
            anchor="w",
            justify="left"
        )
        self.time_estimate_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Quick stats
        stats_frame = tk.Frame(summary_card, bg=config.BG_WHITE)
        stats_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        tk.Label(
            stats_frame,
            text="Quick Stats",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 10))
        
        # Available vehicles count
        self.available_vehicles_label = tk.Label(
            stats_frame,
            text="Available vehicles: Loading...",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        self.available_vehicles_label.pack(anchor="w", pady=2)
        
        # Active routes count
        self.active_routes_label = tk.Label(
            stats_frame,
            text="Active routes today: Loading...",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        self.active_routes_label.pack(anchor="w", pady=2)
    
    def _load_form_data(self):
        """Load vehicles, stores, drivers, products, and drop locations from database"""
        try:
            self.repo = AzureSqlRepository()
            
            # Load vehicles
            self.vehicles_data = self.repo.fetch_all("""
                SELECT VehicleID, Model, Year, Miles, Area
                FROM Vehicles
                ORDER BY VehicleID
            """)
            
            if self.vehicles_data:
                vehicle_options = [
                    f"{v['VehicleID']} - {v['Model']} ({v['Year']})"
                    for v in self.vehicles_data
                ]
                self.vehicle_combo['values'] = vehicle_options
            
            # Load drivers
            self.drivers_data = self.repo.fetch_all("""
                SELECT DriverID, FirstName, LastName
                FROM Drivers
                ORDER BY DriverID
            """)
            
            if self.drivers_data:
                driver_options = [
                    f"{d['DriverID']} - {d['FirstName']} {d['LastName']}"
                    for d in self.drivers_data
                ]
                self.driver_combo['values'] = driver_options
            
            # Load products
            self.products_data = self.repo.fetch_all("""
                SELECT ProductID, ProdDescription
                FROM Products
                ORDER BY ProductID
            """)
            
            if self.products_data:
                product_options = [
                    f"{p['ProductID']} - {p['ProdDescription']}"
                    for p in self.products_data
                ]
                self.product_combo['values'] = product_options
            
            # Load stores
            self.stores_data = self.repo.fetch_all("""
                SELECT StoreID, lat, lon
                FROM Stores
                ORDER BY StoreID
            """)
            
            if self.stores_data:
                store_options = [
                    f"Store {s['StoreID']} (Lat: {s['lat']:.4f}, Lon: {s['lon']:.4f})"
                    for s in self.stores_data
                ]
                self.store_combo['values'] = store_options
            
            # Load drop locations (limit initial load for performance, use search for full list)
            self.drop_locations_data = self.repo.fetch_all("""
                SELECT TOP 500 DropLocationID, lat, lon
                FROM DropLocations
                ORDER BY DropLocationID
            """)
            
            if self.drop_locations_data:
                drop_options = [
                    f"Drop {d['DropLocationID']} (Lat: {d['lat']:.4f}, Lon: {d['lon']:.4f})"
                    for d in self.drop_locations_data
                ]
                self.drop_location_combo['values'] = drop_options
            
            # Update quick stats
            total_vehicles = len(self.vehicles_data) if self.vehicles_data else 0
            self.available_vehicles_label.config(text=f"Available vehicles: {total_vehicles}")
            
            # Get active routes count
            active_count = self.repo.fetch_all("""
                SELECT COUNT(*) AS Count
                FROM DeliveryLog
                WHERE CAST(Order_Date AS DATE) = CAST(GETDATE() AS DATE)
            """)
            active_routes = active_count[0]['Count'] if active_count else 0
            self.active_routes_label.config(text=f"Active routes today: {active_routes}")
            
            logging.info(f"Loaded {total_vehicles} vehicles, {len(self.drivers_data) if self.drivers_data else 0} drivers, "
                        f"{len(self.products_data) if self.products_data else 0} products, "
                        f"{len(self.stores_data) if self.stores_data else 0} stores, "
                        f"{len(self.drop_locations_data) if self.drop_locations_data else 0} drop locations")
            
        except Exception as e:
            logging.error(f"Error loading form data: {e}")
            messagebox.showerror("Error", f"Failed to load form data:\n{str(e)[:150]}")
    
    def _filter_drop_locations(self, event=None):
        """Filter drop locations based on search text"""
        search_text = self.drop_search_var.get().strip()
        
        if not search_text or len(search_text) < 2:
            # Show initial 500 if no search
            if self.drop_locations_data:
                drop_options = [
                    f"Drop {d['DropLocationID']} (Lat: {d['lat']:.4f}, Lon: {d['lon']:.4f})"
                    for d in self.drop_locations_data
                ]
                self.drop_location_combo['values'] = drop_options
            return
        
        try:
            # Search by ID if numeric, otherwise search in a broader way
            if search_text.isdigit():
                query = f"""
                    SELECT TOP 100 DropLocationID, lat, lon
                    FROM DropLocations
                    WHERE CAST(DropLocationID AS VARCHAR) LIKE '%{search_text}%'
                    ORDER BY DropLocationID
                """
            else:
                # Search by lat/lon pattern
                query = f"""
                    SELECT TOP 100 DropLocationID, lat, lon
                    FROM DropLocations
                    ORDER BY DropLocationID
                """
            
            results = self.repo.fetch_all(query)
            if results:
                drop_options = [
                    f"Drop {d['DropLocationID']} (Lat: {d['lat']:.4f}, Lon: {d['lon']:.4f})"
                    for d in results
                ]
                self.drop_location_combo['values'] = drop_options
                # Update the data reference for selection parsing
                self.drop_locations_data = results
        except Exception as e:
            logging.error(f"Error filtering drop locations: {e}")

    def _on_vehicle_selected(self, event=None):
        """Handle vehicle selection"""
        selected_idx = self.vehicle_combo.current()
        if selected_idx >= 0 and self.vehicles_data:
            vehicle = self.vehicles_data[selected_idx]
            vehicle_info = (
                f"{vehicle['Model']}\n"
                f"Year: {vehicle['Year']}\n"
                f"Miles: {vehicle['Miles']}\n"
                f"Area: {vehicle['Area']}"
            )
            self.vehicle_info_label.config(text=vehicle_info)
        
        self._update_summary()
    
    def _update_summary(self):
        """Update summary panel"""
        # Update selection count label
        store_sel = self.store_combo.current() >= 0
        drop_sel = self.drop_location_combo.current() >= 0
        
        selection_text = []
        if store_sel:
            selection_text.append("Store selected")
        if drop_sel:
            selection_text.append("Drop location selected")
        
        self.stores_count_label.config(
            text=", ".join(selection_text) if selection_text else "No selections"
        )
        
        # Update time estimates
        try:
            # Simple dynamic estimate
            base_pickup = 30
            base_delivery = 45
            
            total_time = base_pickup + base_delivery
            
            self.time_estimate_label.config(
                text=f"Total: {total_time} minutes\nPickup: {base_pickup} min | Delivery: {base_delivery} min"
            )
            
        except ValueError:
            self.time_estimate_label.config(
                text="Invalid time values"
            )
    
    def _clear_form(self):
        """Clear all form fields"""
        if messagebox.askyesno("Clear Form", "Are you sure you want to clear all fields?"):
            self.order_id_entry.delete(0, tk.END)
            self.vehicle_var.set("")
            self.driver_var.set("")
            self.product_var.set("")
            self.store_var.set("")
            self.drop_location_var.set("")
            self.drop_search_var.set("")
            self.vehicle_info_label.config(text="No vehicle selected")
            self.order_date_entry.delete(0, tk.END)
            self.order_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
            self.priority_var.set("Normal")
            self.pickup_time_entry.delete(0, tk.END)
            self.pickup_time_entry.insert(0, "30")
            self.delivery_time_entry.delete(0, tk.END)
            self.delivery_time_entry.insert(0, "45")
            self.notes_text.delete("1.0", tk.END)
            self._update_summary()
            logging.info("Form cleared")
    
    def _create_route(self):
        """Create new delivery route"""
        try:
            # Validate inputs
            order_id = self.order_id_entry.get().strip()
            if not order_id:
                messagebox.showwarning("Validation Error", "Order ID is required")
                return
            
            vehicle_idx = self.vehicle_combo.current()
            if vehicle_idx < 0:
                messagebox.showwarning("Validation Error", "Please select a vehicle")
                return
            
            driver_idx = self.driver_combo.current()
            if driver_idx < 0:
                messagebox.showwarning("Validation Error", "Please select a driver")
                return
            
            product_idx = self.product_combo.current()
            if product_idx < 0:
                messagebox.showwarning("Validation Error", "Please select a product")
                return
            
            store_idx = self.store_combo.current()
            if store_idx < 0:
                messagebox.showwarning("Validation Error", "Please select a pickup store")
                return
            
            drop_idx = self.drop_location_combo.current()
            if drop_idx < 0:
                messagebox.showwarning("Validation Error", "Please select a drop location")
                return
            
            order_date = self.order_date_entry.get().strip()
            if not order_date:
                messagebox.showwarning("Validation Error", "Order date is required")
                return
            
            try:
                pickup_time = int(self.pickup_time_entry.get())
                delivery_time = int(self.delivery_time_entry.get())
            except ValueError:
                messagebox.showwarning("Validation Error", "Pickup and delivery times must be numbers")
                return
            
            # Get IDs from selections
            vehicle = self.vehicles_data[vehicle_idx]
            vehicle_id = vehicle['VehicleID']
            
            driver = self.drivers_data[driver_idx]
            driver_id = driver['DriverID']
            
            product = self.products_data[product_idx]
            product_id = product['ProductID']
            
            store = self.stores_data[store_idx]
            store_id = store['StoreID']
            
            drop_location = self.drop_locations_data[drop_idx]
            drop_location_id = drop_location['DropLocationID']
            
            # Insert into DeliveryLog
            current_dt = datetime.now()
            current_time_str = current_dt.strftime("%H:%M:%S")
            
            # Calculate estimated pickup time (Time of day)
            est_pickup_dt = current_dt + timedelta(minutes=pickup_time)
            est_pickup_str = est_pickup_dt.strftime("%H:%M:%S")
            
            self.repo.execute(f"""
                INSERT INTO DeliveryLog (
                    Order_ID, VehicleID, DriverID, ProductID, StoreID, DropLocationID,
                    Order_Date, Order_Time, Pickup_Time, Delivery_Time, Status
                )
                VALUES (
                    '{order_id}', 
                    {vehicle_id}, 
                    {driver_id},
                    {product_id},
                    {store_id},
                    {drop_location_id},
                    '{order_date}', 
                    '{current_time_str}', 
                    '{est_pickup_str}',
                    {delivery_time},
                    'Pending'
                )
            """)
            
            messagebox.showinfo(
                "Success", 
                f"Route created successfully!\n\n"
                f"Order ID: {order_id}\n"
                f"Vehicle: {vehicle_id}\n"
                f"Driver: {driver_id}\n"
                f"Product: {product_id}\n"
                f"Store: {store_id} -> Drop: {drop_location_id}\n"
                f"Est. Time: {pickup_time + delivery_time} min"
            )
            
            logging.info(f"Route created: Order {order_id}, Vehicle {vehicle_id}, Driver {driver_id}, "
                        f"Product {product_id}, Store {store_id} -> Drop {drop_location_id}")
            
            # Clear form after successful creation
            self._clear_form()
            
        except Exception as e:
            logging.error(f"Error creating route: {e}")
            messagebox.showerror("Error", f"Failed to create route:\n{str(e)[:200]}")
    
    def _optimize_route(self):
        """
        Optimize route using two strategies:
        1. Form-based optimization: Suggest best vehicle/times for current form selections
        2. Fleet-wide optimization: Optimize all pending deliveries across fleet
        """
        store_idx = self.store_combo.current()
        
        # If store is selected, optimize THIS route
        if store_idx >= 0:
            self._optimize_current_route(store_idx)
        else:
            # If no store selected, offer fleet-wide optimization
            self._optimize_fleet_routes()
    
    def _optimize_current_route(self, store_idx):
        """Optimize the current route form based on selected store"""
        try:
            store = self.stores_data[store_idx]
            store_id = store['StoreID']
            
            # 1. Find best vehicle (lowest avg delivery time for this store)
            best_vehicle_query = f"""
                SELECT TOP 1 
                    VehicleID, 
                    AVG(Delivery_Time) as AvgTime,
                    COUNT(*) as DeliveryCount
                FROM DeliveryLog
                WHERE StoreID = {store_id}
                  AND Delivery_Time IS NOT NULL
                  AND Delivery_Time > 0
                  AND Delivery_Time BETWEEN 20 AND 400
                GROUP BY VehicleID
                HAVING COUNT(*) >= 3
                ORDER BY AVG(Delivery_Time) ASC
            """
            best_vehicle = self.repo.fetch_all(best_vehicle_query)
            
            vehicle_found = False
            vehicle_name = ""
            avg_time = 0
            
            if best_vehicle and len(best_vehicle) > 0:
                best_vehicle_id = best_vehicle[0]['VehicleID']
                avg_time = best_vehicle[0]['AvgTime']
                
                # Find index in combo
                for i, v in enumerate(self.vehicles_data):
                    if v['VehicleID'] == best_vehicle_id:
                        self.vehicle_combo.current(i)
                        self._on_vehicle_selected(None)
                        vehicle_found = True
                        vehicle_name = f"{v['Model']} ({v['Year']})"
                        break
            
            # 2. Estimate pickup time based on prep time patterns
            # ✅ Fixed: Use CAST to convert TIME to DATETIME for DATEDIFF
            pickup_query = f"""
                SELECT 
                    AVG(
                        DATEDIFF(
                            MINUTE, 
                            CAST(CAST(GETDATE() AS DATE) AS DATETIME) + CAST(Order_Time AS DATETIME),
                            CAST(CAST(GETDATE() AS DATE) AS DATETIME) + CAST(Pickup_Time AS DATETIME)
                        )
                    ) as AvgPrep
                FROM DeliveryLog
                WHERE StoreID = {store_id}
                  AND Pickup_Time IS NOT NULL
                  AND Order_Time IS NOT NULL
                  AND Pickup_Time > Order_Time
            """
            pickup_results = self.repo.fetch_all(pickup_query)
            
            pickup_estimate = 30  # Default
            if pickup_results and len(pickup_results) > 0 and pickup_results[0]['AvgPrep']:
                pickup_estimate = max(5, min(120, int(pickup_results[0]['AvgPrep'])))  # Clamp between 5-120
                self.pickup_time_entry.delete(0, tk.END)
                self.pickup_time_entry.insert(0, str(pickup_estimate))
            
            # 3. Estimate delivery time based on historical average
            delivery_query = f"""
                SELECT AVG(Delivery_Time) as AvgTime
                FROM DeliveryLog
                WHERE StoreID = {store_id}
                  AND Delivery_Time IS NOT NULL
                  AND Delivery_Time > 0
                  AND Delivery_Time BETWEEN 20 AND 400
            """
            delivery_results = self.repo.fetch_all(delivery_query)
            
            delivery_estimate = 45  # Default
            if delivery_results and len(delivery_results) > 0 and delivery_results[0]['AvgTime']:
                delivery_estimate = int(delivery_results[0]['AvgTime'])
                self.delivery_time_entry.delete(0, tk.END)
                self.delivery_time_entry.insert(0, str(delivery_estimate))
            
            # 4. Update summary
            self._update_summary()
            
            # Build optimization message
            msg = "Route Optimization Complete!\n\n"
            msg += "Optimizations Applied:\n\n"
            
            if vehicle_found:
                msg += f"Vehicle: {vehicle_name}\n"
                msg += f"   Best performer for this store (avg: {int(avg_time)} min)\n\n"
            else:
                msg += "Vehicle: No historical data found\n"
                msg += "   (Need at least 3 deliveries per vehicle)\n\n"
            
            msg += f"Pickup Time: {pickup_estimate} minutes\n"
            msg += f"   Based on historical preparation patterns\n\n"
            
            msg += f"Delivery Time: {delivery_estimate} minutes\n"
            msg += f"   Based on Store {store_id} average\n\n"
            
            total_time = pickup_estimate + delivery_estimate
            msg += f"Total Estimated Time: {total_time} minutes\n"
            msg += f"   ({total_time // 60}h {total_time % 60}min)"
            
            messagebox.showinfo("Optimization Complete", msg)
            logging.info(f"Route optimized: Store {store_id}, est. {total_time} min")
                
        except Exception as e:
            logging.error(f"Route optimization error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Optimization failed:\n{str(e)[:200]}")
    
    def _optimize_fleet_routes(self):
        """Optimize all pending deliveries across the entire fleet"""
        try:
            from backend.route_optimizer import RouteOptimizer
            
            # Show loading message
            loading_msg = messagebox.showinfo(
                "Fleet Optimization",
                "Analyzing pending deliveries and available vehicles...\n\nPlease wait..."
            )
            self.update()
            
            # Create optimizer
            optimizer = RouteOptimizer(self.repo)
            
            # Get current status first
            summary = optimizer.get_optimization_summary()
            
            if summary['pending_deliveries'] == 0:
                messagebox.showinfo(
                    "No Pending Deliveries",
                    "There are no pending deliveries to optimize.\n\n"
                    "Fleet-wide optimization requires unassigned deliveries in the system.\n\n"
                    "Tip: Create individual routes using this form, or import pending orders."
                )
                return
            
            # Show confirmation with details
            confirm_msg = (
                f"Fleet-Wide Route Optimization\n\n"
                f"Found:\n"
                f"  • {summary['pending_deliveries']} pending deliveries\n"
                f"  • {summary['unique_stores']} unique stores\n"
                f"  • {summary['vehicles_available']} available vehicles\n\n"
                f"Optimization potential: {summary['optimization_potential']}\n\n"
                f"This will automatically assign pending deliveries to vehicles\n"
                f"using an intelligent clustering algorithm.\n\n"
                f"Proceed with fleet optimization?"
            )
            
            if not messagebox.askyesno("Confirm Fleet Optimization", confirm_msg):
                return
            
            # Run optimization
            logging.info("Starting fleet-wide route optimization...")
            result = optimizer.optimize_routes(max_deliveries_per_vehicle=10)
            
            if result['success']:
                # Show success message with details
                success_msg = (
                    f"Fleet Optimization Complete!\n\n"
                    f"Results:\n"
                    f"  • Deliveries Optimized: {result['total_deliveries']}\n"
                    f"  • Vehicles Assigned: {result['vehicles_used']}\n"
                    f"  • Est. Time Saved: {result['estimated_time_saved']} minutes\n"
                    f"    ({result['estimated_time_saved'] // 60}h {result['estimated_time_saved'] % 60}min)\n\n"
                    f"Optimization Strategy:\n"
                    f"  • Grouped deliveries by store location\n"
                    f"  • Balanced load across available vehicles\n"
                    f"  • Minimized total delivery time\n\n"
                    f"{result['message']}"
                )
                
                # Show route details
                if result['optimized_routes']:
                    success_msg += "\n\nVehicle Assignments:\n"
                    for idx, route in enumerate(result['optimized_routes'][:5], 1):  # Show first 5
                        success_msg += f"  {idx}. Vehicle {route['vehicle_id']}: {route['delivery_count']} deliveries\n"
                    
                    if len(result['optimized_routes']) > 5:
                        success_msg += f"  ... and {len(result['optimized_routes']) - 5} more\n"
                
                messagebox.showinfo("Fleet Optimization Complete", success_msg)
                
                # Offer to view optimized routes
                if messagebox.askyesno("View Routes", "Would you like to view the optimized routes?"):
                    # Here you could switch to the routes view or refresh data
                    # For now, just log it
                    logging.info("User requested to view optimized routes")
                    messagebox.showinfo(
                        "View Routes",
                        "Navigate to the 'Routes' tab to view all optimized delivery routes.\n\n"
                        "The Routes view shows all active deliveries with their assigned vehicles."
                    )
                
                logging.info(f"Fleet optimization complete: {result['total_deliveries']} deliveries across {result['vehicles_used']} vehicles")
            else:
                messagebox.showerror(
                    "Optimization Failed",
                    f"Fleet optimization encountered an error:\n\n{result['message']}"
                )
            
        except ImportError:
            messagebox.showerror(
                "Module Not Found",
                "Route optimizer module not found.\n\n"
                "Please ensure backend/route_optimizer.py exists.\n\n"
                "This feature requires the route optimization module to be installed."
            )
        except Exception as e:
            logging.error(f"Fleet optimization error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "Optimization Error",
                f"An error occurred during fleet optimization:\n\n{str(e)[:200]}"
            )
    
    def destroy(self):
        """Clean up resources"""
        if self.repo:
            try:
                self.repo.close()
                logging.info("New routes repository connection closed")
            except Exception as e:
                logging.error(f"Error closing repository: {e}")
        super().destroy()