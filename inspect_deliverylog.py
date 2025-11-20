
from azure_token_connector import connect_with_token

def inspect_deliverylog():
    try:
        conn = connect_with_token()
        cursor = conn.cursor()
        
        print("--- Columns in DeliveryLog ---")
        query = """
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'DeliveryLog'
        """
        cursor.execute(query)
        columns = cursor.fetchall()
        print("--- Sample Data from DeliveryLog ---")
        query = "SELECT TOP 5 Pickup_Time, Delivery_Time FROM DeliveryLog"
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            print(f"Pickup: {row[0]} (Type: {type(row[0])}), Delivery: {row[1]} (Type: {type(row[1])})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_deliverylog()
