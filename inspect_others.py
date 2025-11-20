
from azure_token_connector import connect_with_token

def inspect_other_tables():
    try:
        conn = connect_with_token()
        cursor = conn.cursor()
        
        print("--- Columns in DropLocations ---")
        try:
            cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'DropLocations'")
            for col in cursor.fetchall(): print(col[0])
        except: pass

        print("\n--- Columns in amazon_delivery_info ---")
        try:
            cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'amazon_delivery_info'")
            for col in cursor.fetchall(): print(col[0])
        except: pass

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_other_tables()
