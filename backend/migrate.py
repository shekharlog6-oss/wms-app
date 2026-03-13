"""
Migration Script - Add new tables to existing warehouse.db
Run: python migrate.py
"""
import sqlite3

DB_PATH = r"C:\work\warehouse-prototype\backend\warehouse.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Unit of Measure
cur.execute("""
    CREATE TABLE IF NOT EXISTS unit_of_measure (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        VARCHAR NOT NULL UNIQUE,
        name        VARCHAR NOT NULL,
        description VARCHAR,
        uom_type    VARCHAR NOT NULL DEFAULT 'Count',
        is_active   BOOLEAN NOT NULL DEFAULT 1,
        created_at  DATETIME NOT NULL,
        updated_at  DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_uom_code   ON unit_of_measure(code)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_uom_active ON unit_of_measure(is_active)")

# Supplier
cur.execute("""
    CREATE TABLE IF NOT EXISTS supplier (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        code             VARCHAR NOT NULL UNIQUE,
        name             VARCHAR NOT NULL,
        contact_person   VARCHAR,
        email            VARCHAR,
        phone            VARCHAR,
        address          VARCHAR,
        city             VARCHAR,
        country          VARCHAR,
        payment_terms    VARCHAR,
        lead_time_days   INTEGER DEFAULT 0,
        is_active        BOOLEAN NOT NULL DEFAULT 1,
        notes            VARCHAR,
        created_at       DATETIME NOT NULL,
        updated_at       DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_supplier_code   ON supplier(code)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_supplier_active ON supplier(is_active)")

# Warehouse Location
cur.execute("""
    CREATE TABLE IF NOT EXISTS warehouse_location (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        VARCHAR NOT NULL UNIQUE,
        name        VARCHAR NOT NULL,
        zone        VARCHAR,
        aisle       VARCHAR,
        rack        VARCHAR,
        bin         VARCHAR,
        loc_type    VARCHAR NOT NULL DEFAULT 'Storage',
        capacity    FLOAT,
        is_active   BOOLEAN NOT NULL DEFAULT 1,
        notes       VARCHAR,
        created_at  DATETIME NOT NULL,
        updated_at  DATETIME NOT NULL
    )
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_wloc_code   ON warehouse_location(code)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_wloc_zone   ON warehouse_location(zone)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_wloc_active ON warehouse_location(is_active)")

conn.commit()

# Verify
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cur.fetchall()])
cur.execute("SELECT COUNT(*) FROM item")
print("Items preserved:", cur.fetchone()[0])
print("Migration complete!")

conn.close()
