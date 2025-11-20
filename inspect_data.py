from backend.repository import AzureSqlRepository

def inspect_delivery_log():
    repo = AzureSqlRepository()
    query = "SELECT TOP 10 * FROM DeliveryLog"
    rows = repo.fetch_all(query)
    for row in rows:
        print(row)

if __name__ == "__main__":
    inspect_delivery_log()
