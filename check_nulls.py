
import pyodbc
from backend.db_connector import connect_with_token

def check_nullability():
    conn = connect_with_token()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'DeliveryLog'
        """)
        columns = cursor.fetchall()
        print("--- DeliveryLog Nullability ---")
        for col in columns:
            print(f"{col.COLUMN_NAME}: {col.IS_NULLABLE} ({col.DATA_TYPE})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_nullability()
