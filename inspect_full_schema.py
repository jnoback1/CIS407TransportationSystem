from backend.repository import AzureSqlRepository

def inspect_all_tables():
    repo = AzureSqlRepository()
    
    # Get all table names
    tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
    tables = repo.fetch_all(tables_query)
    
    for table in tables:
        table_name = table['TABLE_NAME']
        print(f"\nTable: {table_name}")
        
        # Get columns for each table
        columns_query = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'"
        columns = repo.fetch_all(columns_query)
        
        for col in columns:
            print(f"  - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")

if __name__ == "__main__":
    inspect_all_tables()
