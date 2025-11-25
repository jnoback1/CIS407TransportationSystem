"""
Edit Routes View - Manage delivery routes (Vehicle + Driver + Date groupings)
A route is defined as all deliveries assigned to a specific Vehicle on a specific Date.
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
    """Edit Routes - Manage routes (Vehicle + Date groupings) and their deliveries"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.selected_route = None  # (VehicleID, Order_Date) tuple
        self.routes_data = []
        self.deliveries_data = []
        self._create_ui()
        self.after(100, self._load_routes)
    
    def _create_ui(self):
        """Create the UI layout"""
        # Main container
        main_container = tk.Frame(self, bg=config.BG_LIGHT)
        main_container.pack(fill="both", expand=True, padx=config.PADDING_LARGE, pady=config.PADDING_LARGE)
        
        # Header
        header = SectionHeader(main_container, "Manage Routes", 
                             button_text="Refresh", 
                             button_command=self._load_routes)
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        # Description
        desc_label = tk.Label(
            main_container,
            text="Routes are grouped by Vehicle and Date. Select a route to view and manage its deliveries.",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_SECONDARY
        )
        desc_label.pack(fill="x", pady=(0, 10))
        
        # Content Split (Routes List vs Deliveries)
        content = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, bg=config.BG_LIGHT, sashwidth=5)
        content.pack(fill="both", expand=True)
        
        # Left Panel: Routes List
        left_panel = tk.Frame(content, bg=config.BG_LIGHT)
        content.add(left_panel, minsize=350)
        
        self._create_routes_panel(left_panel)
        
        # Right Panel: Route Details & Deliveries
        right_panel = tk.Frame(content, bg=config.BG_LIGHT)
        content.add(right_panel, minsize=450)
        
        self._create_details_panel(right_panel)
        
    def _create_routes_panel(self, parent):
        """Create the routes list panel"""
        # Title
        tk.Label(
            parent,
            text="Routes (Vehicle + Date)",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_LIGHT,
            fg=config.TEXT_PRIMARY
        ).pack(fill="x", pady=(0, 5))
        
        # Filter Frame
        filter_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(filter_frame, text="Filter:", bg=config.BG_LIGHT, 
                 font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL)).pack(side="left")
        
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.filter_var,
            values=["All", "Today", "This Week", "This Month"],
            state="readonly",
            width=12
        )
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._load_routes())
        
        # Routes Treeview
        columns = ("Date", "Vehicle", "Driver", "Deliveries", "Status")
        self.routes_tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse", height=15)
        
        col_widths = {"Date": 90, "Vehicle": 70, "Driver": 80, "Deliveries": 70, "Status": 80}
        for col in columns:
            self.routes_tree.heading(col, text=col)
            self.routes_tree.column(col, width=col_widths.get(col, 80), anchor="center")
            
        self.routes_tree.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.routes_tree.yview)
        scrollbar.place(relx=1, rely=0.1, relheight=0.8, anchor="ne")
        self.routes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.routes_tree.bind("<<TreeviewSelect>>", self._on_route_select)

    def _create_details_panel(self, parent):
        """Create the route details and deliveries panel"""
        # Route Summary Card
        summary_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        summary_frame.pack(fill="x", padx=(10, 0), pady=(0, 10))
        
        summary_content = tk.Frame(summary_frame, bg=config.BG_WHITE)
        summary_content.pack(fill="x", padx=15, pady=10)
        
        tk.Label(
            summary_content,
            text="Route Summary",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(anchor="w")
        
        self.summary_label = tk.Label(
            summary_content,
            text="Select a route to view details",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY,
            justify="left"
        )
        self.summary_label.pack(anchor="w", pady=(5, 0))
        
        # Route Actions
        actions_frame = tk.Frame(summary_content, bg=config.BG_WHITE)
        actions_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(
            actions_frame,
            text="Reassign Vehicle",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            command=self._reassign_vehicle
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="Reassign Driver",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            command=self._reassign_driver
        ).pack(side="left", padx=5)
        
        tk.Button(
            actions_frame,
            text="Delete Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg="#ffcccc",
            fg="#cc0000",
            command=self._delete_route
        ).pack(side="left", padx=5)
        
        # Deliveries List
        deliveries_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        deliveries_frame.pack(fill="both", expand=True, padx=(10, 0))
        
        deliveries_header = tk.Frame(deliveries_frame, bg=config.BG_WHITE)
        deliveries_header.pack(fill="x", padx=15, pady=10)
        
        tk.Label(
            deliveries_header,
            text="Deliveries in Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY
        ).pack(side="left")
        
        self.deliveries_count_label = tk.Label(
            deliveries_header,
            text="",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_SECONDARY
        )
        self.deliveries_count_label.pack(side="left", padx=(10, 0))
        
        # Deliveries Treeview
        del_columns = ("Order ID", "Store", "Drop Location", "Status", "Delivery Time")
        self.deliveries_tree = ttk.Treeview(
            deliveries_frame, 
            columns=del_columns, 
            show="headings", 
            selectmode="browse",
            height=10
        )
        
        del_widths = {"Order ID": 120, "Store": 60, "Drop Location": 90, "Status": 80, "Delivery Time": 90}
        for col in del_columns:
            self.deliveries_tree.heading(col, text=col)
            self.deliveries_tree.column(col, width=del_widths.get(col, 80), anchor="center")
        
        self.deliveries_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Delivery scrollbar
        del_scroll = ttk.Scrollbar(deliveries_frame, orient="vertical", command=self.deliveries_tree.yview)
        del_scroll.place(relx=0.98, rely=0.35, relheight=0.55, anchor="ne")
        self.deliveries_tree.configure(yscrollcommand=del_scroll.set)
        
        # Delivery Actions
        del_actions = tk.Frame(deliveries_frame, bg=config.BG_WHITE)
        del_actions.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Button(
            del_actions,
            text="Edit Delivery",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BUTTON_BG,
            fg=config.BUTTON_TEXT,
            command=self._edit_delivery
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            del_actions,
            text="Update Status",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg="#4CAF50",
            fg="white",
            command=self._update_delivery_status
        ).pack(side="left", padx=5)
        
        tk.Button(
            del_actions,
            text="Remove from Route",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg="#ffcccc",
            fg="#cc0000",
            command=self._remove_delivery
        ).pack(side="left", padx=5)

    def _load_routes(self):
        """Load routes (grouped by Vehicle + Date) from DB"""
        try:
            if not self.repo:
                self.repo = AzureSqlRepository()
            
            # Build date filter
            filter_val = self.filter_var.get()
            date_condition = ""
            if filter_val == "Today":
                date_condition = "WHERE Order_Date = CAST(GETDATE() AS DATE)"
            elif filter_val == "This Week":
                date_condition = "WHERE Order_Date >= DATEADD(DAY, -7, GETDATE())"
            elif filter_val == "This Month":
                date_condition = "WHERE Order_Date >= DATEADD(MONTH, -1, GETDATE())"
            
            # Get routes grouped by Vehicle + Date
            query = f"""
                SELECT 
                    VehicleID,
                    Order_Date,
                    MAX(DriverID) AS DriverID,
                    COUNT(*) AS DeliveryCount,
                    SUM(CASE WHEN Status = 'Delivered' THEN 1 ELSE 0 END) AS CompletedCount,
                    SUM(Delivery_Time) AS TotalDeliveryTime
                FROM DeliveryLog
                {date_condition}
                GROUP BY VehicleID, Order_Date
                ORDER BY Order_Date DESC, VehicleID
            """
            self.routes_data = self.repo.fetch_all(query)
            self._populate_routes_tree()
            
        except Exception as e:
            logging.error(f"Error loading routes: {e}")
            messagebox.showerror("Error", f"Failed to load routes: {e}")

    def _populate_routes_tree(self):
        """Populate routes treeview"""
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)
            
        for route in self.routes_data:
            date_str = str(route['Order_Date'])[:10]
            vehicle = f"V{route['VehicleID']}"
            driver = f"D{route['DriverID']}" if route['DriverID'] else "Unassigned"
            deliveries = route['DeliveryCount']
            completed = route['CompletedCount']
            
            if completed == deliveries:
                status = "Completed"
            elif completed > 0:
                status = f"{completed}/{deliveries}"
            else:
                status = "Pending"
            
            self.routes_tree.insert("", "end", 
                iid=f"{route['VehicleID']}_{route['Order_Date']}",
                values=(date_str, vehicle, driver, deliveries, status)
            )

    def _on_route_select(self, event):
        """Handle route selection"""
        selected = self.routes_tree.selection()
        if not selected:
            return
        
        # Parse VehicleID and Date from iid
        iid = selected[0]
        parts = iid.split("_")
        vehicle_id = int(parts[0])
        order_date = parts[1]
        
        self.selected_route = (vehicle_id, order_date)
        self._load_route_details()

    def _load_route_details(self):
        """Load details for selected route"""
        if not self.selected_route:
            return
        
        vehicle_id, order_date = self.selected_route
        
        try:
            # Get route summary
            route = next(
                (r for r in self.routes_data 
                 if r['VehicleID'] == vehicle_id and str(r['Order_Date']) == order_date),
                None
            )
            
            if route:
                total_time = route['TotalDeliveryTime'] or 0
                completed = route['CompletedCount']
                total = route['DeliveryCount']
                
                self.summary_label.config(
                    text=f"Vehicle: V{vehicle_id}  |  Date: {order_date}\n"
                         f"Driver: D{route['DriverID'] or 'Unassigned'}  |  "
                         f"Deliveries: {completed}/{total} completed\n"
                         f"Total Delivery Time: {total_time} minutes"
                )
            
            # Load deliveries for this route
            query = f"""
                SELECT 
                    Order_ID, StoreID, DropLocationID, Status, 
                    Delivery_Time, Pickup_Time, Order_Time
                FROM DeliveryLog
                WHERE VehicleID = {vehicle_id} 
                  AND Order_Date = '{order_date}'
                ORDER BY Order_Time
            """
            self.deliveries_data = self.repo.fetch_all(query)
            self._populate_deliveries_tree()
            
        except Exception as e:
            logging.error(f"Error loading route details: {e}")

    def _populate_deliveries_tree(self):
        """Populate deliveries treeview"""
        for item in self.deliveries_tree.get_children():
            self.deliveries_tree.delete(item)
        
        self.deliveries_count_label.config(text=f"({len(self.deliveries_data)} deliveries)")
        
        for delivery in self.deliveries_data:
            order_id = delivery['Order_ID']
            store = f"S{delivery['StoreID']}"
            drop = f"D{delivery['DropLocationID']}" if delivery['DropLocationID'] else "N/A"
            status = delivery['Status'] or "Pending"
            del_time = f"{delivery['Delivery_Time']} min" if delivery['Delivery_Time'] else "-"
            
            self.deliveries_tree.insert("", "end",
                iid=order_id,
                values=(order_id, store, drop, status, del_time)
            )

    def _reassign_vehicle(self):
        """Reassign all deliveries in route to a different vehicle"""
        if not self.selected_route:
            messagebox.showwarning("No Selection", "Please select a route first")
            return
        
        vehicle_id, order_date = self.selected_route
        
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Reassign Vehicle")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Current Vehicle: V{vehicle_id}").pack(pady=10)
        tk.Label(dialog, text="New Vehicle ID:").pack()
        
        new_vehicle_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=new_vehicle_var)
        entry.pack(pady=5)
        
        def do_reassign():
            try:
                new_id = int(new_vehicle_var.get())
                sql = f"""
                    UPDATE DeliveryLog 
                    SET VehicleID = {new_id}
                    WHERE VehicleID = {vehicle_id} AND Order_Date = '{order_date}'
                """
                self.repo.execute(sql)
                messagebox.showinfo("Success", f"Route reassigned to Vehicle {new_id}")
                dialog.destroy()
                self._load_routes()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reassign: {e}")
        
        tk.Button(dialog, text="Reassign", command=do_reassign).pack(pady=10)

    def _reassign_driver(self):
        """Reassign all deliveries in route to a different driver"""
        if not self.selected_route:
            messagebox.showwarning("No Selection", "Please select a route first")
            return
        
        vehicle_id, order_date = self.selected_route
        
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Reassign Driver")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="New Driver ID:").pack(pady=10)
        
        new_driver_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=new_driver_var)
        entry.pack(pady=5)
        
        def do_reassign():
            try:
                new_id = int(new_driver_var.get())
                sql = f"""
                    UPDATE DeliveryLog 
                    SET DriverID = {new_id}
                    WHERE VehicleID = {vehicle_id} AND Order_Date = '{order_date}'
                """
                self.repo.execute(sql)
                messagebox.showinfo("Success", f"Route reassigned to Driver {new_id}")
                dialog.destroy()
                self._load_route_details()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reassign: {e}")
        
        tk.Button(dialog, text="Reassign", command=do_reassign).pack(pady=10)

    def _delete_route(self):
        """Delete entire route (all deliveries for Vehicle + Date)"""
        if not self.selected_route:
            messagebox.showwarning("No Selection", "Please select a route first")
            return
        
        vehicle_id, order_date = self.selected_route
        count = len(self.deliveries_data)
        
        if not messagebox.askyesno(
            "Confirm Delete", 
            f"Delete entire route?\n\nVehicle: V{vehicle_id}\nDate: {order_date}\n\n"
            f"This will remove {count} delivery records.\n\nThis action cannot be undone."
        ):
            return
        
        try:
            sql = f"""
                DELETE FROM DeliveryLog 
                WHERE VehicleID = {vehicle_id} AND Order_Date = '{order_date}'
            """
            self.repo.execute(sql)
            messagebox.showinfo("Success", f"Route deleted ({count} deliveries removed)")
            self.selected_route = None
            self.summary_label.config(text="Select a route to view details")
            self.deliveries_count_label.config(text="")
            for item in self.deliveries_tree.get_children():
                self.deliveries_tree.delete(item)
            self._load_routes()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete route: {e}")

    def _edit_delivery(self):
        """Edit selected delivery"""
        selected = self.deliveries_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a delivery to edit")
            return
        
        order_id = selected[0]
        delivery = next((d for d in self.deliveries_data if d['Order_ID'] == order_id), None)
        
        if not delivery:
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Delivery - {order_id}")
        dialog.geometry("350x300")
        dialog.transient(self)
        dialog.grab_set()
        
        form = tk.Frame(dialog)
        form.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Fields
        fields = {}
        
        row = 0
        for label, key, value in [
            ("Order ID:", "order_id", order_id),
            ("Store ID:", "store_id", delivery['StoreID']),
            ("Drop Location ID:", "drop_id", delivery['DropLocationID'] or ""),
            ("Status:", "status", delivery['Status'] or "Pending"),
            ("Delivery Time (min):", "del_time", delivery['Delivery_Time'] or ""),
        ]:
            tk.Label(form, text=label, anchor="w").grid(row=row, column=0, sticky="w", pady=3)
            entry = tk.Entry(form, width=25)
            entry.insert(0, str(value))
            if key == "order_id":
                entry.config(state="readonly")
            entry.grid(row=row, column=1, pady=3)
            fields[key] = entry
            row += 1
        
        def save_changes():
            try:
                drop_id = fields['drop_id'].get()
                drop_value = drop_id if drop_id else "NULL"
                del_time = fields['del_time'].get()
                del_value = del_time if del_time else "0"
                
                sql = f"""
                    UPDATE DeliveryLog
                    SET StoreID = {fields['store_id'].get()},
                        DropLocationID = {drop_value},
                        Status = '{fields['status'].get()}',
                        Delivery_Time = {del_value}
                    WHERE Order_ID = '{order_id}'
                """
                self.repo.execute(sql)
                messagebox.showinfo("Success", "Delivery updated")
                dialog.destroy()
                self._load_route_details()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update: {e}")
        
        tk.Button(form, text="Save Changes", command=save_changes).grid(row=row, column=0, columnspan=2, pady=15)

    def _update_delivery_status(self):
        """Quick status update for selected delivery"""
        selected = self.deliveries_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a delivery")
            return
        
        order_id = selected[0]
        
        # Status options dialog
        dialog = tk.Toplevel(self)
        dialog.title("Update Status")
        dialog.geometry("250x150")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Order: {order_id}").pack(pady=10)
        tk.Label(dialog, text="New Status:").pack()
        
        status_var = tk.StringVar(value="Delivered")
        combo = ttk.Combobox(
            dialog,
            textvariable=status_var,
            values=["Pending", "In Transit", "Delivered", "Failed", "Cancelled"],
            state="readonly"
        )
        combo.pack(pady=5)
        
        def update():
            try:
                sql = f"UPDATE DeliveryLog SET Status = '{status_var.get()}' WHERE Order_ID = '{order_id}'"
                self.repo.execute(sql)
                messagebox.showinfo("Success", "Status updated")
                dialog.destroy()
                self._load_route_details()
                self._load_routes()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update: {e}")
        
        tk.Button(dialog, text="Update", command=update).pack(pady=10)

    def _remove_delivery(self):
        """Remove selected delivery from route"""
        selected = self.deliveries_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a delivery to remove")
            return
        
        order_id = selected[0]
        
        if not messagebox.askyesno("Confirm Delete", f"Delete delivery {order_id}?\n\nThis cannot be undone."):
            return
        
        try:
            sql = f"DELETE FROM DeliveryLog WHERE Order_ID = '{order_id}'"
            self.repo.execute(sql)
            messagebox.showinfo("Success", "Delivery removed")
            self._load_route_details()
            self._load_routes()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {e}")

    def destroy(self):
        if self.repo:
            try:
                self.repo.close()
            except:
                pass
        super().destroy()
