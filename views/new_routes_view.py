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
            text="🗺️ Create New Delivery Route",
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
        
        # Store Selection (Multi-select)
        self._create_form_field(fields_frame, "Delivery Stores:", 3, align_top=True)
        
        stores_container = tk.Frame(fields_frame, bg=config.BG_WHITE)
        stores_container.grid(row=3, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Listbox with scrollbar for store selection
        stores_scroll = tk.Scrollbar(stores_container, orient="vertical")
        self.stores_listbox = tk.Listbox(
            stores_container,
            selectmode="multiple",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            height=6,
            yscrollcommand=stores_scroll.set,
            relief="solid",
            borderwidth=1
        )
        stores_scroll.config(command=self.stores_listbox.yview)
        self.stores_listbox.bind('<<ListboxSelect>>', lambda e: self._update_summary())
        
        self.stores_listbox.pack(side="left", fill="both", expand=True)
        stores_scroll.pack(side="right", fill="y")
        
        # Order Date
        self._create_form_field(fields_frame, "Order Date:", 4)
        self.order_date_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.order_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.order_date_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Priority
        self._create_form_field(fields_frame, "Priority:", 5)
        self.priority_var = tk.StringVar(value="Normal")
        priority_frame = tk.Frame(fields_frame, bg=config.BG_WHITE)
        priority_frame.grid(row=5, column=1, sticky="ew", pady=5, padx=(10, 0))
        
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
        self._create_form_field(fields_frame, "Est. Pickup Time (min):", 6)
        self.pickup_time_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.pickup_time_entry.insert(0, "30")
        self.pickup_time_entry.grid(row=6, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Estimated Delivery Time
        self._create_form_field(fields_frame, "Est. Delivery Time (min):", 7)
        self.delivery_time_entry = tk.Entry(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            relief="solid",
            borderwidth=1
        )
        self.delivery_time_entry.insert(0, "45")
        self.delivery_time_entry.grid(row=7, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        # Notes
        self._create_form_field(fields_frame, "Notes (Optional):", 8, align_top=True)
        self.notes_text = tk.Text(
            fields_frame,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            height=4,
            relief="solid",
            borderwidth=1,
            wrap="word"
        )
        self.notes_text.grid(row=8, column=1, sticky="ew", pady=5, padx=(10, 0))
        
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
            text="✨ Optimize",
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
            text="📊 Route Summary",
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
            text="💡 Quick Stats",
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
        """Load vehicles and stores data from database"""
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
            
            # Load stores
            self.stores_data = self.repo.fetch_all("""
                SELECT StoreID, lat, lon
                FROM Stores
                ORDER BY StoreID
            """)
            
            if self.stores_data:
                self.stores_listbox.delete(0, tk.END)
                for store in self.stores_data:
                    store_display = f"Store {store['StoreID']} (Lat: {store['lat']}, Lon: {store['lon']})"
                    self.stores_listbox.insert(tk.END, store_display)
            
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
            
            logging.info(f"Loaded {total_vehicles} vehicles and {len(self.stores_data) if self.stores_data else 0} stores")
            
        except Exception as e:
            logging.error(f"Error loading form data: {e}")
            messagebox.showerror("Error", f"Failed to load form data:\n{str(e)[:150]}")
    
    def _on_vehicle_selected(self, event=None):
        """Handle vehicle selection"""
        selected_idx = self.vehicle_combo.current()
        if selected_idx >= 0 and self.vehicles_data:
            vehicle = self.vehicles_data[selected_idx]
            vehicle_info = (
                f"🚚 {vehicle['Model']}\n"
                f"Year: {vehicle['Year']}\n"
                f"Miles: {vehicle['Miles']}\n"
                f"Area: {vehicle['Area']}"
            )
            self.vehicle_info_label.config(text=vehicle_info)
        
        self._update_summary()
    
    def _update_summary(self):
        """Update summary panel"""
        # Update stores count
        selected_stores = self.stores_listbox.curselection()
        stores_count = len(selected_stores)
        self.stores_count_label.config(
            text=f"{stores_count} store{'s' if stores_count != 1 else ''} selected"
        )
        
        # Update time estimates
        try:
            # Simple dynamic estimate: 30 min base + 15 min per store
            base_pickup = 30
            per_store_delivery = 15
            
            pickup_time = base_pickup
            delivery_time = stores_count * per_store_delivery
            
            # Update entries if they haven't been manually edited (simple check)
            # For now, just update the label to show the calculated estimate
            
            total_time = pickup_time + delivery_time
            
            self.time_estimate_label.config(
                text=f"Total: {total_time} minutes\nPickup: {pickup_time} min | Delivery: {delivery_time} min"
            )
            
            # Also update the entry fields with these estimates
            self.pickup_time_entry.delete(0, tk.END)
            self.pickup_time_entry.insert(0, str(pickup_time))
            self.delivery_time_entry.delete(0, tk.END)
            self.delivery_time_entry.insert(0, str(delivery_time))
            
        except ValueError:
            self.time_estimate_label.config(
                text="Invalid time values"
            )
    
    def _clear_form(self):
        """Clear all form fields"""
        if messagebox.askyesno("Clear Form", "Are you sure you want to clear all fields?"):
            self.order_id_entry.delete(0, tk.END)
            self.vehicle_var.set("")
            self.vehicle_info_label.config(text="No vehicle selected")
            self.stores_listbox.selection_clear(0, tk.END)
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
            
            selected_stores = self.stores_listbox.curselection()
            if not selected_stores:
                messagebox.showwarning("Validation Error", "Please select at least one delivery store")
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
            
            # Get vehicle ID
            vehicle = self.vehicles_data[vehicle_idx]
            vehicle_id = vehicle['VehicleID']
            
            # Insert into DeliveryLog
            # Note: Order_ID is nvarchar, so it needs quotes
            # Note: Order_Time is required, so we provide a default value
            # Note: Status is 'Pending' initially
            # Note: Pickup_Time and Delivery_Time are NOT NULL
            
            current_dt = datetime.now()
            current_time_str = current_dt.strftime("%H:%M:%S")
            
            # Calculate estimated pickup time (Time of day)
            # Assuming pickup_time input is minutes from now
            est_pickup_dt = current_dt + timedelta(minutes=pickup_time)
            est_pickup_str = est_pickup_dt.strftime("%H:%M:%S")
            
            # Delivery_Time is smallint (duration in minutes)
            # We use the input delivery_time directly
            
            for i, store_idx in enumerate(selected_stores):
                store = self.stores_data[store_idx]
                store_id = store['StoreID']
                
                # Append suffix to Order ID for multiple stores if needed
                final_order_id = f"{order_id}-{i+1}" if len(selected_stores) > 1 else order_id
                
                self.repo.execute(f"""
                    INSERT INTO DeliveryLog (
                        Order_ID, VehicleID, Order_Date, Order_Time, 
                        Pickup_Time, Delivery_Time, StoreID, Status
                    )
                    VALUES (
                        '{final_order_id}', 
                        {vehicle_id}, 
                        '{order_date}', 
                        '{current_time_str}', 
                        '{est_pickup_str}',
                        {delivery_time},
                        {store_id},
                        'Pending'
                    )
                """)
            
            messagebox.showinfo(
                "Success", 
                f"Route created successfully!\n\n"
                f"Order ID: {order_id}\n"
                f"Vehicle: {vehicle_id}\n"
                f"Stores: {len(selected_stores)}\n"
                f"Est. Time: {pickup_time + delivery_time} min"
            )
            
            logging.info(f"Route created: Order {order_id}, Vehicle {vehicle_id}, {len(selected_stores)} stores")
            
            # Clear form after successful creation
            self._clear_form()
            
        except Exception as e:
            logging.error(f"Error creating route: {e}")
            messagebox.showerror("Error", f"Failed to create route:\n{str(e)[:200]}")
    
    def _optimize_route(self):
        """Suggest best vehicle and time estimates based on historical data"""
        selected_stores_indices = self.stores_listbox.curselection()
        if not selected_stores_indices:
            messagebox.showinfo("Optimization", "Please select delivery stores first to get recommendations.")
            return
            
        try:
            store_ids = [str(self.stores_data[i]['StoreID']) for i in selected_stores_indices]
            store_ids_str = ",".join(store_ids)
            
            # 1. Find best vehicle (lowest avg delivery time for these stores)
            best_vehicle_query = f"""
                SELECT TOP 1 VehicleID, AVG(Delivery_Time) as AvgTime
                FROM DeliveryLog
                WHERE StoreID IN ({store_ids_str})
                AND Status = 'Delivered'
                AND Delivery_Time > 0
                GROUP BY VehicleID
                ORDER BY AvgTime ASC
            """
            best_vehicle = self.repo.fetch_all(best_vehicle_query)
            
            vehicle_found = False
            if best_vehicle:
                best_vehicle_id = best_vehicle[0]['VehicleID']
                # Find index in combo
                for i, v in enumerate(self.vehicles_data):
                    if v['VehicleID'] == best_vehicle_id:
                        self.vehicle_combo.current(i)
                        self._on_vehicle_selected(None)
                        vehicle_found = True
                        break
            
            # 2. Estimate delivery time based on historical average
            avg_time_query = f"""
                SELECT AVG(Delivery_Time) as AvgTime
                FROM DeliveryLog
                WHERE StoreID IN ({store_ids_str})
                AND Status = 'Delivered'
                AND Delivery_Time > 0
            """
            avg_time_result = self.repo.fetch_all(avg_time_query)
            
            msg = "Route Optimized!\n\n"
            if vehicle_found:
                msg += "• Selected best performing vehicle based on history\n"
            else:
                msg += "• No specific vehicle data found for these stores\n"

            if avg_time_result and avg_time_result[0]['AvgTime']:
                estimated_time = int(avg_time_result[0]['AvgTime'])
                # Update delivery time entry
                self.delivery_time_entry.delete(0, tk.END)
                self.delivery_time_entry.insert(0, str(estimated_time))
                msg += f"• Updated delivery time estimate to {estimated_time} min (historical average)"
            else:
                msg += "• No historical time data available for estimates"
                
            messagebox.showinfo("Optimization Complete", msg)
                
        except Exception as e:
            logging.error(f"Optimization error: {e}")
            messagebox.showerror("Error", f"Optimization failed: {e}")

    def destroy(self):
        """Clean up resources"""
        if self.repo:
            try:
                self.repo.close()
                logging.info("New routes repository connection closed")
            except Exception as e:
                logging.error(f"Error closing repository: {e}")
        super().destroy()