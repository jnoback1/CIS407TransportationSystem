"""Database Connection Module"""

import pyodbc
from azure.identity import DefaultAzureCredential
import struct


def connect_with_token():
    """Connect to Azure SQL Database using Azure AD authentication"""
    try:
        server = "jhutchensmsu.database.windows.net"
        database = "CIS407_Project_WillChristopher_JesseHutchens"
        driver = "{ODBC Driver 17 for SQL Server}"
        
        # Get Azure AD token
        credential = DefaultAzureCredential()
        token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string with token
        connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};"
        
        # Connect with access token
        conn = pyodbc.connect(connection_string, attrs_before={1256: token_struct})
        
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


if __name__ == "__main__":
    # Test connection
    conn = connect_with_token()
    if conn:
        print("✓ Connection successful!")
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"Database version: {row[0][:50]}...")
        conn.close()
    else:
        print("✗ Connection failed")
