# CIS407 Transportation System
Transportation & Logistics Tracking System

## Overview
This application provides a graphical interface for viewing Amazon delivery data stored in Azure SQL Database. The system uses secure token-based authentication for database access.

## Quick Start

### Prerequisites
- Python 3.7 or higher
- Murray State University Azure account

### Setup for Windows

1. **Install ODBC Driver 18 for SQL Server** (Required!)
   - Download: https://go.microsoft.com/fwlink/?linkid=2249006
   - Run installer and follow prompts

2. **Install Azure CLI:**
   ```powershell
   winget install Microsoft.AzureCLI
   ```
   Or download from: https://aka.ms/installazurecliwindows

3. **Authenticate with Azure:**
   ```powershell
   az login
   ```
   Use your @murraystate.edu account

4. **Install Python packages:**
   ```bash
   pip install pyodbc azure-identity
   ```

5. **Run the application:**
   ```bash
   python delivery_viewer_gui.py
   ```

### Setup for macOS

1. **Install ODBC Driver:**
   ```bash
   brew install microsoft-odbc-18
   ```

2. **Install Azure CLI:**
   ```bash
   brew install azure-cli
   az login
   ```

3. **Install Python packages:**
   ```bash
   pip install pyodbc azure-identity
   ```

4. **Run the application:**
   ```bash
   python delivery_viewer_gui.py
   ```

## Authentication
The application uses Azure token-based authentication:
- No passwords stored in code
- Supports Azure CLI, VS Code Azure extension, or interactive browser login
- Tokens automatically refresh as needed

## Project Structure
- `azure_token_connector.py` - Database connection module (read-only access)
- `delivery_viewer_gui.py` - GUI application for data visualization
- `amazon_delivery.csv` - Source dataset (43,738 delivery records)

## Database Configuration
- **Server:** jhutchensmsu.database.windows.net
- **Database:** CIS407_Project_WillChristopher_JesseHutchens
- **Primary Table:** amazon_delivery_info

## Troubleshooting

### "ODBC Driver not found"
- **Windows:** Install ODBC Driver 18 from the link above
- **macOS:** Run `brew install microsoft-odbc-18`

### "Authentication failed"
- Run `az login` and sign in with your @murraystate.edu account
- Or ensure you're logged into Azure in VS Code

### "Login timeout expired"
- Check your internet connection
- Verify you have database access (contact instructor if needed)

## Team Members
- Will Christopher (wchristopher1@murraystate.edu)
- Jesse Hutchens

## Course Information
CIS 407 - Database Systems
Murray State University
