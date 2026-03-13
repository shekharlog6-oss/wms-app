#!/usr/bin/env python3
"""Warehouse Management System - Python + SQLite3 Backend"""

import sqlite3
import json
import os
import shutil
import hashlib
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import io

DB_PATH = "warehouse.db"
BACKUP_DIR = "backups"

# ── Database initialization ──────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'operator',
        email TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS units_of_measure (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        zone TEXT,
        aisle TEXT,
        rack TEXT,
        bin TEXT,
        capacity REAL DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        uom_id INTEGER REFERENCES units_of_measure(id),
        supplier_id INTEGER REFERENCES suppliers(id),
        reorder_point REAL DEFAULT 0,
        reorder_qty REAL DEFAULT 0,
        unit_cost REAL DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS inbound (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference_no TEXT UNIQUE NOT NULL,
        supplier_id INTEGER REFERENCES suppliers(id),
        received_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_by INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS inbound_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inbound_id INTEGER REFERENCES inbound(id) ON DELETE CASCADE,
        item_id INTEGER REFERENCES items(id),
        location_id INTEGER REFERENCES locations(id),
        qty_expected REAL DEFAULT 0,
        qty_received REAL DEFAULT 0,
        unit_cost REAL DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS outbound (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference_no TEXT UNIQUE NOT NULL,
        destination TEXT,
        dispatch_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_by INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS outbound_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outbound_id INTEGER REFERENCES outbound(id) ON DELETE CASCADE,
        item_id INTEGER REFERENCES items(id),
        location_id INTEGER REFERENCES locations(id),
        qty_requested REAL DEFAULT 0,
        qty_dispatched REAL DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER REFERENCES items(id),
        location_id INTEGER REFERENCES locations(id),
        quantity REAL DEFAULT 0,
        last_updated TEXT DEFAULT (datetime('now')),
        UNIQUE(item_id, location_id)
    );
    """)

    # Default admin user (password: admin123)
    pwd_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""INSERT OR IGNORE INTO users (username,password_hash,full_name,role,email)
                 VALUES ('admin',?,'System Administrator','admin','admin@wms.local')""", (pwd_hash,))

    # Seed UoMs
    uoms = [('PCS','Pieces','Individual pieces'),('KG','Kilograms','Weight in kg'),
            ('LTR','Litres','Volume in litres'),('MTR','Metres','Length in metres'),
            ('BOX','Box','Packaged box'),('CTN','Carton','Carton/case')]
    c.executemany("INSERT OR IGNORE INTO units_of_measure (code,name,description) VALUES (?,?,?)", uoms)

    # Seed Suppliers
    suppliers = [
        ('SUP001','Acme Corp','John Doe','555-1001','john@acme.com','123 Main St'),
        ('SUP002','Global Supplies','Jane Smith','555-1002','jane@global.com','456 Park Ave'),
        ('SUP003','FastFreight Ltd','Bob Lee','555-1003','bob@fastfreight.com','789 Dock Rd'),
    ]
    c.executemany("INSERT OR IGNORE INTO suppliers (code,name,contact_person,phone,email,address) VALUES (?,?,?,?,?,?)", suppliers)

    # Seed Locations
    locations = [
        ('LOC-A01','Aisle A Rack 01','A','A','01','01',500),
        ('LOC-A02','Aisle A Rack 02','A','A','02','01',500),
        ('LOC-B01','Aisle B Rack 01','B','B','01','01',750),
        ('LOC-B02','Aisle B Rack 02','B','B','02','01',750),
        ('LOC-RECV','Receiving Dock','RECV','','','',1000),
        ('LOC-DISP','Dispatch Dock','DISP','','','',1000),
    ]
    c.executemany("INSERT OR IGNORE INTO locations (code,name,zone,aisle,rack,bin,capacity) VALUES (?,?,?,?,?,?,?)", locations)

    # Seed Items
    c.execute("SELECT id FROM units_of_measure WHERE code='PCS'")
    uom_row = c.fetchone()
    c.execute("SELECT id FROM suppliers WHERE code='SUP001'")
    sup_row = c.fetchone()
    if uom_row and sup_row:
        uom_id, sup_id = uom_row[0], sup_row[0]
        items = [
            ('SKU-001','Widget A','Standard widget type A','Electronics',uom_id,sup_id,50,100,12.50),
            ('SKU-002','Widget B','Standard widget type B','Electronics',uom_id,sup_id,30,60,18.00),
            ('SKU-003','Bolt M8','M8 bolt 50mm','Hardware',uom_id,sup_id,200,500,0.50),
            ('SKU-004','Cable 5m','USB cable 5m','Electronics',uom_id,sup_id,20,40,8.75),
            ('SKU-005','Lubricant','General purpose lubricant','Maintenance',uom_id,sup_id,10,25,15.00),
        ]
        c.executemany("""INSERT OR IGNORE INTO items
            (sku,name,description,category,uom_id,supplier_id,reorder_point,reorder_qty,unit_cost)
            VALUES (?,?,?,?,?,?,?,?,?)""", items)

    conn.commit()
    conn.close()
    print("Database initialized.")

# ── Helpers ──────────────────────────────────────────────────────────────────

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def rows_to_list(rows):
    return [dict(r) for r in rows]

def ok(data=None, message="OK"):
    return {"success": True, "message": message, "data": data}

def err(message="Error"):
    return {"success": False, "message": message, "data": None}

def gen_ref(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ── API handlers ─────────────────────────────────────────────────────────────

def handle_login(body):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password_hash=? AND active=1",
        (body.get("username",""), hash_password(body.get("password","")))
    ).fetchone()
    conn.close()
    if row:
        u = dict(row)
        u.pop("password_hash", None)
        return ok(u, "Login successful")
    return err("Invalid credentials")

# ── Generic CRUD ──────────────────────────────────────────────────────────────

TABLES = {
    "users": {
        "fields": ["username","full_name","role","email","active"],
        "search": ["username","full_name","email"]
    },
    "items": {
        "fields": ["sku","name","description","category","uom_id","supplier_id","reorder_point","reorder_qty","unit_cost","active"],
        "search": ["sku","name","category"]
    },
    "locations": {
        "fields": ["code","name","zone","aisle","rack","bin","capacity","active"],
        "search": ["code","name","zone"]
    },
    "suppliers": {
        "fields": ["code","name","contact_person","phone","email","address","active"],
        "search": ["code","name","email"]
    },
    "units_of_measure": {
        "fields": ["code","name","description"],
        "search": ["code","name"]
    },
}

def handle_list(table, params):
    if table not in TABLES: return err("Unknown table")
    conn = get_db()
    search = params.get("search", [""])[0]
    if search:
        cols = TABLES[table]["search"]
        where = " OR ".join([f"{c} LIKE ?" for c in cols])
        rows = conn.execute(f"SELECT * FROM {table} WHERE {where}", [f"%{search}%"]*len(cols)).fetchall()
    else:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    conn.close()
    return ok(rows_to_list(rows))

def handle_get(table, record_id):
    if table not in TABLES: return err("Unknown table")
    conn = get_db()
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
    conn.close()
    return ok(dict(row) if row else None)

def handle_create(table, body):
    if table not in TABLES: return err("Unknown table")
    fields = TABLES[table]["fields"]
    data = {f: body.get(f) for f in fields if f in body}
    if table == "users":
        if "password" in body:
            data["password_hash"] = hash_password(body["password"])
        else:
            return err("Password required")
        data.pop("password", None)
        fields_to_insert = list(data.keys())
    else:
        fields_to_insert = list(data.keys())
    if not fields_to_insert: return err("No data")
    placeholders = ",".join(["?"]*len(fields_to_insert))
    cols = ",".join(fields_to_insert)
    try:
        conn = get_db()
        cur = conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
        new_id = cur.lastrowid
        conn.commit()
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (new_id,)).fetchone()
        conn.close()
        r = dict(row)
        r.pop("password_hash", None)
        return ok(r, "Created successfully")
    except sqlite3.IntegrityError as e:
        return err(str(e))

