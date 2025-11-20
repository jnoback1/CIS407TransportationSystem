
import pyodbc
from backend.db_connector import connect_with_token

def inspect_data():
    conn = connect_with_token()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT TOP 10 * FROM DeliveryLog ORDER BY Order_Date DESC")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        print("--- Recent DeliveryLog Data ---")
        print(columns)
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_data()
