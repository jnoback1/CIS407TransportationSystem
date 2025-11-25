"""
Analytics View - Database-driven reporting and insights
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


#TO DO:
#FIX DELIVERY PERFORMANCE CARD VIEW ERRORS
class AnalyticsView(tk.Frame):
    """Analytics Dashboard - Database-driven reporting and insights"""
    
    def __init__(self, parent, user_info):
        super().__init__(parent, bg=config.BG_LIGHT)
        self.user_info = user_info
        self.repo = None
        self.predictor = None  # Placeholder for future ML model (Phase 2)
        self._create_ui()
        self.after(100, self._load_analytics_data)
    
    def _create_ui(self):
        """Create analytics dashboard UI"""
        # Main scrollable canvas
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
        
        # Header with controls
        self._create_header(content)
        
        # Performance metrics section
        self._create_performance_metrics(content)
        
        # Vehicle utilization section
        self._create_vehicle_metrics(content)
        
        # Time-based analytics with charts
        self._create_time_analytics(content)
        
        # Detailed reports table
        self._create_reports_table(content)
        
        # Future ML predictions placeholder
        self._create_ml_placeholder(content)
    
    def _create_header(self, parent):
        """Create header with title and controls"""
        header_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Analytics & Reports",
            font=(config.FONT_FAMILY, config.FONT_SIZE_HEADING, "bold"),
            bg=config.BG_LIGHT, 
            fg=config.TEXT_PRIMARY, 
            anchor="w"
        )
        title_label.pack(side="left")
        
        # Last updated timestamp
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
        
        # Retrain ML Model button
        retrain_btn = tk.Button(
            controls_frame, 
            text="Retrain AI Model",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#9B59B6",
            fg=config.BG_WHITE,
            activebackground="#8E44AD",
            relief="flat", 
            cursor="hand2",
            padx=15, 
            pady=5,
            command=self._retrain_ml_model
        )
        retrain_btn.pack(side="right", padx=5)
        
        # Export button
        export_btn = tk.Button(
            controls_frame, 
            text="Export CSV",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg="#2ECC71", 
            fg=config.BG_WHITE,
            activebackground="#27AE60",
            relief="flat", 
            cursor="hand2",
            padx=15, 
            pady=5,
            command=self._export_to_csv
        )
        export_btn.pack(side="right", padx=5)
        
        # Refresh button
        refresh_btn = tk.Button(
            controls_frame, 
            text="Refresh",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.BUTTON_BG, 
            fg=config.BUTTON_TEXT,
            activebackground=config.BUTTON_HOVER,
            relief="flat", 
            cursor="hand2",
            padx=15, 
            pady=5,
            command=self._load_analytics_data
        )
        refresh_btn.pack(side="right", padx=5)
    
    def _create_performance_metrics(self, parent):
        """Create delivery performance metrics section"""
        header = SectionHeader(parent, "Delivery Performance")
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        metrics_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        metrics_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        # Configure grid
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)
        
        # Performance cards
        self.avg_delivery_card = MetricCard(
            metrics_frame, 
            "Avg Delivery Time", 
            value="—", 
            subtitle="Minutes"
        )
        self.avg_delivery_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.total_today_card = MetricCard(
            metrics_frame, 
            "Today's Total", 
            value="—", 
            subtitle="Deliveries"
        )
        self.total_today_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.total_week_card = MetricCard(
            metrics_frame, 
            "This Week", 
            value="—", 
            subtitle="Deliveries"
        )
        self.total_week_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.total_month_card = MetricCard(
            metrics_frame, 
            "This Month", 
            value="—", 
            subtitle="Deliveries"
        )
        self.total_month_card.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Second row of metrics
        self.avg_pickup_card = MetricCard(
            metrics_frame, 
            "Avg Pickup Time", 
            value="—", 
            subtitle="Minutes"
        )
        self.avg_pickup_card.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.success_rate_card = MetricCard(
            metrics_frame, 
            "Success Rate", 
            value="—", 
            subtitle="% Completed"
        )
        self.success_rate_card.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.fastest_delivery_card = MetricCard(
            metrics_frame, 
            "Fastest Delivery", 
            value="—", 
            subtitle="Minutes"
        )
        self.fastest_delivery_card.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        self.slowest_delivery_card = MetricCard(
            metrics_frame, 
            "Slowest Delivery", 
            value="—", 
            subtitle="Minutes"
        )
        self.slowest_delivery_card.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
    
    def _create_vehicle_metrics(self, parent):
        """Create vehicle utilization metrics"""
        header = SectionHeader(parent, "Vehicle & Resource Utilization")
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        metrics_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        metrics_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)
        
        self.total_vehicles_card = MetricCard(
            metrics_frame, 
            "Total Vehicles", 
            value="—", 
            subtitle="In fleet"
        )
        self.total_vehicles_card.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.active_vehicles_card = MetricCard(
            metrics_frame, 
            "Active Now", 
            value="—", 
            subtitle="Vehicles"
        )
        self.active_vehicles_card.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.idle_vehicles_card = MetricCard(
            metrics_frame, 
            "Idle Vehicles", 
            value="—", 
            subtitle="Available"
        )
        self.idle_vehicles_card.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.avg_per_vehicle_card = MetricCard(
            metrics_frame, 
            "Avg per Vehicle", 
            value="—", 
            subtitle="Deliveries/day"
        )
        self.avg_per_vehicle_card.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
    
    def _create_time_analytics(self, parent):
        """Create time-based analytics with visual charts"""
        header = SectionHeader(parent, "Delivery Trends & Patterns")
        header.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        timeline_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        timeline_frame.pack(fill="x", pady=(0, config.PADDING_LARGE))
        
        # Scrollable text widget for timeline visualization
        self.timeline_text = tk.Text(
            timeline_frame,
            font=("Courier New", config.FONT_SIZE_SMALL),  # Monospace for charts
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY,
            height=15,
            wrap="none",
            borderwidth=0,
            padx=15,
            pady=15
        )
        
        # Scrollbars
        timeline_scroll_y = tk.Scrollbar(timeline_frame, orient="vertical", command=self.timeline_text.yview)
        timeline_scroll_x = tk.Scrollbar(timeline_frame, orient="horizontal", command=self.timeline_text.xview)
        self.timeline_text.configure(yscrollcommand=timeline_scroll_y.set, xscrollcommand=timeline_scroll_x.set)
        
        self.timeline_text.grid(row=0, column=0, sticky="nsew")
        timeline_scroll_y.grid(row=0, column=1, sticky="ns")
        timeline_scroll_x.grid(row=1, column=0, sticky="ew")
        
        timeline_frame.grid_rowconfigure(0, weight=1)
        timeline_frame.grid_columnconfigure(0, weight=1)
        
        self.timeline_text.config(state="disabled")
    
    def _create_reports_table(self, parent):
        """Create detailed reports table with filtering"""
        header_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(0, config.PADDING_MEDIUM))
        
        SectionHeader(header_frame, "Detailed Delivery Reports").pack(side="left", fill="x", expand=True)
        
        # Filter controls
        filter_frame = tk.Frame(header_frame, bg=config.BG_LIGHT)
        filter_frame.pack(side="right")
        
        tk.Label(
            filter_frame,
            text="Show:",
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL),
            bg=config.BG_LIGHT,
            fg=config.TEXT_PRIMARY
        ).pack(side="left", padx=5)
        
        self.report_filter = ttk.Combobox(
            filter_frame,
            values=["All Records", "Last 50", "Last 100", "Last 500"],
            state="readonly",
            width=15,
            font=(config.FONT_FAMILY, config.FONT_SIZE_SMALL)
        )
        self.report_filter.set("Last 100")
        self.report_filter.pack(side="left", padx=5)
        self.report_filter.bind("<<ComboboxSelected>>", lambda e: self._load_reports_table_data())
        
        # Table frame
        table_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        table_frame.pack(fill="both", expand=True)
        
        # Create Treeview
        columns = ("Order ID", "Date", "Vehicle", "Pickup Time", "Delivery Time", "Total Time", "Status")
        self.reports_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        column_widths = {
            "Order ID": 80,
            "Date": 150,
            "Vehicle": 80,
            "Pickup Time": 100,
            "Delivery Time": 100,
            "Total Time": 100,
            "Status": 100
        }
        
        for col in columns:
            self.reports_tree.heading(col, text=col, command=lambda c=col: self._sort_table(c))
            self.reports_tree.column(col, width=column_widths.get(col, 100), anchor="center" if col == "Order ID" else "w")
        
        # Scrollbars
        tree_scroll_y = tk.Scrollbar(table_frame, orient="vertical", command=self.reports_tree.yview)
        tree_scroll_x = tk.Scrollbar(table_frame, orient="horizontal", command=self.reports_tree.xview)
        self.reports_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.reports_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Alternating row colors
        self.reports_tree.tag_configure('oddrow', background=config.BG_WHITE)
        self.reports_tree.tag_configure('evenrow', background='#F5F5F5')
    
    def _create_ml_placeholder(self, parent):
        """ML-powered delivery time predictions"""
        header_frame = tk.Frame(parent, bg=config.BG_LIGHT)
        header_frame.pack(fill="x", pady=(config.PADDING_LARGE, config.PADDING_MEDIUM))
        
        SectionHeader(header_frame, "Forecasted Delivery Times").pack(side="left")
        
        # Add Load Predictions button
        load_predictions_btn = tk.Button(
            header_frame,
            text="Load Predictions",
            font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL, "bold"),
            bg=config.PRIMARY_COLOR,
            fg=config.BG_WHITE,
            activebackground="#2980B9",  # Darker shade of PRIMARY_COLOR
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=5,
            command=self._load_ml_predictions
        )
        load_predictions_btn.pack(side="right")
        
        prediction_frame = tk.Frame(parent, bg=config.BG_WHITE, relief="solid", borderwidth=1)
        prediction_frame.pack(fill="both", expand=True, pady=(0, config.PADDING_LARGE))
        
        # Create scrollable text widget for predictions
        self.prediction_text = tk.Text(
            prediction_frame,
            font=("Consolas", config.FONT_SIZE_SMALL),
            bg=config.BG_WHITE,
            fg=config.TEXT_PRIMARY,
            height=20,
            wrap="word",
            borderwidth=0,
            padx=15,
            pady=15,
            state="disabled"
        )
        
        prediction_scroll = tk.Scrollbar(prediction_frame, orient="vertical", command=self.prediction_text.yview)
        self.prediction_text.configure(yscrollcommand=prediction_scroll.set)
        
        self.prediction_text.grid(row=0, column=0, sticky="nsew")
        prediction_scroll.grid(row=0, column=1, sticky="ns")
        
        prediction_frame.grid_rowconfigure(0, weight=1)
        prediction_frame.grid_columnconfigure(0, weight=1)
        
        # Try to load ML model but don't run predictions yet
        self._initialize_ml_model()
        
        # Show placeholder message
        self._show_prediction_placeholder()
    
    def _show_prediction_placeholder(self):
        """Show placeholder message before predictions are loaded"""
        self.prediction_text.config(state="normal")
        self.prediction_text.delete(1.0, "end")
        
        if not self.predictor:
            self.prediction_text.insert("end", "Machine learning libraries not installed.\n\n")
            self.prediction_text.insert("end", "To enable AI predictions, install:\n")
            self.prediction_text.insert("end", "  pip install scikit-learn pandas numpy joblib\n\n")
            self.prediction_text.insert("end", "Then train the model with:\n")
            self.prediction_text.insert("end", "  python machine_learning/delivery_predictor.py")
        elif not self.predictor.is_trained:
            self.prediction_text.insert("end", "Model not trained yet.\n\n")
            self.prediction_text.insert("end", "To train the model, click 'Retrain AI Model' button above\n")
            self.prediction_text.insert("end", "or run from command line:\n")
            self.prediction_text.insert("end", "  python machine_learning/delivery_predictor.py\n\n")
            self.prediction_text.insert("end", "This will analyze your historical delivery data and create\n")
            self.prediction_text.insert("end", "a regression model to predict future delivery times.")
        else:
            self.prediction_text.insert("end", "AI model loaded and ready.\n\n")
            self.prediction_text.insert("end", "Click 'Load Predictions' button above to view\n")
            self.prediction_text.insert("end", "recent delivery time predictions and model accuracy.\n\n")
            
            if hasattr(self.predictor, 'training_date') and self.predictor.training_date:
                train_date = self.predictor.training_date.strftime('%Y-%m-%d %H:%M')
                self.prediction_text.insert("end", f"Last Trained: {train_date}\n")
            if hasattr(self.predictor, 'training_samples'):
                self.prediction_text.insert("end", f"Training Samples: {self.predictor.training_samples}\n")
        
        self.prediction_text.config(state="disabled")
    
    def _initialize_ml_model(self):
        """Initialize the ML prediction model"""
        try:
            from machine_learning.delivery_predictor import DeliveryTimePredictor
            
            self.predictor = DeliveryTimePredictor()
            
            if not self.predictor.is_trained:
                logging.info("ML model not trained yet")
            else:
                logging.info("ML model loaded successfully")
                
        except ImportError as e:
            logging.warning(f"ML model not available: {e}")
            self.predictor = None
        except Exception as e:
            logging.error(f"Error initializing ML model: {e}")
            self.predictor = None
    
    def _load_analytics_data(self):
        """Load all analytics data from database"""
        try:
            if not self.repo:
                self.repo = AzureSqlRepository()
            
            # Load all sections EXCEPT predictions (load on demand)
            self._load_performance_metrics()
            self._load_vehicle_metrics()
            self._load_timeline_data()
            self._load_reports_table_data()
            # self._load_ml_predictions()  # ❌ Remove this line
            
            # Update timestamp
            self.last_updated_label.config(text=f"Last updated: {datetime.now().strftime('%I:%M:%S %p')}")
            
            logging.info("Analytics data loaded successfully")
            
        except Exception as e:
            logging.error(f"Error loading analytics data: {e}")
            messagebox.showerror("Error", f"Failed to load analytics:\n{str(e)[:150]}")
    
    def _load_performance_metrics(self):
        """Load delivery performance metrics"""
        try:
            # Average delivery time - Delivery_Time is already in minutes
            avg_delivery = self.repo.fetch_all("""
                SELECT AVG(CAST(Delivery_Time AS FLOAT)) AS AvgTime
                FROM DeliveryLog
                WHERE Delivery_Time IS NOT NULL
            """)
            avg_time = round(avg_delivery[0]['AvgTime'], 1) if avg_delivery and avg_delivery[0]['AvgTime'] else 0
            self.avg_delivery_card.update_value(f"{avg_time}")
            
            # Average pickup time - convert TIME to minutes using DATEDIFF
            avg_pickup = self.repo.fetch_all("""
                SELECT AVG(DATEDIFF(MINUTE, '00:00:00', CAST(Pickup_Time AS TIME))) AS AvgTime
                FROM DeliveryLog
                WHERE Pickup_Time IS NOT NULL
            """)
            avg_pickup_time = round(avg_pickup[0]['AvgTime'], 1) if avg_pickup and avg_pickup[0]['AvgTime'] else 0
            self.avg_pickup_card.update_value(f"{avg_pickup_time}")
            
            # Today's total
            today_total = self.repo.fetch_all("""
                SELECT COUNT(*) AS Total
                FROM DeliveryLog
                WHERE CAST(Order_Date AS DATE) = CAST(GETDATE() AS DATE)
            """)
            self.total_today_card.update_value(str(today_total[0]['Total']) if today_total else "0")
            
            # This week's total
            week_total = self.repo.fetch_all("""
                SELECT COUNT(*) AS Total
                FROM DeliveryLog
                WHERE Order_Date >= DATEADD(WEEK, -1, GETDATE())
            """)
            self.total_week_card.update_value(str(week_total[0]['Total']) if week_total else "0")
            
            # This month's total
            month_total = self.repo.fetch_all("""
                SELECT COUNT(*) AS Total
                FROM DeliveryLog
                WHERE Order_Date >= DATEADD(MONTH, -1, GETDATE())
            """)
            self.total_month_card.update_value(str(month_total[0]['Total']) if month_total else "0")
            
            # Success rate (completed vs total)
            success_rate = self.repo.fetch_all("""
                SELECT 
                    CAST(COUNT(CASE WHEN Delivery_Time IS NOT NULL THEN 1 END) AS FLOAT) /
                    NULLIF(COUNT(*), 0) * 100 AS SuccessRate
                FROM DeliveryLog
            """)
            rate = round(success_rate[0]['SuccessRate'], 1) if success_rate and success_rate[0]['SuccessRate'] else 0
            self.success_rate_card.update_value(f"{rate}%")
            
            # Fastest delivery - Delivery_Time is in minutes
            fastest = self.repo.fetch_all("""
                SELECT MIN(Delivery_Time) AS Fastest
                FROM DeliveryLog
                WHERE Delivery_Time IS NOT NULL
            """)
            fastest_time = fastest[0]['Fastest'] if fastest and fastest[0]['Fastest'] else 0
            self.fastest_delivery_card.update_value(f"{fastest_time}")
            
            # Slowest delivery - Delivery_Time is in minutes
            slowest = self.repo.fetch_all("""
                SELECT MAX(Delivery_Time) AS Slowest
                FROM DeliveryLog
                WHERE Delivery_Time IS NOT NULL
            """)
            slowest_time = slowest[0]['Slowest'] if slowest and slowest[0]['Slowest'] else 0
            self.slowest_delivery_card.update_value(f"{slowest_time}")
            
        except Exception as e:
            logging.error(f"Error loading performance metrics: {e}")
            # Show error in cards
            self.avg_delivery_card.update_value("Error")
            self.avg_pickup_card.update_value("Error")

    def _load_vehicle_metrics(self):
        """Load vehicle utilization metrics"""
        try:
            # Total vehicles
            total_vehicles = self.repo.fetch_all("""
                SELECT COUNT(DISTINCT VehicleID) AS Total
                FROM DeliveryLog
            """)
            total = total_vehicles[0]['Total'] if total_vehicles else 0
            self.total_vehicles_card.update_value(str(total))
            
            # Active vehicles (currently on delivery)
            active_vehicles = self.repo.fetch_all("""
                SELECT COUNT(DISTINCT VehicleID) AS Total
                FROM DeliveryLog
                WHERE Delivery_Time IS NULL AND Pickup_Time IS NOT NULL
            """)
            active = active_vehicles[0]['Total'] if active_vehicles else 0
            self.active_vehicles_card.update_value(str(active))
            
            # Idle vehicles
            idle = max(0, total - active)
            self.idle_vehicles_card.update_value(str(idle))
            
            # Average deliveries per vehicle per day
            avg_per_vehicle = self.repo.fetch_all("""
                SELECT 
                    CAST(COUNT(*) AS FLOAT) / NULLIF(COUNT(DISTINCT VehicleID), 0) AS AvgPerVehicle
                FROM DeliveryLog
                WHERE CAST(Order_Date AS DATE) = CAST(GETDATE() AS DATE)
            """)
            avg_per_veh = round(avg_per_vehicle[0]['AvgPerVehicle'], 1) if avg_per_vehicle and avg_per_vehicle[0]['AvgPerVehicle'] else 0
            self.avg_per_vehicle_card.update_value(f"{avg_per_veh}")
            
        except Exception as e:
            logging.error(f"Error loading vehicle metrics: {e}")
    
    def _load_timeline_data(self):
        """Load and visualize timeline analysis"""
        try:
            # Daily delivery volume for last 7 days
            daily_data = self.repo.fetch_all("""
                SELECT 
                    CAST(Order_Date AS DATE) AS DeliveryDate,
                    COUNT(*) AS TotalDeliveries,
                    AVG(CAST(Delivery_Time AS FLOAT)) AS AvgDeliveryTime
                FROM DeliveryLog
                WHERE Order_Date >= DATEADD(DAY, -7, GETDATE())
                  AND Delivery_Time IS NOT NULL
                GROUP BY CAST(Order_Date AS DATE)
                ORDER BY DeliveryDate DESC
            """)
            
            self.timeline_text.config(state="normal")
            self.timeline_text.delete(1.0, tk.END)
            
            # Header
            self.timeline_text.insert(tk.END, "=" * 100 + "\n", "header")
            self.timeline_text.insert(tk.END, "   DELIVERY TRENDS - LAST 7 DAYS\n", "header")
            self.timeline_text.insert(tk.END, "=" * 100 + "\n\n", "header")
            
            if daily_data:
                # Find max for scaling bar chart
                max_deliveries = max(row['TotalDeliveries'] for row in daily_data)
                max_bar_length = 50;
                
                for row in daily_data:
                    date_str = str(row['DeliveryDate']);
                    count = row['TotalDeliveries'];
                    avg_time = round(row['AvgDeliveryTime'], 1) if row['AvgDeliveryTime'] else 0;
                    
                    # Scale bar length
                    bar_length = int((count / max_deliveries) * max_bar_length) if max_deliveries > 0 else 0
                    bar = "█" * bar_length;
                    
                    # Format line
                    line = f"  {date_str}  │ {bar} {count} deliveries (avg: {avg_time} min)\n";
                    self.timeline_text.insert(tk.END, line);
                
                self.timeline_text.insert(tk.END, "\n" + "=" * 100 + "\n\n");
                
                # Hourly distribution (if data available)
                hourly_data = self.repo.fetch_all("""
                    SELECT 
                        DATEPART(HOUR, CAST(Order_Time AS TIME)) AS DeliveryHour,
                        COUNT(*) AS TotalDeliveries
                    FROM DeliveryLog
                    WHERE Order_Date >= DATEADD(DAY, -7, GETDATE())
                    GROUP BY DATEPART(HOUR, CAST(Order_Time AS TIME))
                    ORDER BY DeliveryHour
                """)
                
                if hourly_data:
                    self.timeline_text.insert(tk.END, "   PEAK DELIVERY HOURS (Last 7 Days)\n", "header")
                    self.timeline_text.insert(tk.END, "=" * 100 + "\n\n", "header")
                    
                    max_hourly = max(row['TotalDeliveries'] for row in hourly_data)
                    
                    for row in hourly_data:
                        hour = row['DeliveryHour']
                        count = row['TotalDeliveries']
                        bar_length = int((count / max_hourly) * max_bar_length) if max_hourly > 0 else 0
                        bar = "█" * bar_length
                        
                        time_str = f"{hour:02d}:00"
                        line = f"  {time_str}  │ {bar} {count} deliveries\n"
                        self.timeline_text.insert(tk.END, line)
                    
                    self.timeline_text.insert(tk.END, "\n" + "=" * 100 + "\n")
            else:
                self.timeline_text.insert(tk.END, "  No data available for the last 7 days.\n\n")
            
            # Configure tags
            self.timeline_text.tag_config("header", font=("Courier New", config.FONT_SIZE_NORMAL, "bold"), foreground=config.PRIMARY_COLOR)
            self.timeline_text.config(state="disabled")
            
        except Exception as e:
            logging.error(f"Error loading timeline data: {e}")
    
    def _load_reports_table_data(self):
        """Load detailed reports into table"""
        try:
            # Clear existing data
            for item in self.reports_tree.get_children():
                self.reports_tree.delete(item)
            
            # Get limit from filter
            filter_value = self.report_filter.get()
            limit_map = {
                "All Records": "",
                "Last 50": "TOP 50",
                "Last 100": "TOP 100",
                "Last 500": "TOP 500"
            }
            limit = limit_map.get(filter_value, "TOP 100")
            
            # Fetch delivery reports - convert TIME to minutes
            reports = self.repo.fetch_all(f"""
                SELECT {limit}
                    Order_ID,
                    Order_Date,
                    VehicleID,
                    DATEDIFF(MINUTE, '00:00:00', Pickup_Time) AS Pickup_Time_Minutes,
                    DATEDIFF(MINUTE, '00:00:00', Delivery_Time) AS Delivery_Time_Minutes
                FROM DeliveryLog
                ORDER BY Order_Date DESC
            """)
            
            if reports:
                for idx, report in enumerate(reports):
                    order_id = report['Order_ID']
                    date = str(report['Order_Date'])[:19] if report['Order_Date'] else "N/A"
                    vehicle = report['VehicleID'] if report['VehicleID'] else "N/A"
                    
                    # Handle minutes (already converted from TIME)
                    pickup_minutes = report['Pickup_Time_Minutes']
                    delivery_minutes = report['Delivery_Time_Minutes']
                    
                    pickup = f"{pickup_minutes} min" if pickup_minutes is not None else "—"
                    delivery = f"{delivery_minutes} min" if delivery_minutes is not None else "—"
                    
                    # Calculate total time and status
                    if delivery_minutes is not None:
                        total = (pickup_minutes or 0) + delivery_minutes
                        total_time = f"{total} min"
                        status = "Completed"
                    elif pickup_minutes is not None:
                        total_time = "In Transit"
                        status = "In Transit"
                    else:
                        total_time = "Pending"
                        status = "Pending"
                    
                    # Alternate row colors
                    tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                    
                    self.reports_tree.insert("", "end", values=(
                        order_id, date, vehicle, pickup, delivery, total_time, status
                    ), tags=(tag,))
            
        except Exception as e:
            logging.error(f"Error loading reports table: {e}")
    
    def _sort_table(self, column):
        """Sort table by column (placeholder for future implementation)"""
        logging.info(f"Sorting by column: {column}")
        # Future: Implement sorting logic
        pass
    
    def _export_to_csv(self):
        """Export analytics data to CSV file"""
        try:
            from tkinter import filedialog
            import csv
            
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"delivery_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if not filename:
                return
            
            # Fetch all data for export
            export_data = self.repo.fetch_all("""
                SELECT 
                    Order_ID,
                    Order_Date,
                    VehicleID,
                    Pickup_Time,
                    Delivery_Time,
                    CASE 
                        WHEN Delivery_Time IS NOT NULL THEN 'Completed'
                        WHEN Pickup_Time IS NOT NULL THEN 'In Transit'
                        ELSE 'Pending'
                    END AS Status
                FROM DeliveryLog
                ORDER BY Order_Date DESC
            """)
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if export_data:
                    fieldnames = export_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(export_data)
            
            messagebox.showinfo("Success", f"Analytics exported successfully!\n\nSaved to:\n{filename}")
            logging.info(f"Analytics data exported to {filename}")
            
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")
    
    def destroy(self):
        """Clean up resources"""
        if self.repo:
            try:
                self.repo.close()
                logging.info("Analytics repository connection closed")
            except Exception as e:
                logging.error(f"Error closing analytics repository: {e}")
        super().destroy()
    
    def _retrain_ml_model(self):
        """Retrain the ML model with latest data"""
        try:
            from machine_learning.delivery_predictor import train_model_from_database
            
            # Confirm action
            result = messagebox.askyesno(
                "Retrain Model",
                "This will retrain the AI model with latest delivery data.\n\n"
            )
            
            if not result:
                return
            
            # Show progress
            progress_window = tk.Toplevel(self)
            progress_window.title("Training Model")
            progress_window.geometry("400x150")
            progress_window.transient(self)
            progress_window.grab_set()
            
            # Center window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
            y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
            progress_window.geometry(f"+{x}+{y}")
            
            tk.Label(
                progress_window,
                text="Training AI Model...",
                font=(config.FONT_FAMILY, config.FONT_SIZE_LARGE, "bold"),
                pady=20
            ).pack()
            
            progress_label = tk.Label(
                progress_window,
                text="Fetching training data from database...",
                font=(config.FONT_FAMILY, config.FONT_SIZE_NORMAL),
                fg=config.TEXT_SECONDARY
            )
            progress_label.pack(pady=10)
            
            progress_window.update()
            
            # Run training in background
            def train():
                try:
                    predictor, metrics = train_model_from_database()
                    progress_window.destroy()
                    
                    if predictor and metrics:
                        self.predictor = predictor
                        
                        messagebox.showinfo(
                            "Success",
                            f"Model trained successfully!\n\n"
                            f"R² Score: {metrics['test_r2']:.3f}\n"
                            f"MAE: {metrics['test_mae']:.2f} minutes\n\n"
                            "Click 'Load Predictions' to view results."
                        )
                        
                        # Show updated placeholder instead of auto-loading
                        self._show_prediction_placeholder()
                    else:
                        messagebox.showerror(
                            "Training Failed",
                            "Could not train model. Check console for details."
                        )
                except Exception as e:
                    progress_window.destroy()
                    messagebox.showerror("Error", f"Training failed: {str(e)}")
            
            # Start training after short delay
            self.after(100, train)
            
        except ImportError:
            messagebox.showerror(
                "Import Error",
                "Could not import training module.\n\n"
                "Ensure machine_learning/delivery_predictor.py exists."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrain model: {str(e)}")
    
    def _load_ml_predictions(self):
        """Load and display ML-powered delivery time predictions"""
        if not self.predictor or not self.predictor.is_trained:
            return
        
        try:
            # Fetch recent completed deliveries for validation
            query = """
                SELECT TOP 15
                    dl.Order_ID,
                    CAST(dl.Order_Time AS VARCHAR(8)) AS Order_Time,
                    dl.Order_Date,
                    dl.VehicleID,
                    dl.StoreID,
                    dl.Delivery_Time AS Actual_Delivery_Time,
                    CAST(dl.Pickup_Time AS VARCHAR(8)) AS Pickup_Time,
                    DATEDIFF(MINUTE, '00:00:00', dl.Order_Time) AS Order_Time_Minutes,
                    DATEDIFF(MINUTE, '00:00:00', dl.Pickup_Time) AS Pickup_Time_Minutes,
                    DATEPART(HOUR, dl.Order_Time) AS Order_Hour,
                    DATEPART(WEEKDAY, dl.Order_Date) AS Day_Of_Week
                FROM DeliveryLog dl
                WHERE dl.Order_Date >= DATEADD(DAY, -90, GETDATE())
                  AND dl.Delivery_Time IS NOT NULL
                  AND dl.Delivery_Time > 0
                  AND dl.Delivery_Time >= 20
                  AND dl.Delivery_Time <= 400
                  AND dl.Pickup_Time IS NOT NULL
                  AND dl.Order_Time IS NOT NULL
                ORDER BY dl.Order_Date DESC
            """
            
            rows = self.repo.fetch_all(query)
            
            self.prediction_text.config(state="normal")
            self.prediction_text.delete(1.0, "end")
            
            if not rows or len(rows) == 0:
                self.prediction_text.insert("end", "No recent delivery data available for predictions.\n\n")
                self.prediction_text.insert("end", "The system requires completed deliveries from the last 90 days\n")
                self.prediction_text.insert("end", "with valid delivery times (20-400 minutes).")
                self.prediction_text.config(state="disabled")
                return
            
            # Convert to DataFrame
            import pandas as pd
            import numpy as np
            
            order_data = pd.DataFrame(rows, columns=[
                'Order_ID', 'Order_Time', 'Order_Date', 'VehicleID', 
                'StoreID', 'Actual_Delivery_Time', 'Pickup_Time', 
                'Order_Time_Minutes', 'Pickup_Time_Minutes', 'Order_Hour', 'Day_Of_Week'
            ])
            
            # Calculate prep time
            order_data['Prep_Time_Minutes'] = (
                order_data['Pickup_Time_Minutes'] - order_data['Order_Time_Minutes']
            )
            order_data['Prep_Time_Minutes'] = order_data['Prep_Time_Minutes'].apply(
                lambda x: x if x >= 0 else x + 1440
            )
            
            # Add historical features if available
            if hasattr(self.predictor, 'store_avg_dict') and self.predictor.store_avg_dict:
                default_avg = order_data['Actual_Delivery_Time'].mean()
                order_data['Store_Avg_Time'] = order_data['StoreID'].map(
                    lambda x: self.predictor.store_avg_dict.get(x, {}).get('avg_time', default_avg)
                )
                order_data['Store_Avg_Prep'] = order_data['StoreID'].map(
                    lambda x: self.predictor.store_avg_dict.get(x, {}).get('avg_prep', 15)
                )
            
            if hasattr(self.predictor, 'vehicle_avg_dict') and self.predictor.vehicle_avg_dict:
                default_avg = order_data['Actual_Delivery_Time'].mean()
                order_data['Vehicle_Avg_Time'] = order_data['VehicleID'].map(
                    lambda x: self.predictor.vehicle_avg_dict.get(x, {}).get('avg_time', default_avg)
                )
            
            # Prepare input and generate predictions
            prediction_input = order_data.drop(columns=['Actual_Delivery_Time'])
            
            if hasattr(self.predictor, 'predict_with_confidence'):
                pred_results = self.predictor.predict_with_confidence(prediction_input)
                predictions = pred_results['predictions']
            else:
                predictions = self.predictor.predict(prediction_input)
            
            actual_values = order_data['Actual_Delivery_Time'].values
            
            # Calculate metrics
            from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
            
            mae = mean_absolute_error(actual_values, predictions)
            r2 = r2_score(actual_values, predictions)
            
            # Display simplified results
            self.prediction_text.config(state="normal")
            self.prediction_text.delete(1.0, "end")
            
            # Header
            self.prediction_text.insert("end", "Forecasted Delivery Times\n")
            self.prediction_text.insert("end", "=" * 70 + "\n\n")
            
            # Compact model info
            if hasattr(self.predictor, 'training_date') and self.predictor.training_date:
                train_date = self.predictor.training_date.strftime('%Y-%m-%d %H:%M')
                self.prediction_text.insert("end", f"Last Trained: {train_date}  |  ")
            
            if hasattr(self.predictor, 'training_samples'):
                self.prediction_text.insert("end", f"Samples: {self.predictor.training_samples}  |  ")
            
            # Always show LinearRegression
            model_type = type(self.predictor.model).__name__
            self.prediction_text.insert("end", f"Model: {model_type}\n")
            
            # Compact accuracy metrics
            self.prediction_text.insert("end", f"\nR-Squared: {r2:.3f}  |  MAE: {mae:.1f} min  |  ")
            accuracy_pct = max(0, 100 * (1 - mae / np.mean(actual_values)))
            self.prediction_text.insert("end", f"Accuracy: {accuracy_pct:.1f}%\n")
            self.prediction_text.insert("end", "=" * 70 + "\n\n")
            
            # Simplified predictions table
            self.prediction_text.insert("end", "Order ID          Predicted    Actual    Error\n")
            self.prediction_text.insert("end", "-" * 70 + "\n")
            
            for idx, (_, order) in enumerate(order_data.iterrows(), 1):
                order_id = str(order['Order_ID'])[:16].ljust(16)
                predicted = round(predictions[idx-1], 0)
                actual = order['Actual_Delivery_Time']
                error = abs(predicted - actual)
                
                # Format times
                def format_time(minutes):
                    hours = int(minutes // 60)
                    mins = int(minutes % 60)
                    if hours > 0:
                        return f"{hours}h {mins:02d}m"
                    return f"{int(minutes)}m"
                
                pred_str = format_time(predicted).ljust(10)
                actual_str = format_time(actual).ljust(8)
                error_str = f"{int(error)}m"
                
                self.prediction_text.insert("end", f"{order_id}  {pred_str}  {actual_str}  {error_str}\n")
            
            # Lock the text widget after inserting all content
            self.prediction_text.config(state="disabled")
            
        except Exception as e:
            logging.error(f"Error loading predictions: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message in the text widget
            self.prediction_text.config(state="normal")
            self.prediction_text.delete(1.0, "end")
            self.prediction_text.insert("end", f"Error loading predictions:\n{str(e)}")
            self.prediction_text.config(state="disabled")