def handle_update(table, record_id, body):
    if table not in TABLES: return err("Unknown table")
    fields = TABLES[table]["fields"]
    data = {f: body.get(f) for f in fields if f in body}
    if table == "users" and "password" in body and body["password"]:
        data["password_hash"] = hash_password(body["password"])
    if not data: return err("No data to update")
    set_clause = ",".join([f"{k}=?" for k in data.keys()])
    try:
        conn = get_db()
        conn.execute(f"UPDATE {table} SET {set_clause} WHERE id=?", list(data.values()) + [record_id])
        conn.commit()
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,)).fetchone()
        conn.close()
        r = dict(row)
        r.pop("password_hash", None)
        return ok(r, "Updated successfully")
    except sqlite3.IntegrityError as e:
        return err(str(e))

def handle_delete(table, record_id):
    if table not in TABLES: return err("Unknown table")
    conn = get_db()
    conn.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    return ok(None, "Deleted successfully")

# ── Inbound ───────────────────────────────────────────────────────────────────

def handle_inbound_list(params):
    conn = get_db()
    rows = conn.execute("""
        SELECT i.*, s.name as supplier_name, u.full_name as created_by_name
        FROM inbound i
        LEFT JOIN suppliers s ON i.supplier_id=s.id
        LEFT JOIN users u ON i.created_by=u.id
        ORDER BY i.created_at DESC
    """).fetchall()
    conn.close()
    return ok(rows_to_list(rows))

