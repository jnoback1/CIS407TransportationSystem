"""
Route Optimization Module
Uses greedy algorithms to optimize delivery routes based on:
- Pending delivery locations
- Vehicle capacity and availability
- Historical delivery time patterns
- Store/location clustering
"""
import logging
from datetime import datetime
from typing import List, Dict, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class RouteOptimizer:
    """Optimizes delivery routes using greedy clustering algorithms"""
    
    def __init__(self, repository):
        self.repo = repository
    
    def optimize_routes(self, max_deliveries_per_vehicle=10) -> Dict:
        """
        Optimize pending delivery routes
        
        Returns dict with:
        - optimized_routes: List of vehicle assignments
        - total_deliveries: Number of deliveries optimized
        - estimated_time_saved: Estimated time savings
        - success: Boolean
        - message: Status message
        """
        try:
            # Step 1: Get all pending deliveries
            pending_deliveries = self._get_pending_deliveries()
            
            if not pending_deliveries or len(pending_deliveries) == 0:
                return {
                    'success': False,
                    'message': 'No pending deliveries to optimize',
                    'optimized_routes': [],
                    'total_deliveries': 0,
                    'estimated_time_saved': 0
                }
            
            # Step 2: Get available vehicles
            available_vehicles = self._get_available_vehicles()
            
            if not available_vehicles or len(available_vehicles) == 0:
                return {
                    'success': False,
                    'message': 'No available vehicles for route optimization',
                    'optimized_routes': [],
                    'total_deliveries': 0,
                    'estimated_time_saved': 0
                }
            
            # Step 3: Cluster deliveries by store/location
            clustered_deliveries = self._cluster_deliveries_by_store(pending_deliveries)
            
            # Step 4: Assign clusters to vehicles using greedy algorithm
            vehicle_assignments = self._assign_clusters_to_vehicles(
                clustered_deliveries,
                available_vehicles,
                max_deliveries_per_vehicle
            )
            
            # Step 5: Calculate estimated time savings
            time_saved = self._estimate_time_savings(vehicle_assignments)
            
            # Step 6: Update database with optimized routes
            updated_count = self._update_delivery_routes(vehicle_assignments)
            
            return {
                'success': True,
                'message': f'Successfully optimized {updated_count} deliveries across {len(vehicle_assignments)} vehicles',
                'optimized_routes': vehicle_assignments,
                'total_deliveries': updated_count,
                'estimated_time_saved': time_saved,
                'vehicles_used': len(vehicle_assignments)
            }
            
        except Exception as e:
            logging.error(f"Route optimization failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Optimization error: {str(e)}',
                'optimized_routes': [],
                'total_deliveries': 0,
                'estimated_time_saved': 0
            }
    
    def _get_pending_deliveries(self) -> List[Dict]:
        """Get all pending deliveries (not yet assigned pickup time)"""
        query = """
            SELECT 
                Order_ID,
                StoreID,
                Order_Time,
                Order_Date,
                VehicleID
            FROM DeliveryLog
            WHERE Pickup_Time IS NULL
              AND Delivery_Time IS NULL
              AND Order_Date >= CAST(GETDATE() AS DATE)
            ORDER BY Order_Time
        """
        
        deliveries = self.repo.fetch_all(query)
        logging.info(f"Found {len(deliveries) if deliveries else 0} pending deliveries")
        return deliveries if deliveries else []
    
    def _get_available_vehicles(self) -> List[Dict]:
        """Get vehicles that are currently idle or have capacity"""
        query = """
            SELECT DISTINCT
                v.VehicleID,
                v.Status,
                COUNT(dl.Order_ID) AS Current_Load
            FROM Vehicles v
            LEFT JOIN DeliveryLog dl ON v.VehicleID = dl.VehicleID
                AND dl.Pickup_Time IS NOT NULL
                AND dl.Delivery_Time IS NULL
            WHERE v.Status IN ('idle', 'available', 'active')
            GROUP BY v.VehicleID, v.Status
            HAVING COUNT(dl.Order_ID) < 10
            ORDER BY Current_Load ASC
        """
        
        try:
            vehicles = self.repo.fetch_all(query)
            logging.info(f"Found {len(vehicles) if vehicles else 0} available vehicles")
            return vehicles if vehicles else []
        except Exception as e:
            logging.warning(f"Error fetching vehicles, using fallback: {e}")
            # Fallback: Get all vehicles from DeliveryLog
            fallback_query = """
                SELECT DISTINCT VehicleID, 0 AS Current_Load
                FROM DeliveryLog
                WHERE VehicleID IS NOT NULL
            """
            vehicles = self.repo.fetch_all(fallback_query)
            return vehicles if vehicles else []
    
    def _cluster_deliveries_by_store(self, deliveries: List[Dict]) -> Dict[str, List[Dict]]:
        """Group deliveries by store for efficient routing"""
        clusters = {}
        
        for delivery in deliveries:
            store_id = delivery['StoreID']
            if store_id not in clusters:
                clusters[store_id] = []
            clusters[store_id].append(delivery)
        
        logging.info(f"Clustered deliveries into {len(clusters)} store groups")
        return clusters
    
    def _assign_clusters_to_vehicles(
        self, 
        clusters: Dict[str, List[Dict]], 
        vehicles: List[Dict],
        max_per_vehicle: int
    ) -> List[Dict]:
        """
        Assign delivery clusters to vehicles using greedy algorithm
        Prioritizes:
        1. Vehicles with lowest current load
        2. Keeping store deliveries together (cluster integrity)
        3. Balancing load across fleet
        """
        assignments = []
        vehicle_loads = {v['VehicleID']: v.get('Current_Load', 0) for v in vehicles}
        
        # Sort clusters by size (largest first for better packing)
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        
        for store_id, store_deliveries in sorted_clusters:
            # Find vehicle with lowest load that can accommodate this cluster
            best_vehicle = None
            min_load = float('inf')
            
            for vehicle in vehicles:
                vehicle_id = vehicle['VehicleID']
                current_load = vehicle_loads[vehicle_id]
                
                # Check if vehicle can accommodate entire cluster
                if current_load + len(store_deliveries) <= max_per_vehicle:
                    if current_load < min_load:
                        min_load = current_load
                        best_vehicle = vehicle_id
            
            # If found suitable vehicle, assign entire cluster
            if best_vehicle:
                assignments.append({
                    'vehicle_id': best_vehicle,
                    'store_id': store_id,
                    'deliveries': store_deliveries,
                    'delivery_count': len(store_deliveries)
                })
                vehicle_loads[best_vehicle] += len(store_deliveries)
                logging.info(f"Assigned {len(store_deliveries)} deliveries from Store {store_id} to Vehicle {best_vehicle}")
            else:
                # Split cluster if too large for any single vehicle
                logging.warning(f"Cluster for Store {store_id} too large ({len(store_deliveries)}), splitting...")
                self._split_and_assign_cluster(
                    store_id, 
                    store_deliveries, 
                    vehicles, 
                    vehicle_loads, 
                    max_per_vehicle, 
                    assignments
                )
        
        return assignments
    
    def _split_and_assign_cluster(
        self,
        store_id: str,
        deliveries: List[Dict],
        vehicles: List[Dict],
        vehicle_loads: Dict,
        max_per_vehicle: int,
        assignments: List[Dict]
    ):
        """Split large cluster across multiple vehicles"""
        remaining = deliveries[:]
        
        while remaining:
            # Find vehicle with most capacity
            best_vehicle = None
            max_capacity = 0
            
            for vehicle in vehicles:
                vehicle_id = vehicle['VehicleID']
                capacity = max_per_vehicle - vehicle_loads[vehicle_id]
                if capacity > max_capacity:
                    max_capacity = capacity
                    best_vehicle = vehicle_id
            
            if not best_vehicle or max_capacity == 0:
                logging.warning(f"Unable to assign remaining {len(remaining)} deliveries - no vehicle capacity")
                break
            
            # Assign as many as possible to this vehicle
            chunk = remaining[:max_capacity]
            remaining = remaining[max_capacity:]
            
            assignments.append({
                'vehicle_id': best_vehicle,
                'store_id': store_id,
                'deliveries': chunk,
                'delivery_count': len(chunk)
            })
            vehicle_loads[best_vehicle] += len(chunk)
            logging.info(f"Assigned {len(chunk)} deliveries (split) from Store {store_id} to Vehicle {best_vehicle}")
    
    def _estimate_time_savings(self, assignments: List[Dict]) -> float:
        """
        Estimate time saved by optimization
        Assumes clustered deliveries reduce travel time by 20-30%
        """
        if not assignments:
            return 0.0
        
        total_deliveries = sum(a['delivery_count'] for a in assignments)
        
        # Rough estimate: Each delivery takes average 45 minutes
        # Clustering saves approximately 15 minutes per delivery
        estimated_savings = total_deliveries * 15
        
        return estimated_savings
    
    def _update_delivery_routes(self, assignments: List[Dict]) -> int:
        """Update database with optimized vehicle assignments"""
        updated_count = 0
        
        for assignment in assignments:
            vehicle_id = assignment['vehicle_id']
            deliveries = assignment['deliveries']
            
            # Update each delivery with assigned vehicle
            for delivery in deliveries:
                order_id = delivery['Order_ID']
                
                try:
                    update_query = """
                        UPDATE DeliveryLog
                        SET VehicleID = ?
                        WHERE Order_ID = ?
                    """
                    self.repo.execute(update_query, (vehicle_id, order_id))
                    updated_count += 1
                except Exception as e:
                    logging.error(f"Failed to update Order {order_id}: {e}")
        
        logging.info(f"Updated {updated_count} delivery routes in database")
        return updated_count
    
    def get_optimization_summary(self) -> Dict:
        """Get summary statistics for route optimization potential"""
        try:
            summary_query = """
                SELECT 
                    COUNT(*) AS Pending_Deliveries,
                    COUNT(DISTINCT StoreID) AS Unique_Stores,
                    COUNT(DISTINCT VehicleID) AS Vehicles_Available
                FROM DeliveryLog
                WHERE Pickup_Time IS NULL
                  AND Delivery_Time IS NULL
                  AND Order_Date >= CAST(GETDATE() AS DATE)
            """
            
            # ✅ Use fetch_all instead of fetch_one
            results = self.repo.fetch_all(summary_query)
            
            if results and len(results) > 0:
                result = results[0]  # Get first row
                return {
                    'pending_deliveries': result['Pending_Deliveries'],
                    'unique_stores': result['Unique_Stores'],
                    'vehicles_available': result['Vehicles_Available'],
                    'optimization_potential': 'High' if result['Pending_Deliveries'] > 20 else 'Medium' if result['Pending_Deliveries'] > 10 else 'Low'
                }
            
            return {
                'pending_deliveries': 0,
                'unique_stores': 0,
                'vehicles_available': 0,
                'optimization_potential': 'None'
            }
            
        except Exception as e:
            logging.error(f"Error getting optimization summary: {e}")
            return {
                'pending_deliveries': 0,
                'unique_stores': 0,
                'vehicles_available': 0,
                'optimization_potential': 'Unknown'
            }


