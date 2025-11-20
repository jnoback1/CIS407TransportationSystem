from backend.repository import AzureSqlRepository

def analyze_data():
    repo = AzureSqlRepository()
    
    print("--- Status Counts ---")
    statuses = repo.fetch_all("SELECT Status, COUNT(*) as C FROM DeliveryLog GROUP BY Status")
    for s in statuses:
        print(f"Status: {s['Status']}, Count: {s['C']}")
        
    print("\n--- Null Checks ---")
    nulls = repo.fetch_all("""
        SELECT 
            SUM(CASE WHEN Delivery_Time IS NULL THEN 1 ELSE 0 END) as NullDeliveryTime,
            SUM(CASE WHEN Pickup_Time IS NULL THEN 1 ELSE 0 END) as NullPickupTime
        FROM DeliveryLog
    """)
    print(f"Null Delivery_Time: {nulls[0]['NullDeliveryTime']}")
    print(f"Null Pickup_Time: {nulls[0]['NullPickupTime']}")

    print("\n--- Recent Orders ---")
    recent = repo.fetch_all("SELECT TOP 5 * FROM DeliveryLog ORDER BY Order_Date DESC")
    for r in recent:
        print(r)

if __name__ == "__main__":
    analyze_data()
