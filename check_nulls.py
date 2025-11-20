from backend.repository import AzureSqlRepository

def check_nullability():
    repo = AzureSqlRepository()
    query = """
    SELECT COLUMN_NAME, IS_NULLABLE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'DeliveryLog'
    """
    rows = repo.fetch_all(query)
    for row in rows:
        print(f"{row['COLUMN_NAME']}: {row['IS_NULLABLE']}")

if __name__ == "__main__":
    check_nullability()