def test_route_optimization():
    """Test route optimization functionality"""
    from backend.repository import AzureSqlRepository
    
    print("🗺️  Testing Route Optimization...")
    print("=" * 60)
    
    repo = AzureSqlRepository()
    optimizer = RouteOptimizer(repo)
    
    # Get summary first
    print("\n📊 Current Status:")
    summary = optimizer.get_optimization_summary()
    print(f"   Pending Deliveries: {summary['pending_deliveries']}")
    print(f"   Unique Stores: {summary['unique_stores']}")
    print(f"   Vehicles Available: {summary['vehicles_available']}")
    print(f"   Optimization Potential: {summary['optimization_potential']}")
    
    if summary['pending_deliveries'] == 0:
        print("\n⚠️  No pending deliveries to optimize")
        repo.close()
        return
    
    # Run optimization
    print("\n🔄 Running route optimization...")
    result = optimizer.optimize_routes(max_deliveries_per_vehicle=10)
    
    print("\n" + "=" * 60)
    if result['success']:
        print("✅ Optimization Complete!")
        print(f"   Total Deliveries Optimized: {result['total_deliveries']}")
        print(f"   Vehicles Used: {result['vehicles_used']}")
        print(f"   Estimated Time Saved: {result['estimated_time_saved']} minutes")
        print(f"\n   {result['message']}")
        
        if result['optimized_routes']:
            print("\n📋 Route Assignments:")
            for idx, route in enumerate(result['optimized_routes'], 1):
                print(f"   {idx}. Vehicle {route['vehicle_id']}: {route['delivery_count']} deliveries from Store {route['store_id']}")
    else:
        print(f"❌ Optimization Failed: {result['message']}")
    
    repo.close()


if __name__ == "__main__":
    test_route_optimization()