def handle_inbound_get(inbound_id):
    conn = get_db()
    header = conn.execute("""
        SELECT i.*, s.name as supplier_name
        FROM inbound i LEFT JOIN suppliers s ON i.supplier_id=s.id
        WHERE i.id=?
    """, (inbound_id,)).fetchone()
    lines = conn.execute("""
        SELECT il.*, it.sku, it.name as item_name, l.code as location_code
        FROM inbound_lines il
        LEFT JOIN items it ON il.item_id=it.id
        LEFT JOIN locations l ON il.location_id=l.id
        WHERE il.inbound_id=?
    """, (inbound_id,)).fetchall()
    conn.close()
    if not header: return err("Not found")
    return ok({"header": dict(header), "lines": rows_to_list(lines)})

def handle_inbound_create(body):
    conn = get_db()
    ref = body.get("reference_no") or gen_ref("INB")
    try:
        cur = conn.execute("""
            INSERT INTO inbound (reference_no,supplier_id,received_date,status,notes,created_by)
            VALUES (?,?,?,?,?,?)
        """, (ref, body.get("supplier_id"), body.get("received_date"), body.get("status","pending"),
              body.get("notes"), body.get("created_by")))
        inb_id = cur.lastrowid
        for line in body.get("lines", []):
            conn.execute("""
                INSERT INTO inbound_lines (inbound_id,item_id,location_id,qty_expected,qty_received,unit_cost,notes)
                VALUES (?,?,?,?,?,?,?)
            """, (inb_id, line.get("item_id"), line.get("location_id"),
                  line.get("qty_expected",0), line.get("qty_received",0),
                  line.get("unit_cost",0), line.get("notes")))
        if body.get("status") == "completed":
            _update_inventory_inbound(conn, inb_id)
        conn.commit()
        conn.close()
        return ok({"id": inb_id, "reference_no": ref}, "Inbound created")
    except sqlite3.IntegrityError as e:
        conn.close()
        return err(str(e))

def handle_inbound_update(inbound_id, body):
    conn = get_db()
    old = conn.execute("SELECT status FROM inbound WHERE id=?", (inbound_id,)).fetchone()
    conn.execute("""
        UPDATE inbound SET supplier_id=?,received_date=?,status=?,notes=?
        WHERE id=?
    """, (body.get("supplier_id"), body.get("received_date"), body.get("status"),
          body.get("notes"), inbound_id))
    conn.execute("DELETE FROM inbound_lines WHERE inbound_id=?", (inbound_id,))
    for line in body.get("lines", []):
        conn.execute("""
            INSERT INTO inbound_lines (inbound_id,item_id,location_id,qty_expected,qty_received,unit_cost,notes)
            VALUES (?,?,?,?,?,?,?)
        """, (inbound_id, line.get("item_id"), line.get("location_id"),
              line.get("qty_expected",0), line.get("qty_received",0),
              line.get("unit_cost",0), line.get("notes")))
    if old and old[0] != "completed" and body.get("status") == "completed":
        _update_inventory_inbound(conn, inbound_id)
    conn.commit()
    conn.close()
    return ok(None, "Updated")

def _update_inventory_inbound(conn, inbound_id):
    lines = conn.execute(
        "SELECT item_id,location_id,qty_received FROM inbound_lines WHERE inbound_id=?", (inbound_id,)
    ).fetchall()
    for l in lines:
        conn.execute("""
            INSERT INTO inventory (item_id,location_id,quantity,last_updated)
            VALUES (?,?,?,datetime('now'))
            ON CONFLICT(item_id,location_id) DO UPDATE SET
            quantity=quantity+excluded.quantity, last_updated=excluded.last_updated
        """, (l["item_id"], l["location_id"], l["qty_received"]))

