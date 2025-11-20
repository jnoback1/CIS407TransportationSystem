
from azure_token_connector import connect_with_token

def inspect_stores():
    try:
        conn = connect_with_token()
        cursor = conn.cursor()
        
        print("--- Columns in Stores ---")
        query = """
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Stores'
        """
        cursor.execute(query)
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]}: {col[1]}")
            
        print("\n--- Sample Data from Stores ---")
        cursor.execute("SELECT TOP 3 * FROM Stores")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_stores()
