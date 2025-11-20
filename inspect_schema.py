from backend.repository import AzureSqlRepository

def inspect_vehicles():
    repo = AzureSqlRepository()
    query = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Vehicles'"
    columns = repo.fetch_all(query)
    print("Columns in Vehicles table:")
    for col in columns:
        print(col['COLUMN_NAME'])

if __name__ == "__main__":
    inspect_vehicles()