# ── Outbound ──────────────────────────────────────────────────────────────────

def handle_outbound_list(params):
    conn = get_db()
    rows = conn.execute("""
        SELECT o.*, u.full_name as created_by_name
        FROM outbound o
        LEFT JOIN users u ON o.created_by=u.id
        ORDER BY o.created_at DESC
    """).fetchall()
    conn.close()
    return ok(rows_to_list(rows))

def handle_outbound_get(outbound_id):
    conn = get_db()
    header = conn.execute("SELECT * FROM outbound WHERE id=?", (outbound_id,)).fetchone()
    lines = conn.execute("""
        SELECT ol.*, it.sku, it.name as item_name, l.code as location_code
        FROM outbound_lines ol
        LEFT JOIN items it ON ol.item_id=it.id
        LEFT JOIN locations l ON ol.location_id=l.id
        WHERE ol.outbound_id=?
    """, (outbound_id,)).fetchall()
    conn.close()
    if not header: return err("Not found")
    return ok({"header": dict(header), "lines": rows_to_list(lines)})

def handle_outbound_create(body):
    conn = get_db()
    ref = body.get("reference_no") or gen_ref("OUT")
    try:
        cur = conn.execute("""
            INSERT INTO outbound (reference_no,destination,dispatch_date,status,notes,created_by)
            VALUES (?,?,?,?,?,?)
        """, (ref, body.get("destination"), body.get("dispatch_date"), body.get("status","pending"),
              body.get("notes"), body.get("created_by")))
        out_id = cur.lastrowid
        for line in body.get("lines", []):
            conn.execute("""
                INSERT INTO outbound_lines (outbound_id,item_id,location_id,qty_requested,qty_dispatched,notes)
                VALUES (?,?,?,?,?,?)
            """, (out_id, line.get("item_id"), line.get("location_id"),
                  line.get("qty_requested",0), line.get("qty_dispatched",0), line.get("notes")))
        if body.get("status") == "completed":
            _update_inventory_outbound(conn, out_id)
        conn.commit()
        conn.close()
        return ok({"id": out_id, "reference_no": ref}, "Outbound created")
    except sqlite3.IntegrityError as e:
        conn.close()
        return err(str(e))

def handle_outbound_update(outbound_id, body):
    conn = get_db()
    old = conn.execute("SELECT status FROM outbound WHERE id=?", (outbound_id,)).fetchone()
    conn.execute("""
        UPDATE outbound SET destination=?,dispatch_date=?,status=?,notes=?
        WHERE id=?
    """, (body.get("destination"), body.get("dispatch_date"), body.get("status"),
          body.get("notes"), outbound_id))
    conn.execute("DELETE FROM outbound_lines WHERE outbound_id=?", (outbound_id,))
    for line in body.get("lines", []):
        conn.execute("""
            INSERT INTO outbound_lines (outbound_id,item_id,location_id,qty_requested,qty_dispatched,notes)
            VALUES (?,?,?,?,?,?)
        """, (outbound_id, line.get("item_id"), line.get("location_id"),
              line.get("qty_requested",0), line.get("qty_dispatched",0), line.get("notes")))
    if old and old[0] != "completed" and body.get("status") == "completed":
        _update_inventory_outbound(conn, outbound_id)
    conn.commit()
    conn.close()
    return ok(None, "Updated")

def _update_inventory_outbound(conn, outbound_id):
    lines = conn.execute(
        "SELECT item_id,location_id,qty_dispatched FROM outbound_lines WHERE outbound_id=?", (outbound_id,)
    ).fetchall()
    for l in lines:
        conn.execute("""
            INSERT INTO inventory (item_id,location_id,quantity,last_updated)
            VALUES (?,?,0,datetime('now'))
            ON CONFLICT(item_id,location_id) DO UPDATE SET
            quantity=MAX(0,quantity-?), last_updated=datetime('now')
        """, (l["item_id"], l["location_id"], l["qty_dispatched"]))

# ── Reports ───────────────────────────────────────────────────────────────────

