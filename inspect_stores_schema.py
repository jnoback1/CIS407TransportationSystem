
from backend.db_connector import connect_with_token

conn = connect_with_token()
if conn:
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM DeliveryLog")
        columns = [column[0] for column in cursor.description]
        print(f"DeliveryLog Columns: {columns}")
    except Exception as e:
        print(e)
    finally:
        conn.close()
