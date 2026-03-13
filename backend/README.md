# Warehouse Management System

## Setup & Run
1. Put both files (`server.py` and `index.html`) in the same folder
2. Run: `python3 server.py`
3. Open: http://localhost:8080
4. Login: **admin** / **admin123**

## Requirements
- Python 3.7+ (no extra libraries needed — uses only built-in `sqlite3`, `http.server`, `hashlib`, etc.)

## Features
- **Master Data**: Items, Locations, Suppliers, Units of Measure, Users
- **Inbound**: Goods receipt with line items, status tracking, inventory update on completion
- **Outbound**: Dispatch orders with line items, inventory deduction on completion
- **Reports**: 11 reports with charts (dashboard, by category, by location, trends, top items, etc.)
- **Utilities**: Database backup/restore (create, list, download, restore, delete backups)
- **Login/Logout**: Session-based auth from Users table

## Database
SQLite3 file: `wms.db` (auto-created on first run)
Backups stored in: `backups/` folder
