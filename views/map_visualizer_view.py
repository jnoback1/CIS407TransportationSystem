"""
Map Visualizer View - Interactive route and delivery mapping
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
    """Map Visualizer - Interactive route and delivery mapping"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.map_widget = None
        self.markers = []
        self.paths = []
        
        # Filter states
        self.show_stores = tk.BooleanVar(value=True)
        self.show_vehicles = tk.BooleanVar(value=False)
        self.show_routes = tk.BooleanVar(value=False)  # Default OFF for performance
        
        # Route planning variables
        self.stores_data = []
        self.route_marker_a = None
        self.route_marker_b = None
        self.selected_route_path = None
        self.loading_label = None
        
        self._create_ui()
        
        if MAP_AVAILABLE:
            # Load map data in background to prevent UI blocking
            self.after(100, self._load_map_data_async)
        else:
            self._show_installation_instructions()
    
    def _create_ui(self):
        """Create map visualization UI"""
        content = tk.Frame(self, bg=config.BG_LIGHT)
        content.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        # Header with controls
        self._create_header(content)
        
        # Route planner panel
        self._create_route_planner_panel(content)
        
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
            text="🗺️ Route Map Visualizer",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, 
            fg=config.TEXT_PRIMARY
        )
        title_label.pack(side="left")
        
        # Controls frame
        controls_frame = tk.Frame(header_frame, bg=config.BG_LIGHT)
        controls_frame.pack(side="right")
        
        # Only keep "Show Stores" checkbox
        tk.Checkbutton(
            controls_frame, 
            text="Show Stores", 
            variable=self.show_stores,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL), 
            bg=config.BG_LIGHT,
            command=self._update_map_filters
        ).pack(side="left", padx=5)
        
        # Refresh button
        tk.Button(
            controls_frame,
            text="🔄 Refresh",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._load_map_data_async
        ).pack(side="left", padx=5)
    
    def _create_route_planner_panel(self, parent):
        """Create route planner controls panel"""
        panel_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        panel_frame.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        panel_content = tk.Frame(panel_frame, bg=config.BG_WHITE)
        panel_content.pack(padx=15, pady=10)
        
        # Title
        tk.Label(
            panel_content,
            text="🛣️ Route Planner - Select Route to Highlight",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left", padx=(0, 20))
        
        # Store A selection
        tk.Label(
            panel_content,
            text="Origin:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        self.store_a_var = tk.StringVar()
        self.store_a_combo = ttk.Combobox(
            panel_content,
            textvariable=self.store_a_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            width=15
        )
        self.store_a_combo.pack(side="left", padx=(0, 15))
        
        # Store B selection
        tk.Label(
            panel_content,
            text="Destination:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        self.store_b_var = tk.StringVar()
        self.store_b_combo = ttk.Combobox(
            panel_content,
            textvariable=self.store_b_var,
            state="readonly",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            width=15
        )
        self.store_b_combo.pack(side="left", padx=(0, 15))
        
        # Show Route button
        tk.Button(
            panel_content,
            text="🚗 Highlight Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL, "bold"),
            bg=config.PRIMARY_COLOR,
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self._highlight_selected_route
        ).pack(side="left", padx=5)
        
        # Clear Route button
        tk.Button(
            panel_content,
            text="🗑️ Clear Highlight",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_PRIMARY,
            activebackground="#E0E0E0",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self._clear_selected_route
        ).pack(side="left", padx=5)
        
        # Distance label
        self.route_distance_label = tk.Label(
            panel_content,
            text="",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        self.route_distance_label.pack(side="left", padx=(20, 0))
    
    def _create_map_widget(self, parent):
        """Create the interactive map widget"""
        try:
            # Create map widget
            self.map_widget = tkintermapview.TkinterMapView(
                parent, 
                width=800, 
                height=600,
                corner_radius=0
            )
            self.map_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Set initial position (center of India)
            self.map_widget.set_position(20.5937, 78.9629)
            self.map_widget.set_zoom(5)
            
            # Set tile server (OpenStreetMap)
            self.map_widget.set_tile_server(
                "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                max_zoom=19
            )
            
            # Create loading indicator
            self.loading_label = tk.Label(
                self.map_widget,
                text="⏳ Loading map data...",
                font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
                bg="white",
                fg=config.PRIMARY_COLOR,
                padx=20,
                pady=10,
                relief="solid",
                borderwidth=2
            )
            
            logging.info("Map widget created successfully - centered on India")
            
        except Exception as e:
            logging.error(f"Error creating map widget: {e}")
            self._create_placeholder(parent)
    
    def _create_placeholder(self, parent):
        """Create placeholder when map is not available"""
        placeholder_frame = tk.Frame(parent, bg=config.BG_WHITE)
        placeholder_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(
            placeholder_frame,
            text="🗺️",
            font=(config.FONT_FAMILY, 72),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(pady=(50, 20))
        
        tk.Label(
            placeholder_frame,
            text="Map Visualization",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(pady=10)
        
        tk.Label(
            placeholder_frame,
            text="Install required packages to enable interactive maps:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        ).pack(pady=5)
        
        command_label = tk.Label(
            placeholder_frame,
            text="pip install tkintermapview requests",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#F0F0F0",
            fg=config.PRIMARY_COLOR,
            padx=20,
            pady=10,
            relief="solid",
            borderwidth=1
        )
        command_label.pack(pady=20)
    
    def _create_legend(self, parent):
        """Create map legend"""
        legend_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        legend_frame.pack(fill="x", pady=(config.PADDING_MEDIUM, 0))
        
        legend_content = tk.Frame(legend_frame, bg=config.BG_WHITE)
        legend_content.pack(padx=20, pady=15)
        
        tk.Label(
            legend_content,
            text="Legend:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left", padx=(0, 15))
        
        # Store marker
        self._create_legend_item(legend_content, "🏪", "Stores", "#4CAF50")
        
        # Selected/highlighted route
        self._create_legend_item(legend_content, "━", "Highlighted Route", "#E91E63")
        
        # Vehicle marker
        self._create_legend_item(legend_content, "🚚", "Vehicles", "#2196F3")
    
    def _create_legend_item(self, parent, icon, label, color):
        """Create a legend item"""
        item_frame = tk.Frame(parent, bg=config.BG_WHITE)
        item_frame.pack(side="left", padx=10)
        
        tk.Label(
            item_frame,
            text=icon,
            font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE),
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
    
    def _load_map_data_async(self):
        """Load map data in background thread to prevent UI freezing"""
        if not MAP_AVAILABLE or not self.map_widget:
            return
        
        # Show loading indicator
        if self.loading_label:
            self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Run data loading in background thread
        thread = threading.Thread(target=self._load_map_data, daemon=True)
        thread.start()
    
    def _load_map_data(self):
        """Load store and route locations from database"""
        try:
            self.repo = AzureSqlRepository()
            
            # Load stores - this is fast
            stores = self._load_stores()
            
            # Schedule UI update on main thread
            self.after(0, lambda: self._update_map_ui(stores))
            
        except Exception as e:
            logging.error(f"Error loading map data: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to load map data:\n{str(e)[:150]}"))
            self.after(0, self._hide_loading)
    
    def _update_map_ui(self, stores):
        """Update map UI with loaded data (runs on main thread)"""
        try:
            # Clear existing markers and paths
            self._clear_map(keep_selected=True)
            
            # Store data for route planner
            self.stores_data = stores
            
            # Populate store dropdowns
            self._populate_store_dropdowns()
            
            # Plot stores (fast)
            if self.show_stores.get() and stores:
                self._plot_stores(stores)
            
            # Only load routes if checkbox is enabled (performance optimization)
            if self.show_routes.get():
                # Load and plot routes in background
                threading.Thread(target=self._load_and_plot_routes, daemon=True).start()
            
            # Only load vehicles if checkbox is enabled
            if self.show_vehicles.get():
                active_vehicles = self._load_active_vehicles()
                if active_vehicles:
                    self._plot_vehicles(active_vehicles)
            
            logging.info(f"Map loaded: {len(stores)} stores")
            
        finally:
            self._hide_loading()
    
    def _hide_loading(self):
        """Hide loading indicator"""
        if self.loading_label:
            self.loading_label.place_forget()
    
    def _load_stores(self):
        """Load store locations from database - OPTIMIZED"""
        stores = self.repo.fetch_all("""
            SELECT 
                StoreID,
                lat AS Latitude,
                lon AS Longitude
            FROM Stores
            WHERE lat BETWEEN 8 AND 37
              AND lon BETWEEN 68 AND 97
              AND lat <> 0 
              AND lon <> 0
            ORDER BY StoreID
        """)
        
        logging.info(f"Loaded {len(stores) if stores else 0} valid stores")
        return stores if stores else []
    
    def _load_and_plot_routes(self):
        """Load sample routes from database - OPTIMIZED for performance"""
        try:
            # OPTIMIZED: Only load a sample of routes (e.g., 50 most recent)
            # This prevents the massive CROSS APPLY query
            routes = self.repo.fetch_all("""
                SELECT TOP 50
                    dl.Order_ID,
                    dl.VehicleID,
                    s1.lat AS Origin_Lat,
                    s1.lon AS Origin_Lon,
                    s2.lat AS Dest_Lat,
                    s2.lon AS Dest_Lon
                FROM DeliveryLog dl
                OUTER APPLY (
                    SELECT TOP 1 lat, lon 
                    FROM Stores 
                    WHERE lat BETWEEN 8 AND 37 AND lon BETWEEN 68 AND 97
                    ORDER BY NEWID()
                ) s1
                OUTER APPLY (
                    SELECT TOP 1 lat, lon 
                    FROM Stores 
                    WHERE lat BETWEEN 8 AND 37 AND lon BETWEEN 68 AND 97
                    ORDER BY NEWID()
                ) s2
                WHERE dl.Pickup_Time IS NOT NULL
                ORDER BY dl.Order_Date DESC
            """)
            
            if routes:
                # Plot on main thread
                self.after(0, lambda: self._plot_sample_routes(routes))
            
        except Exception as e:
            logging.error(f"Error loading routes: {e}")
    
    def _plot_sample_routes(self, routes):
        """Plot sample routes on map (light blue, straight lines for performance)"""
        if not routes:
            return
        
        for route in routes:
            try:
                if all([route.get('Origin_Lat'), route.get('Origin_Lon'),
                        route.get('Dest_Lat'), route.get('Dest_Lon')]):
                    
                    # Use straight lines for performance (no OSRM calls)
                    path = self.map_widget.set_path(
                        [
                            (float(route['Origin_Lat']), float(route['Origin_Lon'])),
                            (float(route['Dest_Lat']), float(route['Dest_Lon']))
                        ],
                        color="#90CAF9",  # Light blue
                        width=2
                    )
                    self.paths.append(path)
            except Exception as e:
                logging.warning(f"Could not plot route: {e}")
        
        logging.info(f"Plotted {len(self.paths)} sample routes")
    
    def _load_active_vehicles(self):
        """Load active vehicles from database"""
        vehicles = self.repo.fetch_all("""
            SELECT TOP 20
                dl.VehicleID,
                v.Model AS Vehicle_Model,
                -- Using random coordinates for demonstration
                CAST(20 + (RAND(CHECKSUM(NEWID())) * 15) AS DECIMAL(10,6)) AS Latitude,
                CAST(72 + (RAND(CHECKSUM(NEWID())) * 20) AS DECIMAL(10,6)) AS Longitude
            FROM DeliveryLog dl
            LEFT JOIN Vehicles v ON dl.VehicleID = v.VehicleID
            WHERE dl.Pickup_Time IS NOT NULL 
              AND dl.Delivery_Time IS NULL
        """)
        
        return vehicles if vehicles else []
    
    def _populate_store_dropdowns(self):
        """Populate store selection dropdowns"""
        if self.stores_data:
            store_options = [f"Store {s['StoreID']}" for s in self.stores_data]
            self.store_a_combo['values'] = store_options
            self.store_b_combo['values'] = store_options
    
    def _plot_stores(self, stores):
        """Plot store locations on map"""
        if not stores:
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
                        font=("Arial", 10, "bold")
                    )
                    self.markers.append(marker)
                except Exception as e:
                    logging.warning(f"Could not plot store {store['StoreID']}: {e}")
        
        logging.info(f"Plotted {len(self.markers)} store markers")
    
    def _plot_vehicles(self, vehicles):
        """Plot active vehicles on map"""
        for vehicle in vehicles:
            if vehicle.get('Latitude') and vehicle.get('Longitude'):
                try:
                    marker = self.map_widget.set_marker(
                        float(vehicle['Latitude']),
                        float(vehicle['Longitude']),
                        text=f"V{vehicle['VehicleID']}",
                        marker_color_circle="#2196F3",
                        marker_color_outside="#0D47A1",
                        text_color="#000000",
                        font=("Arial", 10, "bold")
                    )
                    self.markers.append(marker)
                except Exception as e:
                    logging.warning(f"Could not plot vehicle {vehicle['VehicleID']}: {e}")
    
    def _highlight_selected_route(self):
        """Highlight the selected route with realistic routing"""
        if not MAP_AVAILABLE or not self.map_widget:
            messagebox.showwarning("Map Unavailable", "Map widget is not available")
            return
        
        store_a_text = self.store_a_var.get()
        store_b_text = self.store_b_var.get()
        
        if not store_a_text or not store_b_text:
            messagebox.showwarning("Selection Required", "Please select both origin and destination stores")
            return
        
        if store_a_text == store_b_text:
            messagebox.showwarning("Invalid Selection", "Origin and destination must be different")
            return
        
        try:
            # Extract Store IDs
            store_a_id = int(store_a_text.split()[1])
            store_b_id = int(store_b_text.split()[1])
            
            # Find store data
            store_a = next((s for s in self.stores_data if s['StoreID'] == store_a_id), None)
            store_b = next((s for s in self.stores_data if s['StoreID'] == store_b_id), None)
            
            if not store_a or not store_b:
                messagebox.showerror("Error", "Could not find store coordinates")
                return
            
            # Clear previous highlighted route
            self._clear_selected_route()
            
            # Show loading message
            self.route_distance_label.config(text="⏳ Fetching route...")
            self.update_idletasks()
            
            # Get realistic route in background
            threading.Thread(
                target=self._fetch_and_plot_route,
                args=(store_a, store_b),
                daemon=True
            ).start()
            
        except Exception as e:
            logging.error(f"Error highlighting route: {e}")
            messagebox.showerror("Error", f"Failed to highlight route:\n{str(e)}")
    
    def _fetch_and_plot_route(self, store_a, store_b):
        """Fetch realistic route and plot it (runs in background)"""
        try:
            # Get realistic route coordinates
            route_coords = self._get_route_coordinates(
                store_a['Latitude'], store_a['Longitude'],
                store_b['Latitude'], store_b['Longitude']
            )
            
            if not route_coords or len(route_coords) < 2:
                logging.warning("Could not fetch realistic route, using straight line")
                route_coords = [
                    (float(store_a['Latitude']), float(store_a['Longitude'])),
                    (float(store_b['Latitude']), float(store_b['Longitude']))
                ]
            
            # Calculate distance
            distance_km = self._calculate_route_distance(route_coords)
            
            # Plot on main thread
            self.after(0, lambda: self._plot_highlighted_route(store_a, store_b, route_coords, distance_km))
            
        except Exception as e:
            logging.error(f"Error fetching route: {e}")
            self.after(0, lambda: self.route_distance_label.config(text="❌ Error fetching route"))
    
    def _plot_highlighted_route(self, store_a, store_b, route_coords, distance_km):
        """Plot the highlighted route on map (runs on main thread)"""
        try:
            # Plot origin marker (Pink)
            self.route_marker_a = self.map_widget.set_marker(
                float(store_a['Latitude']),
                float(store_a['Longitude']),
                text="A",
                marker_color_circle="#E91E63",
                marker_color_outside="#880E4F",
                text_color="#FFFFFF",
                font=("Arial", 14, "bold")
            )
            
            # Plot destination marker (Pink)
            self.route_marker_b = self.map_widget.set_marker(
                float(store_b['Latitude']),
                float(store_b['Longitude']),
                text="B",
                marker_color_circle="#E91E63",
                marker_color_outside="#880E4F",
                text_color="#FFFFFF",
                font=("Arial", 14, "bold")
            )
            
            # Draw highlighted route path (Pink, thick)
            self.selected_route_path = self.map_widget.set_path(
                route_coords,
                color="#E91E63",
                width=5
            )
            
            # Update distance label
            self.route_distance_label.config(
                text=f"📏 {distance_km:.2f} km | ⏱️ {distance_km/50:.1f} hrs"
            )
            
            # Center map on route
            center_lat = (float(store_a['Latitude']) + float(store_b['Latitude'])) / 2
            center_lon = (float(store_a['Longitude']) + float(store_b['Longitude'])) / 2
            self.map_widget.set_position(center_lat, center_lon)
            
            # Auto-zoom
            self._fit_route_to_view(distance_km)
            
            logging.info(f"Route highlighted: Store {store_a['StoreID']} → Store {store_b['StoreID']} ({distance_km:.2f} km)")
            
        except Exception as e:
            logging.error(f"Error plotting highlighted route: {e}")
            self.route_distance_label.config(text="❌ Error plotting route")
    
    def _get_route_coordinates(self, lat1, lon1, lat2, lon2):
        """Fetch realistic route coordinates using OSRM"""
        if not ROUTING_AVAILABLE:
            return None
        
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
            params = {
                "overview": "full",
                "geometries": "geojson"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 'Ok' and data.get('routes'):
                    coordinates = data['routes'][0]['geometry']['coordinates']
                    route_coords = [(coord[1], coord[0]) for coord in coordinates]
                    
                    logging.info(f"Fetched realistic route with {len(route_coords)} waypoints")
                    return route_coords
            
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
        """Calculate distance between two coordinates"""
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
            if distance_km < 50:
                zoom = 10
            elif distance_km < 200:
                zoom = 8
            elif distance_km < 500:
                zoom = 7
            elif distance_km < 1000:
                zoom = 6
            else:
                zoom = 5
            
            self.map_widget.set_zoom(zoom)
        except Exception as e:
            logging.warning(f"Could not auto-zoom: {e}")
    
    def _clear_selected_route(self):
        """Clear the highlighted route"""
        if self.route_marker_a:
            self.route_marker_a.delete()
            self.route_marker_a = None
        
        if self.route_marker_b:
            self.route_marker_b.delete()
            self.route_marker_b = None
        
        if self.selected_route_path:
            self.selected_route_path.delete()
            self.selected_route_path = None
        
        self.route_distance_label.config(text="")
    
    def _clear_map(self, keep_selected=False):
        """Clear all markers and paths from map"""
        try:
            for marker in self.markers:
                marker.delete()
            self.markers.clear()
            
            for path in self.paths:
                path.delete()
            self.paths.clear()
            
            if not keep_selected:
                self._clear_selected_route()
            
        except Exception as e:
            logging.warning(f"Error clearing map: {e}")
    
    def _update_map_filters(self):
        """Update map based on filter checkboxes"""
        self._load_map_data_async()
    
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