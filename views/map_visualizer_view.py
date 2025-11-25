"""
Map Visualizer View - Interactive route and delivery mapping
Shows actual delivery routes from Stores (origin) to Drop Locations (destination)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import os
import math
import threading

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from ui_components import MetricCard, SectionHeader
from backend.repository import AzureSqlRepository
from datetime import datetime

# Try to import map widget
try:
    import tkintermapview
    MAP_AVAILABLE = True
except ImportError:
    MAP_AVAILABLE = False
    logging.warning("tkintermapview not installed. Map features will be limited.")

# Try to import requests for routing
try:
    import requests
    ROUTING_AVAILABLE = True
except ImportError:
    ROUTING_AVAILABLE = False
    logging.warning("requests not installed. Realistic routing will be unavailable.")


class MapVisualizerView(tk.Frame):
    """Map Visualizer - Interactive route and delivery mapping with Store -> Drop Location routes"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.map_widget = None
        self.markers = []
        self.paths = []
        
        # Filter states
        self.show_stores = tk.BooleanVar(value=True)
        self.show_drop_locations = tk.BooleanVar(value=False)  # Off by default (too many)
        
        # Data storage
        self.stores_data = []
        self.completed_routes = []  # Actual delivery routes from DB
        self.selected_route = None
        
        # Route visualization
        self.route_marker_origin = None
        self.route_marker_dest = None
        self.selected_route_path = None
        self.loading_label = None
        
        self._create_ui()
        
        if MAP_AVAILABLE:
            self.after(100, self._load_initial_data)
        else:
            self._show_installation_instructions()
    
    def _create_ui(self):
        """Create map visualization UI"""
        content = tk.Frame(self, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        # Header with controls
        self._create_header(content)
        
        # Completed Routes Panel (replaces old route planner)
        self._create_completed_routes_panel(content)
        
        # Map container
        map_container = tk.Frame(content, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        map_container.pack(fill="both", expand=True, pady=(config.PADDING_MEDIUM, 0))
        
        if MAP_AVAILABLE:
            self._create_map_widget(map_container)
        else:
            self._create_placeholder(map_container)
        
        # Legend
        self._create_legend(content)
    
    def _create_header(self, parent):
        """Create header with title and controls"""
        header_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Delivery Route Map",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, 
            fg=config.TEXT_PRIMARY
        )
        title_label.pack(side="left")
        
        # Subtitle
        subtitle = tk.Label(
            header_frame,
            text="View completed delivery routes (Store -> Drop Location)",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_SECONDARY
        )
        subtitle.pack(side="left", padx=(15, 0))
        
        # Controls frame
        controls_frame = tk.Frame(header_frame, bg=config.BG_LIGHT)
        controls_frame.pack(side="right")
        
        # Show Stores checkbox
        tk.Checkbutton(
            controls_frame, 
            text="Show Stores", 
            variable=self.show_stores,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL), 
            bg=config.BG_LIGHT,
            command=self._update_map_display
        ).pack(side="left", padx=5)
        
        # Refresh button
        tk.Button(
            controls_frame,
            text="Refresh",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._load_initial_data
        ).pack(side="left", padx=5)
    
    def _create_completed_routes_panel(self, parent):
        """Create panel for viewing completed delivery routes"""
        panel_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        panel_frame.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        # Main panel content
        panel_content = tk.Frame(panel_frame, bg=config.BG_WHITE)
        panel_content.pack(padx=15, pady=10, fill="x")
        
        # Row 1: Title and Load button
        row1 = tk.Frame(panel_content, bg=config.BG_WHITE)
        row1.pack(fill="x", pady=(0, 8))
        
        tk.Label(
            row1,
            text="Completed Delivery Routes",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left")
        
        # Stats label
        self.stats_label = tk.Label(
            row1,
            text="",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        self.stats_label.pack(side="left", padx=(15, 0))
        
        tk.Button(
            row1,
            text="Load Routes from DB",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._load_completed_routes
        ).pack(side="right")
        
        # Row 2: Filter controls
        row2 = tk.Frame(panel_content, bg=config.BG_WHITE)
        row2.pack(fill="x", pady=(0, 8))
        
        # Filter by Store
        tk.Label(
            row2,
            text="Filter by Store:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        self.filter_store_var = tk.StringVar(value="All Stores")
        self.filter_store_combo = ttk.Combobox(
            row2,
            textvariable=self.filter_store_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            width=12
        )
        self.filter_store_combo['values'] = ["All Stores"]
        self.filter_store_combo.pack(side="left", padx=(0, 15))
        self.filter_store_combo.bind("<<ComboboxSelected>>", lambda e: self._filter_routes())
        
        # Limit results
        tk.Label(
            row2,
            text="Show:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        self.limit_var = tk.StringVar(value="50")
        limit_combo = ttk.Combobox(
            row2,
            textvariable=self.limit_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            width=6,
            values=["25", "50", "100", "200"]
        )
        limit_combo.pack(side="left", padx=(0, 15))
        
        # Apply filter button
        tk.Button(
            row2,
            text="Apply Filter",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_PRIMARY,
            activebackground="#E0E0E0",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._load_completed_routes
        ).pack(side="left", padx=5)
        
        # Row 3: Route selection
        row3 = tk.Frame(panel_content, bg=config.BG_WHITE)
        row3.pack(fill="x")
        
        tk.Label(
            row3,
            text="Select Route:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        self.route_var = tk.StringVar()
        self.route_combo = ttk.Combobox(
            row3,
            textvariable=self.route_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            width=60
        )
        self.route_combo.pack(side="left", padx=(0, 10))
        self.route_combo.bind("<<ComboboxSelected>>", self._on_route_selected)
        
        # Show on Map button
        tk.Button(
            row3,
            text="Show on Map",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#388E3C",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=3,
            command=self._show_route_on_map
        ).pack(side="left", padx=5)
        
        # Show All Routes for Store
        tk.Button(
            row3,
            text="Show All for Store",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=3,
            command=self._show_all_routes_for_store
        ).pack(side="left", padx=5)
        
        # Clear button
        tk.Button(
            row3,
            text="Clear Map",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_PRIMARY,
            activebackground="#E0E0E0",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._clear_route_display
        ).pack(side="left", padx=5)
        
        # Route info label
        self.route_info_label = tk.Label(
            row3,
            text="",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        self.route_info_label.pack(side="left", padx=(15, 0))
    
    def _create_map_widget(self, parent):
        """Create the interactive map widget"""
        try:
            self.map_widget = tkintermapview.TkinterMapView(
                parent, 
                width=800, 
                height=500,
                corner_radius=0
            )
            self.map_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Set initial position (center of India)
            self.map_widget.set_position(20.5937, 78.9629)
            self.map_widget.set_zoom(5)
            
            # Set tile server
            self.map_widget.set_tile_server(
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                max_zoom=19
            )
            
            # Loading indicator
            self.loading_label = tk.Label(
                self.map_widget,
                text="Loading...",
                font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
                bg="white",
                fg=config.PRIMARY_COLOR,
                padx=20,
                pady=10,
                relief="solid",
                borderwidth=2
            )
            
            logging.info("Map widget created successfully")
            
        except Exception as e:
            logging.error(f"Error creating map widget: {e}")
            self._create_placeholder(parent)
    
    def _create_placeholder(self, parent):
        """Create placeholder when map is not available"""
        placeholder_frame = tk.Frame(parent, bg=config.BG_WHITE)
        placeholder_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(
            placeholder_frame,
            text="Map Visualization",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(pady=(50, 10))
        
        tk.Label(
            placeholder_frame,
            text="Install required packages to enable interactive maps:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(pady=5)
        
        tk.Label(
            placeholder_frame,
            text="pip install tkintermapview requests",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#F0F0F0",
            fg=config.PRIMARY_COLOR,
            padx=20,
            pady=10,
            relief="solid",
            borderwidth=1
        ).pack(pady=20)
    
    def _create_legend(self, parent):
        """Create map legend"""
        legend_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        legend_frame.pack(fill="x", pady=(config.PADDING_MEDIUM, 0))
        
        legend_content = tk.Frame(legend_frame, bg=config.BG_WHITE)
        legend_content.pack(padx=20, pady=10)
        
        tk.Label(
            legend_content,
            text="Legend:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left", padx=(0, 15))
        
        # Store marker (origin)
        self._create_legend_item(legend_content, "S", "Store (Origin)", "#4CAF50")
        
        # Drop Location marker (destination)
        self._create_legend_item(legend_content, "D", "Drop Location (Dest)", "#F44336")
        
        # Route path
        self._create_legend_item(legend_content, "-", "Delivery Route", "#E91E63")
        
        # Multiple routes
        self._create_legend_item(legend_content, "-", "Store Routes", "#2196F3")
    
    def _create_legend_item(self, parent, icon, label, color):
        """Create a legend item"""
        item_frame = tk.Frame(parent, bg=config.BG_WHITE)
        item_frame.pack(side="left", padx=10)
        
        tk.Label(
            item_frame,
            text=icon,
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=color
        ).pack(side="left", padx=(0, 5))
        
        tk.Label(
            item_frame,
            text=label,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left")
    
    # ============================================
    # DATA LOADING METHODS
    # ============================================
    
    def _load_initial_data(self):
        """Load initial data in background"""
        if not MAP_AVAILABLE or not self.map_widget:
            return
        
        if self.loading_label:
            self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        thread = threading.Thread(target=self._load_stores_and_stats, daemon=True)
        thread.start()
    
    def _load_stores_and_stats(self):
        """Load stores and basic stats from database"""
        try:
            if not self.repo:
                self.repo = AzureSqlRepository()
            
            # Load stores
            stores = self.repo.fetch_all("""
                SELECT StoreID, lat AS Latitude, lon AS Longitude
                FROM Stores
                WHERE lat BETWEEN 8 AND 37 AND lon BETWEEN 68 AND 97
                ORDER BY StoreID
            """)
            
            self.stores_data = stores if stores else []
            
            # Get stats
            stats = self.repo.fetch_all("""
                SELECT 
                    COUNT(DISTINCT StoreID) AS TotalStores,
                    COUNT(DISTINCT DropLocationID) AS TotalDrops,
                    COUNT(*) AS TotalDeliveries
                FROM DeliveryLog
                WHERE Delivery_Time IS NOT NULL AND Delivery_Time > 0
            """)
            
            # Update UI on main thread
            self.after(0, lambda: self._update_initial_ui(stores, stats))
            
        except Exception as e:
            logging.error(f"Error loading initial data: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to load data:\n{str(e)[:150]}"))
        finally:
            self.after(0, self._hide_loading)
    
    def _update_initial_ui(self, stores, stats):
        """Update UI with initial data"""
        # Populate store filter dropdown
        store_options = ["All Stores"] + [f"Store {s['StoreID']}" for s in stores]
        self.filter_store_combo['values'] = store_options
        
        # Update stats label
        if stats and len(stats) > 0:
            s = stats[0]
            self.stats_label.config(
                text=f"{s['TotalStores']} stores | {s['TotalDrops']} drop locations | {s['TotalDeliveries']} completed deliveries"
            )
        
        # Plot stores if enabled
        if self.show_stores.get() and stores:
            self._plot_stores(stores)
        
        logging.info(f"Loaded {len(stores)} stores")
    
    def _load_completed_routes(self):
        """Load completed delivery routes from database"""
        try:
            if not self.repo:
                self.repo = AzureSqlRepository()
            
            # Get filter values
            store_filter = self.filter_store_var.get()
            limit = int(self.limit_var.get())
            
            # Build query with proper joins to get Store and DropLocation coordinates
            store_condition = ""
            if store_filter != "All Stores":
                store_id = int(store_filter.replace("Store ", ""))
                store_condition = f"AND dl.StoreID = {store_id}"
            
            routes = self.repo.fetch_all(f"""
                SELECT TOP {limit}
                    dl.Order_ID,
                    dl.StoreID,
                    dl.DropLocationID,
                    dl.VehicleID,
                    dl.Delivery_Time,
                    dl.Order_Date,
                    CAST(dl.Order_Time AS VARCHAR(8)) AS Order_Time,
                    s.lat AS Store_Lat,
                    s.lon AS Store_Lon,
                    d.lat AS Drop_Lat,
                    d.lon AS Drop_Lon
                FROM DeliveryLog dl
                INNER JOIN Stores s ON dl.StoreID = s.StoreID
                INNER JOIN DropLocations d ON dl.DropLocationID = d.DropLocationID
                WHERE dl.Delivery_Time IS NOT NULL
                  AND dl.Delivery_Time > 0
                  AND dl.Delivery_Time BETWEEN 20 AND 400
                  AND s.lat BETWEEN 8 AND 37 AND s.lon BETWEEN 68 AND 97
                  AND d.lat BETWEEN 8 AND 37 AND d.lon BETWEEN 68 AND 97
                  {store_condition}
                ORDER BY dl.Order_Date DESC, dl.Order_Time DESC
            """)
            
            if not routes:
                messagebox.showinfo("No Data", "No completed routes found with the current filter.")
                return
            
            self.completed_routes = routes
            
            # Populate route dropdown
            route_options = []
            for r in routes:
                date_str = str(r['Order_Date'])[:10] if r['Order_Date'] else 'N/A'
                display = f"Order {r['Order_ID']} | Store {r['StoreID']} -> Drop {r['DropLocationID']} | {r['Delivery_Time']}min | {date_str}"
                route_options.append(display)
            
            self.route_combo['values'] = route_options
            self.route_info_label.config(text=f"Loaded {len(routes)} routes")
            
            logging.info(f"Loaded {len(routes)} completed routes")
            
        except Exception as e:
            logging.error(f"Error loading completed routes: {e}")
            messagebox.showerror("Error", f"Failed to load routes:\n{str(e)[:150]}")
    
    def _filter_routes(self):
        """Filter routes based on selection"""
        self._load_completed_routes()
    
    # ============================================
    # MAP DISPLAY METHODS
    # ============================================
    
    def _plot_stores(self, stores):
        """Plot store locations on map"""
        if not stores or not self.map_widget:
            return
        
        for store in stores:
            if store.get('Latitude') and store.get('Longitude'):
                try:
                    marker = self.map_widget.set_marker(
                        float(store['Latitude']),
                        float(store['Longitude']),
                        text=str(store['StoreID']),
                        marker_color_circle="#4CAF50",
                        marker_color_outside="#1B5E20",
                        text_color="#000000",
                        font=("Arial", 9, "bold")
                    )
                    self.markers.append(marker)
                except Exception as e:
                    logging.warning(f"Could not plot store {store['StoreID']}: {e}")
        
        logging.info(f"Plotted {len(self.markers)} store markers")
    
    def _on_route_selected(self, event):
        """Handle route selection from dropdown"""
        selection = self.route_var.get()
        if not selection:
            return
        
        try:
            # Parse order ID from selection
            order_id = selection.split("|")[0].replace("Order", "").strip()
            self.selected_route = next(
                (r for r in self.completed_routes if str(r['Order_ID']).strip() == order_id),
                None
            )
            
            if self.selected_route:
                r = self.selected_route
                distance = self._haversine_distance(
                    r['Store_Lat'], r['Store_Lon'],
                    r['Drop_Lat'], r['Drop_Lon']
                )
                self.route_info_label.config(
                    text=f"Store {r['StoreID']} -> Drop {r['DropLocationID']} | ~{distance:.1f}km | {r['Delivery_Time']}min"
                )
        except Exception as e:
            logging.warning(f"Error parsing route selection: {e}")
    
    def _show_route_on_map(self):
        """Display selected route on map"""
        if not self.selected_route:
            messagebox.showwarning("No Selection", "Please select a route first")
            return
        
        if not MAP_AVAILABLE or not self.map_widget:
            return
        
        try:
            r = self.selected_route
            
            # Clear previous route display
            self._clear_route_display()
            
            # Plot Store (Origin) marker - Green
            self.route_marker_origin = self.map_widget.set_marker(
                float(r['Store_Lat']),
                float(r['Store_Lon']),
                text=f"S{r['StoreID']}",
                marker_color_circle="#4CAF50",
                marker_color_outside="#1B5E20",
                text_color="#FFFFFF",
                font=("Arial", 12, "bold")
            )
            
            # Plot Drop Location (Destination) marker - Red
            self.route_marker_dest = self.map_widget.set_marker(
                float(r['Drop_Lat']),
                float(r['Drop_Lon']),
                text=f"D{r['DropLocationID']}",
                marker_color_circle="#F44336",
                marker_color_outside="#B71C1C",
                text_color="#FFFFFF",
                font=("Arial", 12, "bold")
            )
            
            # Draw route path - fetch realistic route in background
            self.route_info_label.config(text="Fetching route...")
            
            threading.Thread(
                target=self._fetch_and_draw_route,
                args=(r,),
                daemon=True
            ).start()
            
        except Exception as e:
            logging.error(f"Error showing route on map: {e}")
            messagebox.showerror("Error", f"Failed to display route:\n{str(e)}")
    
    def _fetch_and_draw_route(self, route):
        """Fetch realistic route and draw it"""
        try:
            route_coords = self._get_route_coordinates(
                route['Store_Lat'], route['Store_Lon'],
                route['Drop_Lat'], route['Drop_Lon']
            )
            
            if not route_coords or len(route_coords) < 2:
                route_coords = [
                    (float(route['Store_Lat']), float(route['Store_Lon'])),
                    (float(route['Drop_Lat']), float(route['Drop_Lon']))
                ]
            
            distance = self._calculate_route_distance(route_coords)
            
            # Draw on main thread
            self.after(0, lambda: self._draw_route_path(route, route_coords, distance))
            
        except Exception as e:
            logging.error(f"Error fetching route: {e}")
            self.after(0, lambda: self.route_info_label.config(text="Error fetching route"))
    
    def _draw_route_path(self, route, route_coords, distance):
        """Draw the route path on map"""
        try:
            # Draw path
            self.selected_route_path = self.map_widget.set_path(
                route_coords,
                color="#E91E63",
                width=4
            )
            
            # Update info label
            self.route_info_label.config(
                text=f"Store {route['StoreID']} -> Drop {route['DropLocationID']} | {distance:.1f}km | {route['Delivery_Time']}min"
            )
            
            # Center map on route
            center_lat = (float(route['Store_Lat']) + float(route['Drop_Lat'])) / 2
            center_lon = (float(route['Store_Lon']) + float(route['Drop_Lon'])) / 2
            self.map_widget.set_position(center_lat, center_lon)
            
            # Auto-zoom
            self._fit_route_to_view(distance)
            
            logging.info(f"Displayed route: Store {route['StoreID']} -> Drop {route['DropLocationID']}")
            
        except Exception as e:
            logging.error(f"Error drawing route path: {e}")
    
    def _show_all_routes_for_store(self):
        """Show all routes originating from the selected store"""
        store_filter = self.filter_store_var.get()
        
        if store_filter == "All Stores":
            messagebox.showwarning("Select Store", "Please select a specific store from the filter first")
            return
        
        if not self.completed_routes:
            messagebox.showwarning("No Data", "Please load routes first")
            return
        
        if not MAP_AVAILABLE or not self.map_widget:
            return
        
        try:
            store_id = int(store_filter.replace("Store ", ""))
            
            # Filter routes for this store
            store_routes = [r for r in self.completed_routes if r['StoreID'] == store_id]
            
            if not store_routes:
                messagebox.showinfo("No Routes", f"No routes found for Store {store_id}")
                return
            
            # Clear previous display
            self._clear_route_display()
            
            # Get store coordinates
            store = store_routes[0]
            store_lat = float(store['Store_Lat'])
            store_lon = float(store['Store_Lon'])
            
            # Plot store marker
            self.route_marker_origin = self.map_widget.set_marker(
                store_lat, store_lon,
                text=f"S{store_id}",
                marker_color_circle="#4CAF50",
                marker_color_outside="#1B5E20",
                text_color="#FFFFFF",
                font=("Arial", 14, "bold")
            )
            
            # Plot routes to all drop locations (limit to 50 for performance)
            plotted = 0
            for r in store_routes[:50]:
                try:
                    # Draw straight line for performance (many routes)
                    path = self.map_widget.set_path(
                        [
                            (store_lat, store_lon),
                            (float(r['Drop_Lat']), float(r['Drop_Lon']))
                        ],
                        color="#2196F3",
                        width=2
                    )
                    self.paths.append(path)
                    plotted += 1
                except Exception as e:
                    logging.warning(f"Could not plot route: {e}")
            
            # Center on store
            self.map_widget.set_position(store_lat, store_lon)
            self.map_widget.set_zoom(9)
            
            self.route_info_label.config(
                text=f"Showing {plotted} routes from Store {store_id}"
            )
            
            logging.info(f"Displayed {plotted} routes for Store {store_id}")
            
        except Exception as e:
            logging.error(f"Error showing all routes for store: {e}")
            messagebox.showerror("Error", f"Failed to display routes:\n{str(e)}")
    
    def _clear_route_display(self):
        """Clear route markers and paths"""
        try:
            if self.route_marker_origin:
                self.route_marker_origin.delete()
                self.route_marker_origin = None
            
            if self.route_marker_dest:
                self.route_marker_dest.delete()
                self.route_marker_dest = None
            
            if self.selected_route_path:
                self.selected_route_path.delete()
                self.selected_route_path = None
            
            for path in self.paths:
                path.delete()
            self.paths.clear()
            
            self.route_info_label.config(text="")
            
        except Exception as e:
            logging.warning(f"Error clearing route display: {e}")
    
    def _update_map_display(self):
        """Update map display based on checkboxes"""
        self._clear_map()
        
        if self.show_stores.get() and self.stores_data:
            self._plot_stores(self.stores_data)
    
    def _clear_map(self):
        """Clear all markers from map"""
        try:
            for marker in self.markers:
                marker.delete()
            self.markers.clear()
            
            self._clear_route_display()
            
        except Exception as e:
            logging.warning(f"Error clearing map: {e}")
    
    def _hide_loading(self):
        """Hide loading indicator"""
        if self.loading_label:
            self.loading_label.place_forget()
    
    # ============================================
    # ROUTING UTILITIES
    # ============================================
    
    def _get_route_coordinates(self, lat1, lon1, lat2, lon2):
        """Fetch realistic route coordinates using OSRM"""
        if not ROUTING_AVAILABLE:
            return None
        
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
            params = {"overview": "full", "geometries": "geojson"}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok' and data.get('routes'):
                    coordinates = data['routes'][0]['geometry']['coordinates']
                    return [(coord[1], coord[0]) for coord in coordinates]
            
            return None
            
        except Exception as e:
            logging.warning(f"OSRM routing error: {e}")
            return None
    
    def _calculate_route_distance(self, route_coords):
        """Calculate total distance along the route"""
        if not route_coords or len(route_coords) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(route_coords) - 1):
            lat1, lon1 = route_coords[i]
            lat2, lon2 = route_coords[i + 1]
            total_distance += self._haversine_distance(lat1, lon1, lat2, lon2)
        
        return total_distance
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in km"""
        R = 6371.0
        
        lat1_rad = math.radians(float(lat1))
        lon1_rad = math.radians(float(lon1))
        lat2_rad = math.radians(float(lat2))
        lon2_rad = math.radians(float(lon2))
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _fit_route_to_view(self, distance_km):
        """Auto-zoom map to fit the route"""
        try:
            if distance_km < 20:
                zoom = 11
            elif distance_km < 50:
                zoom = 10
            elif distance_km < 100:
                zoom = 9
            elif distance_km < 200:
                zoom = 8
            elif distance_km < 500:
                zoom = 7
            else:
                zoom = 6
            
            self.map_widget.set_zoom(zoom)
        except Exception as e:
            logging.warning(f"Could not auto-zoom: {e}")
    
    def _show_installation_instructions(self):
        """Show installation instructions"""
        messagebox.showinfo(
            "Map Feature Unavailable",
            "Install required packages:\n\n"
            "pip install tkintermapview requests\n\n"
            "Then restart the application."
        )
    
    def destroy(self):
        """Clean up resources"""
        if self.repo:
            try:
                self.repo.close()
            except Exception as e:
                logging.error(f"Error closing repository: {e}")
        super().destroy()
