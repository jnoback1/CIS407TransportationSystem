"""
Azure SQL Database connector using azure-identity
"""
import os
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
import struct
import pyodbc

def get_access_token():
    """
    Get Azure access token for database authentication.
    
    Attempts authentication in the following order:
    1. Azure CLI (if logged in via 'az login')
    2. VS Code Azure extension (if logged in)
    3. Interactive browser login
    
    Returns:
        str: Access token for Azure SQL Database
        
    Raises:
        Exception: If all authentication methods fail
    """
    try:
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/")
        return token.token
    except Exception as e:
        print(f"Default authentication failed: {e}")
        print("Opening browser for interactive login...")
        try:
            credential = InteractiveBrowserCredential()
            token = credential.get_token("https://database.windows.net/")
            return token.token
        except Exception as e2:
            print(f"Authentication failed: {e2}")
            print("\nTo fix this, run: az login")
            print("Or ensure you're logged into Azure in VS Code")
            raise

def connect_with_token():
    """
    Establish connection to Azure SQL Database using token-based authentication.
    
    Returns:
        pyodbc.Connection: Database connection object if successful, None otherwise
    """
    try:
        token = get_access_token()
        
        # Convert token to ODBC-compatible byte format
        token_bytes = token.encode("utf-16le")
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        # Connection string
        conn_str = (
            "Driver={ODBC Driver 18 for SQL Server};"
            "Server=jhutchensmsu.database.windows.net;"
            "Database=CIS407_Project_WillChristopher_JesseHutchens;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
        
        # SQL_COPT_SS_ACCESS_TOKEN = 1256
        conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})
        return conn
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def query_data(sql_query):
    """
    Execute SQL query and return results.
    
    Args:
        sql_query (str): SQL query to execute
        
    Returns:
        tuple: (column_names, rows) if successful, (None, None) otherwise
    """
    conn = connect_with_token()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return columns, rows
        except Exception as e:
            print(f"Query error: {e}")
            return None, None
        finally:
            conn.close()
    return None, None

def show_table_data(table_name, limit=10):
    """
    Display sample data from specified table.
    
    Args:
        table_name (str): Name of the table to query
        limit (int): Maximum number of rows to display
    """
    columns, rows = query_data(f"SELECT TOP {limit} * FROM {table_name}")
    if columns and rows:
        print(f"\n{table_name} ({len(rows)} rows):")
        print(f"Columns: {columns}")
        for row in rows:
            print(row)
    else:
        print(f"No data found in {table_name}")

def list_all_tables():
    """
    Retrieve list of all tables in the database.
    
    Returns:
        list: Table names
    """
    columns, rows = query_data("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    if rows:
        tables = [row[0] for row in rows]
        print(f"Available tables: {tables}")
        return tables
    return []

def test_connection():
    """Test database connection and display available tables."""
    conn = connect_with_token()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 5 * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            print("Connection successful. Available tables:")
            for row in cursor.fetchall():
                print(f"  - {row[2]}")
        finally:
            conn.close()

if __name__ == "__main__":
    print("Testing database connection...\n")
    test_connection()
    
    print("\nListing all tables...")
    tables = list_all_tables()
    
    print("\nSample data from each table:")
    for table in tables:
        show_table_data(table, 3)