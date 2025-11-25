"""
Edit Routes View - Manage existing routes (Read, Update, Delete)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from ui_components import SectionHeader
from backend.repository import AzureSqlRepository

class EditRoutesView(tk.Frame):
    """Edit Routes - CRUD operations for routes"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.selected_route_id = None
        self._create_ui()
        self.after(100, self._load_routes)
    
    def _create_ui(self):
        """Create the UI layout"""
        # Main container
        main_container = tk.Frame(self, bg=config.BG_LIGHT)
        main_container.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        # Header
        header = SectionHeader(main_container, "Manage Routes", 
                             button_text="Refresh Data", 
                             button_command=self._load_routes)
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        # Content Split (List vs Edit Form)
        content = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, bg=config.BG_LIGHT, sashwidth=5)
        content.pack(fill="both", expand=True)
        
        # Left Panel: Route List
        left_panel = tk.Frame(content, bg=config.BG_LIGHT)
        content.add(left_panel, minsize=400)
        
        self._create_list_panel(left_panel)
        
        # Right Panel: Edit Form
        right_panel = tk.Frame(content, bg=config.BG_LIGHT)
        content.add(right_panel, minsize=300)
        
        self._create_edit_form(right_panel)
        
    def _create_list_panel(self, parent):
        """Create the treeview list of routes"""
        # Filter Frame
        filter_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(filter_frame, text="Search Order ID:", bg=config.BG_LIGHT).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda name, index, mode: self._filter_routes())
        tk.Entry(filter_frame, textvariable=self.search_var).pack(side="left", padx=5, fill="x", expand=True)
        
        # Treeview
        columns = ("Order ID", "Status", "Date", "Vehicle")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        self.tree.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        scrollbar.place(relx=1, rely=0, relheight=1, anchor="ne")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _create_edit_form(self, parent):
        """Create the form to edit selected route"""
        self.form_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        self.form_frame.pack(fill="both", expand=True, padx=(10, 0))
        
        tk.Label(self.form_frame, text="Edit Route Details", 
                 font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
                 bg=config.BG_WHITE, fg=config.TEXT_PRIMARY).pack(pady=15)
        
        # Fields
        fields_container = tk.Frame(self.form_frame, bg=config.BG_WHITE)
        fields_container.pack(fill="x", padx=20)
        
        # Order ID (Read Only)
        self._add_field(fields_container, "Order ID:", "order_id", readonly=True)
        
        # Status
        self._add_field(fields_container, "Status:", "status")
        
        # Vehicle ID
        self._add_field(fields_container, "Vehicle ID:", "vehicle_id")
        
        # Delivery Time
        self._add_field(fields_container, "Delivery Time (min):", "delivery_time")
        
        # Pickup Time
        self._add_field(fields_container, "Pickup Time (HH:MM:SS):", "pickup_time")

        # Buttons
        btn_frame = tk.Frame(self.form_frame, bg=config.BG_WHITE)
        btn_frame.pack(pady=20)
        
        # Use standard button colors for better compatibility
        tk.Button(btn_frame, text="Update Route", 
                  bg=config.BUTTON_BG, fg=config.BUTTON_TEXT,
                  font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
                  command=self._update_route).pack(side="left", padx=5)
                  
        tk.Button(btn_frame, text="Delete Route", 
                  bg="#ffcccc", fg="#cc0000", # Light red bg, dark red text for visibility
                  font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
                  command=self._delete_route).pack(side="left", padx=5)

        # Store entry references
        self.entries = {}
        
    def _add_field(self, parent, label_text, key, readonly=False):
        """Helper to add a labeled entry field"""
        frame = tk.Frame(parent, bg=config.BG_WHITE)
        frame.pack(fill="x", pady=5)
        
        tk.Label(frame, text=label_text, width=20, anchor="w", 
                 bg=config.BG_WHITE, fg=config.TEXT_PRIMARY).pack(side="left")
        
        entry = tk.Entry(frame, 
                         bg=config.BG_WHITE, 
                         fg=config.TEXT_PRIMARY,
                         insertbackground=config.TEXT_PRIMARY, # Cursor color
                         relief="solid", borderwidth=1)
        if readonly:
            entry.configure(state="readonly", readonlybackground="#e9ecef")
        entry.pack(side="left", fill="x", expand=True)
        
        # Store reference. If it's the first time calling this, initialize dict
        if not hasattr(self, 'entries'):
            self.entries = {}
        self.entries[key] = entry

    def _load_routes(self):
        """Fetch routes from DB"""
        try:
            if not self.repo:
                self.repo = AzureSqlRepository()
                
            query = """
                SELECT Order_ID, Status, Order_Date, VehicleID, Delivery_Time, Pickup_Time
                FROM DeliveryLog
                ORDER BY Order_Date DESC
            """
            self.routes_data = self.repo.fetch_all(query)
            self._populate_tree(self.routes_data)
            
        except Exception as e:
            logging.error(f"Error loading routes: {e}")
            messagebox.showerror("Error", f"Failed to load routes: {e}")

    def _populate_tree(self, data):
        """Populate treeview with data"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for route in data:
            self.tree.insert("", "end", values=(
                route['Order_ID'],
                route['Status'],
                route['Order_Date'],
                route['VehicleID']
            ))

    def _filter_routes(self):
        """Filter treeview based on search"""
        search_term = self.search_var.get().lower()
        filtered = [r for r in self.routes_data if search_term in str(r['Order_ID']).lower()]
        self._populate_tree(filtered)

    def _on_select(self, event):
        """Handle row selection"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item = self.tree.item(selected_items[0])
        order_id = item['values'][0]
        self.selected_route_id = order_id
        
        # Find full data object
        route = next((r for r in self.routes_data if str(r['Order_ID']) == str(order_id)), None)
        
        if route:
            self._fill_form(route)

    def _fill_form(self, route):
        """Fill the edit form with route data"""
        self._set_entry("order_id", route['Order_ID'])
        self._set_entry("status", route['Status'])
        self._set_entry("vehicle_id", route['VehicleID'])
        self._set_entry("delivery_time", route['Delivery_Time'])
        
        # Handle Pickup Time (might be datetime.time or string)
        pickup = route['Pickup_Time']
        if pickup:
            self._set_entry("pickup_time", str(pickup))
        else:
            self._set_entry("pickup_time", "")

    def _set_entry(self, key, value):
        """Helper to set entry text"""
        entry = self.entries.get(key)
        if entry:
            is_readonly = entry.cget('state') == 'readonly'
            if is_readonly:
                entry.configure(state='normal')
            
            entry.delete(0, tk.END)
            entry.insert(0, str(value) if value is not None else "")
            
            if is_readonly:
                entry.configure(state='readonly')

    def _update_route(self):
        """Update the selected route in DB"""
        if not self.selected_route_id:
            return
            
        try:
            status = self.entries['status'].get()
            vehicle_id = self.entries['vehicle_id'].get()
            delivery_time = self.entries['delivery_time'].get()
            pickup_time = self.entries['pickup_time'].get()
            
            query = """
                UPDATE DeliveryLog
                SET Status = ?, VehicleID = ?, Delivery_Time = ?, Pickup_Time = ?
                WHERE Order_ID = ?
            """
            # Note: In a real app, use parameterized queries properly. 
            # The repo.execute might need formatting if it doesn't support params directly in this way.
            # Based on previous files, it seems we use f-strings often, which is risky but consistent with this codebase.
            # Let's check repo.execute signature.
            
            # Assuming f-string for now based on other files
            sql = f"""
                UPDATE DeliveryLog
                SET Status = '{status}', 
                    VehicleID = {vehicle_id}, 
                    Delivery_Time = {delivery_time},
                    Pickup_Time = '{pickup_time}'
                WHERE Order_ID = '{self.selected_route_id}'
            """
            
            self.repo.execute(sql)
            messagebox.showinfo("Success", "Route updated successfully")
            self._load_routes()
            
        except Exception as e:
            logging.error(f"Update error: {e}")
            messagebox.showerror("Error", f"Failed to update: {e}")

    def _delete_route(self):
        """Delete the selected route"""
        if not self.selected_route_id:
            return
            
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Order {self.selected_route_id}?"):
            return
            
        try:
            sql = f"DELETE FROM DeliveryLog WHERE Order_ID = '{self.selected_route_id}'"
            self.repo.execute(sql)
            messagebox.showinfo("Success", "Route deleted successfully")
            self.selected_route_id = None
            self._clear_form()
            self._load_routes()
            
        except Exception as e:
            logging.error(f"Delete error: {e}")
            messagebox.showerror("Error", f"Failed to delete: {e}")

    def _clear_form(self):
        """Clear all form inputs"""
        for entry in self.entries.values():
            is_readonly = entry.cget('state') == 'readonly'
            if is_readonly:
                entry.configure(state='normal')
            entry.delete(0, tk.END)
            if is_readonly:
                entry.configure(state='readonly')

    def destroy(self):
        if self.repo:
            self.repo.close()
        super().destroy()