def handle_reports(report_type):
    conn = get_db()
    if report_type == "dashboard":
        items_count = conn.execute("SELECT COUNT(*) FROM items WHERE active=1").fetchone()[0]
        locations_count = conn.execute("SELECT COUNT(*) FROM locations WHERE active=1").fetchone()[0]
        suppliers_count = conn.execute("SELECT COUNT(*) FROM suppliers WHERE active=1").fetchone()[0]
        uom_count = conn.execute("SELECT COUNT(*) FROM units_of_measure").fetchone()[0]
        users_count = conn.execute("SELECT COUNT(*) FROM users WHERE active=1").fetchone()[0]
        inbound_count = conn.execute("SELECT COUNT(*) FROM inbound").fetchone()[0]
        outbound_count = conn.execute("SELECT COUNT(*) FROM outbound").fetchone()[0]
        inbound_pending = conn.execute("SELECT COUNT(*) FROM inbound WHERE status='pending'").fetchone()[0]
        outbound_pending = conn.execute("SELECT COUNT(*) FROM outbound WHERE status='pending'").fetchone()[0]
        total_inventory = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory").fetchone()[0]
        conn.close()
        return ok({
            "items": items_count, "locations": locations_count,
            "suppliers": suppliers_count, "uom": uom_count, "users": users_count,
            "inbound_total": inbound_count, "outbound_total": outbound_count,
            "inbound_pending": inbound_pending, "outbound_pending": outbound_pending,
            "total_inventory": total_inventory
        })

    elif report_type == "items_by_category":
        rows = conn.execute("""
            SELECT COALESCE(category,'Uncategorized') as category, COUNT(*) as count
            FROM items WHERE active=1 GROUP BY category
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "inventory_by_location":
        rows = conn.execute("""
            SELECT l.code, l.name, SUM(inv.quantity) as total_qty, COUNT(DISTINCT inv.item_id) as item_count
            FROM inventory inv
            JOIN locations l ON inv.location_id=l.id
            GROUP BY l.id ORDER BY total_qty DESC
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "inbound_by_status":
        rows = conn.execute("""
            SELECT status, COUNT(*) as count FROM inbound GROUP BY status
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "outbound_by_status":
        rows = conn.execute("""
            SELECT status, COUNT(*) as count FROM outbound GROUP BY status
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "inbound_trend":
        rows = conn.execute("""
            SELECT substr(received_date,1,7) as month, COUNT(*) as count,
                   SUM((SELECT SUM(qty_received) FROM inbound_lines WHERE inbound_id=inbound.id)) as total_qty
            FROM inbound GROUP BY month ORDER BY month DESC LIMIT 12
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "outbound_trend":
        rows = conn.execute("""
            SELECT substr(dispatch_date,1,7) as month, COUNT(*) as count,
                   SUM((SELECT SUM(qty_dispatched) FROM outbound_lines WHERE outbound_id=outbound.id)) as total_qty
            FROM outbound GROUP BY month ORDER BY month DESC LIMIT 12
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "top_items_inbound":
        rows = conn.execute("""
            SELECT it.sku, it.name, SUM(il.qty_received) as total_received
            FROM inbound_lines il JOIN items it ON il.item_id=it.id
            GROUP BY it.id ORDER BY total_received DESC LIMIT 10
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "top_items_outbound":
        rows = conn.execute("""
            SELECT it.sku, it.name, SUM(ol.qty_dispatched) as total_dispatched
            FROM outbound_lines ol JOIN items it ON ol.item_id=it.id
            GROUP BY it.id ORDER BY total_dispatched DESC LIMIT 10
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "suppliers_activity":
        rows = conn.execute("""
            SELECT s.name, COUNT(i.id) as inbound_count,
                   COALESCE(SUM((SELECT SUM(qty_received) FROM inbound_lines WHERE inbound_id=i.id)),0) as total_received
            FROM suppliers s
            LEFT JOIN inbound i ON s.id=i.supplier_id
            GROUP BY s.id ORDER BY total_received DESC
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "inventory_value":
        rows = conn.execute("""
            SELECT it.sku, it.name, it.category,
                   SUM(inv.quantity) as total_qty,
                   it.unit_cost,
                   SUM(inv.quantity)*it.unit_cost as total_value
            FROM inventory inv
            JOIN items it ON inv.item_id=it.id
            GROUP BY it.id ORDER BY total_value DESC
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "inventory_history":
        # Full transaction history: all inbound receipts + outbound dispatches
        # joined to items, locations, suppliers — oracle-style history
        rows = conn.execute("""
            SELECT
                il.id                                        AS txn_id,
                'RECEIPT'                                    AS txn_type,
                ib.reference_no                             AS document_no,
                ib.received_date                            AS txn_date,
                ib.status                                   AS document_status,
                it.sku                                      AS item_sku,
                it.name                                     AS item_name,
                it.category                                 AS item_category,
                u.code                                      AS uom,
                l.code                                      AS location_code,
                l.name                                      AS location_name,
                l.zone                                      AS zone,
                s.name                                      AS supplier_name,
                il.qty_expected                             AS qty_expected,
                il.qty_received                             AS qty_moved,
                0                                           AS qty_dispatched,
                il.unit_cost                                AS unit_cost,
                (il.qty_received * il.unit_cost)            AS txn_value,
                ib.created_at                               AS created_at,
                us.full_name                                AS created_by
            FROM inbound_lines il
            JOIN inbound ib       ON il.inbound_id  = ib.id
            JOIN items it         ON il.item_id     = it.id
            LEFT JOIN locations l ON il.location_id = l.id
            LEFT JOIN suppliers s ON ib.supplier_id = s.id
            LEFT JOIN units_of_measure u ON it.uom_id = u.id
            LEFT JOIN users us    ON ib.created_by  = us.id

            UNION ALL

            SELECT
                ol.id                                       AS txn_id,
                'DISPATCH'                                  AS txn_type,
                ob.reference_no                            AS document_no,
                ob.dispatch_date                           AS txn_date,
                ob.status                                  AS document_status,
                it.sku                                     AS item_sku,
                it.name                                    AS item_name,
                it.category                                AS item_category,
                u.code                                     AS uom,
                l.code                                     AS location_code,
                l.name                                     AS location_name,
                l.zone                                     AS zone,
                COALESCE(ob.destination,'—')               AS supplier_name,
                ol.qty_requested                           AS qty_expected,
                0                                          AS qty_moved,
                ol.qty_dispatched                          AS qty_dispatched,
                0                                          AS unit_cost,
                0                                          AS txn_value,
                ob.created_at                              AS created_at,
                us.full_name                               AS created_by
            FROM outbound_lines ol
            JOIN outbound ob      ON ol.outbound_id = ob.id
            JOIN items it         ON ol.item_id     = it.id
            LEFT JOIN locations l ON ol.location_id = l.id
            LEFT JOIN units_of_measure u ON it.uom_id = u.id
            LEFT JOIN users us    ON ob.created_by  = us.id

            ORDER BY txn_date DESC, created_at DESC
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    elif report_type == "inventory_snapshot":
        # Current on-hand inventory snapshot per item+location
        rows = conn.execute("""
            SELECT
                it.sku, it.name AS item_name, it.category,
                u.code          AS uom,
                l.code          AS location_code, l.name AS location_name, l.zone,
                s.name          AS supplier_name,
                inv.quantity    AS on_hand_qty,
                it.unit_cost,
                (inv.quantity * it.unit_cost) AS stock_value,
                it.reorder_point,
                CASE WHEN inv.quantity <= 0           THEN 'OUT_OF_STOCK'
                     WHEN inv.quantity <= it.reorder_point THEN 'BELOW_REORDER'
                     ELSE 'IN_STOCK' END              AS stock_status,
                inv.last_updated
            FROM inventory inv
            JOIN items it         ON inv.item_id     = it.id
            JOIN locations l      ON inv.location_id = l.id
            LEFT JOIN units_of_measure u ON it.uom_id = u.id
            LEFT JOIN suppliers s ON it.supplier_id  = s.id
            ORDER BY it.sku, l.code
        """).fetchall()
        conn.close()
        return ok(rows_to_list(rows))

    conn.close()
    return err("Unknown report")

# ── Backup / Restore ──────────────────────────────────────────────────────────

def handle_home():
    conn = get_db()
    # KPI counts
    total_inventory = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory").fetchone()[0]
    inbound_pending = conn.execute("SELECT COUNT(*) FROM inbound WHERE status='pending'").fetchone()[0]
    inbound_inprog  = conn.execute("SELECT COUNT(*) FROM inbound WHERE status='in_progress'").fetchone()[0]
    outbound_pending= conn.execute("SELECT COUNT(*) FROM outbound WHERE status='pending'").fetchone()[0]
    outbound_inprog = conn.execute("SELECT COUNT(*) FROM outbound WHERE status='in_progress'").fetchone()[0]
    low_stock_count = conn.execute("""
        SELECT COUNT(*) FROM inventory inv
        JOIN items it ON inv.item_id=it.id
        WHERE inv.quantity <= it.reorder_point AND inv.quantity > 0
    """).fetchone()[0]
    out_of_stock    = conn.execute("""
        SELECT COUNT(*) FROM inventory inv WHERE inv.quantity <= 0
    """).fetchone()[0]

    # Inventory status — top 8 items with stock info
    inv_status = conn.execute("""
        SELECT it.sku, it.name, it.category, l.code as location_code,
               SUM(inv.quantity) as qty,
               it.reorder_point,
               CASE WHEN SUM(inv.quantity) <= 0 THEN 'OUT_OF_STOCK'
                    WHEN SUM(inv.quantity) <= it.reorder_point THEN 'LOW_STOCK'
                    ELSE 'IN_STOCK' END as stock_status
        FROM inventory inv
        JOIN items it ON inv.item_id=it.id
        JOIN locations l ON inv.location_id=l.id
        GROUP BY it.id ORDER BY qty DESC LIMIT 8
    """).fetchall()

    # Recent inbound orders (last 5)
    recent_inbound = conn.execute("""
        SELECT ib.reference_no, ib.received_date, ib.status,
               s.name as supplier_name, ib.id
        FROM inbound ib
        LEFT JOIN suppliers s ON ib.supplier_id=s.id
        ORDER BY ib.created_at DESC LIMIT 5
    """).fetchall()

    # Recent outbound orders (last 5)
    recent_outbound = conn.execute("""
        SELECT ob.reference_no, ob.dispatch_date, ob.status,
               ob.destination, ob.id
        FROM outbound ob
        ORDER BY ob.created_at DESC LIMIT 5
    """).fetchall()

    # Low stock alerts
    low_stock_items = conn.execute("""
        SELECT it.sku, it.name, SUM(inv.quantity) as qty, it.reorder_point,
               CASE WHEN SUM(inv.quantity) <= 0 THEN 'OUT_OF_STOCK' ELSE 'LOW_STOCK' END as alert_type
        FROM inventory inv
        JOIN items it ON inv.item_id=it.id
        WHERE inv.quantity <= it.reorder_point
        GROUP BY it.id ORDER BY qty ASC LIMIT 5
    """).fetchall()

    # Weekly stock movement — last 7 days inbound qty per day
    stock_movement = conn.execute("""
        SELECT date(ib.received_date) as day,
               COALESCE(SUM(il.qty_received),0) as qty_in,
               0 as qty_out
        FROM inbound ib
        JOIN inbound_lines il ON il.inbound_id=ib.id
        WHERE ib.received_date >= date('now','-6 days')
        GROUP BY day
        UNION ALL
        SELECT date(ob.dispatch_date) as day,
               0 as qty_in,
               COALESCE(SUM(ol.qty_dispatched),0) as qty_out
        FROM outbound ob
        JOIN outbound_lines ol ON ol.outbound_id=ob.id
        WHERE ob.dispatch_date >= date('now','-6 days')
        GROUP BY day
        ORDER BY day ASC
    """).fetchall()

    conn.close()
    return ok({
        "kpi": {
            "total_inventory": int(total_inventory),
            "inbound_pending": inbound_pending,
            "inbound_inprog":  inbound_inprog,
            "outbound_pending":outbound_pending,
            "outbound_inprog": outbound_inprog,
            "low_stock":       low_stock_count,
            "out_of_stock":    out_of_stock,
        },
        "inventory_status": rows_to_list(inv_status),
        "recent_inbound":   rows_to_list(recent_inbound),
        "recent_outbound":  rows_to_list(recent_outbound),
        "low_stock_items":  rows_to_list(low_stock_items),
        "stock_movement":   rows_to_list(stock_movement),
    })

def handle_backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"wms_backup_{ts}.db")
    shutil.copy2(DB_PATH, backup_path)
    return ok({"filename": os.path.basename(backup_path)}, "Backup created")

def handle_list_backups():
    files = []
    if os.path.exists(BACKUP_DIR):
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if f.endswith(".db"):
                path = os.path.join(BACKUP_DIR, f)
                files.append({"filename": f, "size": os.path.getsize(path),
                               "created": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")})
    return ok(files)

def handle_restore(body):
    filename = body.get("filename", "")
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if not os.path.exists(backup_path):
        return err("Backup file not found")
    shutil.copy2(backup_path, DB_PATH)
    return ok(None, "Database restored successfully")

def handle_delete_backup(body):
    filename = body.get("filename", "")
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return ok(None, "Backup deleted")
    return err("File not found")

def handle_download_backup(filename):
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(filename))
    if not os.path.exists(backup_path):
        return None
    with open(backup_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def handle_upload_restore(body):
    data_b64 = body.get("data", "")
    filename = body.get("filename", "restore.db")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"upload_{ts}.db")
    with open(backup_path, "wb") as f:
        f.write(base64.b64decode(data_b64))
    shutil.copy2(backup_path, DB_PATH)
    return ok(None, "Database restored from upload")

# ── HTTP Handler ──────────────────────────────────────────────────────────────

class WMSHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence default logging

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        params = parse_qs(parsed.query)

        # Serve static files
        if not parts or parts[0] == "":
            self._serve_file("index.html", "text/html")
            return
        if parts[0] == "index.html":
            self._serve_file("index.html", "text/html")
            return

        if parts[0] != "api":
            self.send_response(404)
            self.end_headers()
            return

        # API routes
        if len(parts) == 2 and parts[1] in TABLES:
            self.send_json(handle_list(parts[1], params))
        elif len(parts) == 3 and parts[1] in TABLES:
            self.send_json(handle_get(parts[1], int(parts[2])))
        elif parts[1] == "inbound" and len(parts) == 2:
            self.send_json(handle_inbound_list(params))
        elif parts[1] == "inbound" and len(parts) == 3:
            self.send_json(handle_inbound_get(int(parts[2])))
        elif parts[1] == "outbound" and len(parts) == 2:
            self.send_json(handle_outbound_list(params))
        elif parts[1] == "outbound" and len(parts) == 3:
            self.send_json(handle_outbound_get(int(parts[2])))
        elif parts[1] == "reports" and len(parts) == 3:
            self.send_json(handle_reports(parts[2]))
        elif parts[1] == "home" and len(parts) == 2:
            self.send_json(handle_home())
        elif parts[1] == "backups":
            self.send_json(handle_list_backups())
        elif parts[1] == "backup" and len(parts) == 3 and parts[2] == "download":
            filename = params.get("filename", [""])[0]
            data = handle_download_backup(filename)
            if data:
                self.send_json(ok({"data": data, "filename": filename}))
            else:
                self.send_json(err("Not found"))
        else:
            self.send_json(err("Not found"), 404)

    def _serve_file(self, filename, content_type):
        try:
            with open(filename, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parts = [p for p in self.path.strip("/").split("/") if p]
        body = self.read_body()

        if parts[0] == "api":
            if parts[1] == "login":
                self.send_json(handle_login(body))
            elif parts[1] in TABLES:
                self.send_json(handle_create(parts[1], body))
            elif parts[1] == "inbound":
                self.send_json(handle_inbound_create(body))
            elif parts[1] == "outbound":
                self.send_json(handle_outbound_create(body))
            elif parts[1] == "backup":
                self.send_json(handle_backup())
            elif parts[1] == "restore" and len(parts) == 2:
                self.send_json(handle_restore(body))
            elif parts[1] == "restore" and len(parts) == 3 and parts[2] == "upload":
                self.send_json(handle_upload_restore(body))
            elif parts[1] == "backup" and len(parts) == 3 and parts[2] == "delete":
                self.send_json(handle_delete_backup(body))
            else:
                self.send_json(err("Not found"), 404)

    def do_PUT(self):
        parts = [p for p in self.path.strip("/").split("/") if p]
        body = self.read_body()
        if parts[0] == "api":
            if parts[1] in TABLES and len(parts) == 3:
                self.send_json(handle_update(parts[1], int(parts[2]), body))
            elif parts[1] == "inbound" and len(parts) == 3:
                self.send_json(handle_inbound_update(int(parts[2]), body))
            elif parts[1] == "outbound" and len(parts) == 3:
                self.send_json(handle_outbound_update(int(parts[2]), body))
            else:
                self.send_json(err("Not found"), 404)

    def do_DELETE(self):
        parts = [p for p in self.path.strip("/").split("/") if p]
        if parts[0] == "api" and parts[1] in TABLES and len(parts) == 3:
            self.send_json(handle_delete(parts[1], int(parts[2])))
        else:
            self.send_json(err("Not found"), 404)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), WMSHandler)
    print(f"WMS Server running on http://localhost:{port}")
    print("Default login: admin / admin123")
    server.serve_forever()
