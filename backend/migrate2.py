"""
Migration 2 - Add users, inbound, outbound tables to existing warehouse.db
Run: python migrate2.py
All existing data is preserved.
"""
import sqlite3, hashlib
from datetime import datetime

DB_PATH = r"C:\work\warehouse-prototype\backend\warehouse.db"
now = datetime.now().isoformat()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Running Migration 2...")

# ── wms_user (new table, separate from legacy 'user') ──────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS wms_user (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      VARCHAR NOT NULL UNIQUE,
        password_hash VARCHAR NOT NULL,
        display_name  VARCHAR NOT NULL,
        email         VARCHAR,
        phone         VARCHAR,
        role          VARCHAR NOT NULL DEFAULT 'Operator',
        is_active     BOOLEAN NOT NULL DEFAULT 1,
        last_login    DATETIME,
        created_at    DATETIME NOT NULL,
        updated_at    DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_wms_user_username ON wms_user(username)")

# ── inbound_order ───────────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS inbound_order (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number       VARCHAR NOT NULL UNIQUE,
        supplier_id     INTEGER REFERENCES supplier(id),
        status          VARCHAR NOT NULL DEFAULT 'Pending',
        expected_date   DATE,
        received_date   DATE,
        total_qty       INTEGER DEFAULT 0,
        received_qty    INTEGER DEFAULT 0,
        notes           VARCHAR,
        created_by      INTEGER REFERENCES wms_user(id),
        created_at      DATETIME NOT NULL,
        updated_at      DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_inbound_po     ON inbound_order(po_number)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_inbound_status ON inbound_order(status)")

# ── inbound_order_line ──────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS inbound_order_line (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        inbound_order_id INTEGER NOT NULL REFERENCES inbound_order(id),
        item_id          INTEGER NOT NULL REFERENCES item(id),
        expected_qty     INTEGER NOT NULL DEFAULT 0,
        received_qty     INTEGER NOT NULL DEFAULT 0,
        unit_cost        REAL,
        location_id      INTEGER REFERENCES warehouse_location(id),
        status           VARCHAR NOT NULL DEFAULT 'Pending',
        notes            VARCHAR,
        created_at       DATETIME NOT NULL,
        updated_at       DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_inbound_line_order ON inbound_order_line(inbound_order_id)")

# ── outbound_order ──────────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS outbound_order (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        so_number       VARCHAR NOT NULL UNIQUE,
        customer_name   VARCHAR,
        customer_ref    VARCHAR,
        status          VARCHAR NOT NULL DEFAULT 'Pending',
        priority        VARCHAR NOT NULL DEFAULT 'Normal',
        required_date   DATE,
        dispatched_date DATE,
        total_qty       INTEGER DEFAULT 0,
        picked_qty      INTEGER DEFAULT 0,
        dispatch_address VARCHAR,
        notes           VARCHAR,
        created_by      INTEGER REFERENCES wms_user(id),
        created_at      DATETIME NOT NULL,
        updated_at      DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_outbound_so     ON outbound_order(so_number)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_outbound_status ON outbound_order(status)")

# ── outbound_order_line ─────────────────────────────────────────────────────
cur.execute("""
    CREATE TABLE IF NOT EXISTS outbound_order_line (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        outbound_order_id INTEGER NOT NULL REFERENCES outbound_order(id),
        item_id           INTEGER NOT NULL REFERENCES item(id),
        requested_qty     INTEGER NOT NULL DEFAULT 0,
        picked_qty        INTEGER NOT NULL DEFAULT 0,
        location_id       INTEGER REFERENCES warehouse_location(id),
        status            VARCHAR NOT NULL DEFAULT 'Pending',
        notes             VARCHAR,
        created_at        DATETIME NOT NULL,
        updated_at        DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_outbound_line_order ON outbound_order_line(outbound_order_id)")

conn.commit()

# ── Seed default admin user ─────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM wms_user")
if cur.fetchone()[0] == 0:
    print("Creating default users...")
    default_users = [
        ("admin",    "admin123",    "Administrator",   "admin@warehouse.com",    "+91-98000-00001", "Admin"),
        ("manager",  "manager123",  "Warehouse Manager","manager@warehouse.com", "+91-98000-00002", "Manager"),
        ("operator", "operator123", "Floor Operator",  "operator@warehouse.com", "+91-98000-00003", "Operator"),
        ("viewer",   "viewer123",   "Report Viewer",   "viewer@warehouse.com",   "+91-98000-00004", "Viewer"),
    ]
    for u in default_users:
        cur.execute("""
            INSERT OR IGNORE INTO wms_user
                (username, password_hash, display_name, email, phone, role, is_active, created_at, updated_at)
            VALUES (?,?,?,?,?,?,1,?,?)
        """, (u[0], hash_password(u[1]), u[2], u[3], u[4], u[5], now, now))
    conn.commit()

# ─── Summary ────────────────────────────────────────────────────────────────
print("\n── Migration 2 Summary ───────────────────")
all_tables = ["wms_user","inbound_order","inbound_order_line","outbound_order","outbound_order_line"]
for t in all_tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t:<30} {cur.fetchone()[0]} rows")

print("\n── All Tables in DB ──────────────────────")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for r in cur.fetchall():
    try:
        cur2 = conn.cursor()
        cur2.execute(f'SELECT COUNT(*) FROM "{r[0]}"')
        cnt = cur2.fetchone()[0]
    except: cnt = '?'
    print(f"  {r[0]:<30} {cnt} rows")

print("\n── Default Login Credentials ─────────────")
print("  Username : admin     | Password : admin123")
print("  Username : manager   | Password : manager123")
print("  Username : operator  | Password : operator123")
print("  Username : viewer    | Password : viewer123")
print("──────────────────────────────────────────")
print("Migration 2 complete!")
conn.close()
