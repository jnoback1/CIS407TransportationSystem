# CIS407 Transportation & Logistics Tracking System

A comprehensive logistics management system built with Python, Tkinter, and Azure SQL Database for tracking deliveries, optimizing routes, and managing transportation operations.

## Features

### Core Functionality
- **Real-time Delivery Tracking**: Monitor deliveries from order to completion
- **Route Optimization**: Intelligent route planning using greedy clustering algorithms
- **Interactive Map Visualization**: View delivery routes on an interactive map with real-time data
- **Vehicle Management**: Track vehicle status, capacity, and assignments
- **Store & Location Management**: Manage stores and drop-off locations across India
- **Analytics Dashboard**: Comprehensive metrics and performance insights

### Advanced Features
- **Hierarchical Data Modeling**: Optimized for Azure Cosmos DB patterns
- **Multi-Vehicle Route Planning**: Assign deliveries to vehicles based on capacity and location
- **Historical Route Analysis**: Review completed delivery routes with timing data
- **Geospatial Routing**: Integration with OpenStreetMap Routing Service (OSRM)
- **User Role Management**: Driver, Manager, and Admin access levels

## Prerequisites

- Python 3.8 or higher
- Azure SQL Database account (or SQL Server)
- Internet connection (for map features)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CIS407TransportationSystem.git
cd CIS407TransportationSystem
```

### 2. Install Required Packages

```bash
pip install pyodbc python-dotenv tkintermapview requests numpy pandas
```

**Package Overview:**
- `pyodbc` - Azure SQL Database connectivity
- `python-dotenv` - Environment variable management
- `tkintermapview` - Interactive map widget
- `requests` - HTTP routing API calls
- `numpy` & `pandas` - Data analysis (optional, for advanced features)

## Connecting to Azure SQL Database

### Quick Setup Guide

**1. Get Database Credentials**

Contact admin for:
- Database server name
- Database name
- Username
- Password

**2. Create `.env` File**

Create a `.env` file in your project root with the provided credentials:

```env
DB_SERVER=cis407-server.database.windows.net
DB_DATABASE=TransportationDB
DB_USERNAME=your-username
DB_PASSWORD=your-password
DB_DRIVER={ODBC Driver 18 for SQL Server}
```

Replace the values with your actual credentials.

**3. Install ODBC Driver**

Download and install the [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**Windows:** Run the installer
**Mac:** `brew install msodbcsql18`
**Linux:** Follow the [official guide](https://learn.microsoft.com/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)

**4. Test Your Connection**

```python
from backend.repository import AzureSqlRepository

repo = AzureSqlRepository()
stores = repo.fetch_all("SELECT COUNT(*) AS count FROM Stores")
print(f"✅ Connected! Found {stores[0]['count']} stores.")
repo.close()
```

### Common Issues

| Error | Solution |
|-------|----------|
| "Login failed" | Double-check username/password in `.env` |
| "Cannot open server" | Contact instructor to add your IP to firewall |
| "ODBC Driver not found" | Install ODBC Driver 18 or try Driver 17 |
| Connection timeout | Verify server name includes `.database.windows.net` |

## Authors
Jesse Hutchens
Will Christopher
Justice Noback

