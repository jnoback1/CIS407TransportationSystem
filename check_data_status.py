from backend.repository import AzureSqlRepository

def check_status_counts():
    repo = AzureSqlRepository()
    
    print("Checking counts...")
    
    # Active (Delivery_Time IS NULL)
    active = repo.fetch_all("SELECT COUNT(*) as C FROM DeliveryLog WHERE Delivery_Time IS NULL")
    print(f"Active (Delivery_Time IS NULL): {active[0]['C']}")
    
    # Pending (Pickup_Time IS NULL)
    pending = repo.fetch_all("SELECT COUNT(*) as C FROM DeliveryLog WHERE Pickup_Time IS NULL")
    print(f"Pending (Pickup_Time IS NULL): {pending[0]['C']}")
    
    # Total rows
    total = repo.fetch_all("SELECT COUNT(*) as C FROM DeliveryLog")
    print(f"Total rows: {total[0]['C']}")
    
    # Check sample rows to see what columns look like
    sample = repo.fetch_all("SELECT TOP 5 Order_ID, Order_Date, Order_Time, Pickup_Time, Delivery_Time, Status FROM DeliveryLog")
    for row in sample:
        print(row)

if __name__ == "__main__":
    check_status_counts()
