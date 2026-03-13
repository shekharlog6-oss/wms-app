"""
Seed Script - Insert sample data into warehouse.db
Run: python seed.py
"""
import sqlite3
from datetime import datetime

DB_PATH = r"C:\work\warehouse-prototype\backend\warehouse.db"
now = datetime.now().isoformat()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ─── Units of Measure ────────────────────────────────────────────────────────
print("Seeding Units of Measure...")
uoms = [
    ("PCS",  "Pieces",      "Individual countable units",         "Count"),
    ("BOX",  "Box",         "Boxed quantity",                     "Count"),
    ("CTN",  "Carton",      "Carton / case pack",                 "Count"),
    ("PAL",  "Pallet",      "Full pallet load",                   "Count"),
    ("ROLL", "Roll",        "Roll of material",                   "Count"),
    ("KG",   "Kilograms",   "Weight in kilograms",                "Weight"),
    ("G",    "Grams",       "Weight in grams",                    "Weight"),
    ("TON",  "Metric Ton",  "1000 kilograms",                     "Weight"),
    ("LTR",  "Litres",      "Volume in litres",                   "Volume"),
    ("ML",   "Millilitres", "Volume in millilitres",              "Volume"),
    ("MTR",  "Metres",      "Length in metres",                   "Length"),
    ("CM",   "Centimetres", "Length in centimetres",              "Length"),
    ("SQM",  "Sq. Metres",  "Area in square metres",              "Area"),
    ("SET",  "Set",         "A grouped set of items",             "Count"),
    ("PR",   "Pair",        "A pair of items",                    "Count"),
]
for u in uoms:
    cur.execute("""
        INSERT OR IGNORE INTO unit_of_measure (code, name, description, uom_type, is_active, created_at, updated_at)
        VALUES (?,?,?,?,1,?,?)
    """, (*u, now, now))

# ─── Suppliers ───────────────────────────────────────────────────────────────
print("Seeding Suppliers...")
suppliers = [
    ("SUP-001", "Alpha Industrial Supplies",  "Rajesh Kumar",    "rajesh@alphaindustrial.com",  "+91-98765-43210", "12 Industrial Estate, Phase 2", "Hyderabad",  "India",   "Net 30", 7),
    ("SUP-002", "BetaTech Components Ltd",    "Priya Sharma",    "priya@betatech.com",          "+91-94567-12345", "45 Tech Park, Hitec City",      "Hyderabad",  "India",   "Net 45", 14),
    ("SUP-003", "Global Packaging Co.",       "Suresh Reddy",    "suresh@globalpack.com",       "+91-99887-65432", "78 Logistics Hub, Patancheru",  "Hyderabad",  "India",   "Net 15", 5),
    ("SUP-004", "SafeGuard Equipment Pvt",    "Anita Mehta",     "anita@safeguard.com",         "+91-88776-55443", "22 Safety Plaza, Secunderabad", "Secunderabad","India",  "Net 30", 10),
    ("SUP-005", "PowerCell Batteries",        "Vikram Singh",    "vikram@powercell.com",        "+91-77665-44332", "5 Energy Park, Uppal",          "Hyderabad",  "India",   "Net 60", 21),
    ("SUP-006", "WrapPro Solutions",          "Deepa Nair",      "deepa@wrappro.com",           "+91-66554-33221", "9 Packaging Zone, Balanagar",   "Hyderabad",  "India",   "Net 15", 3),
    ("SUP-007", "FastTrack Logistics",        "Mohammed Ali",    "mali@fasttrack.com",          "+91-55443-22110", "33 Freight Nagar, Shamshabad",  "Hyderabad",  "India",   "Net 30", 2),
]
for s in suppliers:
    cur.execute("""
        INSERT OR IGNORE INTO supplier
            (code, name, contact_person, email, phone, address, city, country,
             payment_terms, lead_time_days, is_active, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?)
    """, (*s, now, now))

# ─── Warehouse Locations ─────────────────────────────────────────────────────
print("Seeding Warehouse Locations...")
locations = [
    ("RCV-01",  "Receiving Bay 1",       "Receiving", "RCV", None,  None,  "Receiving",   500.0),
    ("RCV-02",  "Receiving Bay 2",       "Receiving", "RCV", None,  None,  "Receiving",   500.0),
    ("STG-01",  "Staging Area 1",        "Staging",   "STG", None,  None,  "Staging",     300.0),
    ("STG-02",  "Staging Area 2",        "Staging",   "STG", None,  None,  "Staging",     300.0),
    ("A-01-R1", "Zone A Aisle 01 Rack 1","A",         "01",  "R1",  None,  "Storage",     200.0),
    ("A-01-R2", "Zone A Aisle 01 Rack 2","A",         "01",  "R2",  None,  "Storage",     200.0),
    ("A-02-R1", "Zone A Aisle 02 Rack 1","A",         "02",  "R1",  None,  "Storage",     200.0),
    ("A-02-R2", "Zone A Aisle 02 Rack 2","A",         "02",  "R2",  None,  "Storage",     200.0),
    ("B-01-R1", "Zone B Aisle 01 Rack 1","B",         "01",  "R1",  None,  "Storage",     250.0),
    ("B-01-R2", "Zone B Aisle 01 Rack 2","B",         "01",  "R2",  None,  "Storage",     250.0),
    ("B-02-R1", "Zone B Aisle 02 Rack 1","B",         "02",  "R1",  None,  "Storage",     250.0),
    ("B-02-R2", "Zone B Aisle 02 Rack 2","B",         "02",  "R2",  None,  "Storage",     250.0),
    ("C-01-R1", "Zone C Aisle 01 Rack 1","C",         "01",  "R1",  None,  "Storage",     300.0),
    ("C-01-R2", "Zone C Aisle 01 Rack 2","C",         "01",  "R2",  None,  "Storage",     300.0),
    ("QRN-01",  "Quarantine Zone 1",     "Quarantine","QRN", None,  None,  "Quarantine",  100.0),
    ("RET-01",  "Returns Bay",           "Returns",   "RET", None,  None,  "Returns",     150.0),
    ("DSP-01",  "Dispatch Bay 1",        "Dispatch",  "DSP", None,  None,  "Dispatch",    400.0),
    ("DSP-02",  "Dispatch Bay 2",        "Dispatch",  "DSP", None,  None,  "Dispatch",    400.0),
]
for l in locations:
    cur.execute("""
        INSERT OR IGNORE INTO warehouse_location
            (code, name, zone, aisle, rack, bin, loc_type, capacity, is_active, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,1,?,?)
    """, (*l, now, now))

# ─── Items ───────────────────────────────────────────────────────────────────
print("Seeding Items...")
items = [
    # Safety Equipment
    ("SKU-1001","8901001000001","Industrial Gloves (L)","Heavy-duty cut-resistant gloves, size Large","Safety Equipment","Hand Protection","SafeGuard","PCS",0.3,30,15,5,4.50,9.99,20,200,50,100,120,0,"A","01","R1"),
    ("SKU-1002","8901001000002","Industrial Gloves (M)","Heavy-duty cut-resistant gloves, size Medium","Safety Equipment","Hand Protection","SafeGuard","PCS",0.3,30,15,5,4.50,9.99,20,200,50,100,95,0,"A","01","R1"),
    ("SKU-1003","8901001000003","Safety Helmet White","Hard hat, Class E, ANSI certified","Safety Equipment","Head Protection","SafeGuard","PCS",0.45,32,22,20,8.00,18.50,15,150,30,60,48,0,"A","01","R2"),
    ("SKU-1004","8901001000004","Safety Helmet Yellow","Hard hat, Class E, ANSI certified","Safety Equipment","Head Protection","SafeGuard","PCS",0.45,32,22,20,8.00,18.50,15,150,30,60,35,0,"A","01","R2"),
    ("SKU-1005","8901001000005","Safety Boots Size 42","Steel toe cap safety boots","Safety Equipment","Foot Protection","SafeGuard","PCS",1.2,32,16,14,22.00,48.00,10,100,20,40,28,0,"A","02","R1"),
    ("SKU-1006","8901001000006","Hi-Vis Vest Orange","High visibility reflective vest, one size","Safety Equipment","Body Protection","SafeGuard","PCS",0.2,70,60,1,3.50,7.99,25,300,50,100,142,0,"A","02","R1"),
    # Packaging
    ("SKU-2001","8901002000001","Pallet Wrap 500m","Stretch film pallet wrap, 500m roll, 23 micron","Packaging","Wrapping","WrapPro","ROLL",2.5,50,50,20,12.00,22.00,10,100,20,50,65,0,"B","01","R1"),
    ("SKU-2002","8901002000002","Pallet Wrap 300m","Stretch film pallet wrap, 300m roll, 20 micron","Packaging","Wrapping","WrapPro","ROLL",1.8,50,50,15,8.50,16.00,10,100,20,50,40,0,"B","01","R1"),
    ("SKU-2003","8901002000003","Bubble Wrap Roll 50m","Air bubble protective wrap, 50m x 1.2m","Packaging","Protective","WrapPro","ROLL",1.2,120,100,10,15.00,28.00,5,50,15,30,22,0,"B","01","R2"),
    ("SKU-2004","8901002000004","Cardboard Box Small","Single wall corrugated box 30x20x20cm","Packaging","Boxes","Global Packaging Co.","PCS",0.35,30,20,20,0.80,1.99,50,1000,100,200,350,0,"B","02","R1"),
    ("SKU-2005","8901002000005","Cardboard Box Medium","Single wall corrugated box 50x40x40cm","Packaging","Boxes","Global Packaging Co.","PCS",0.55,50,40,40,1.20,2.99,50,1000,100,200,280,0,"B","02","R1"),
    ("SKU-2006","8901002000006","Cardboard Box Large","Double wall corrugated box 80x60x60cm","Packaging","Boxes","Global Packaging Co.","PCS",0.90,80,60,60,2.50,5.49,30,500,60,120,175,0,"B","02","R2"),
    ("SKU-2007","8901002000007","Packing Tape 50m","Brown self-adhesive packing tape 48mm x 50m","Packaging","Tape","Global Packaging Co.","ROLL",0.15,15,5,5,0.60,1.49,50,500,100,200,320,0,"B","02","R2"),
    # Equipment & Tools
    ("SKU-3001","8901003000001","Forklift Battery 48V","48V 600Ah lead-acid traction battery","Equipment","Batteries","PowerCell","PCS",85.0,80,40,60,850.00,1200.00,1,10,2,4,6,0,"C","01","R1"),
    ("SKU-3002","8901003000002","Pallet Jack 2500kg","Manual hydraulic pallet jack, 2500kg capacity","Equipment","Handling","Alpha Industrial","PCS",68.0,160,55,120,180.00,320.00,1,5,2,3,4,0,"C","01","R2"),
    ("SKU-3003","8901003000003","Hand Truck 300kg","Heavy duty aluminium sack truck 300kg","Equipment","Handling","Alpha Industrial","PCS",8.5,130,50,15,45.00,89.00,2,20,5,8,11,0,"C","01","R2"),
    ("SKU-3004","8901003000004","Barcode Scanner Handheld","Wireless 2D barcode scanner, USB receiver","Equipment","IT Hardware","BetaTech","PCS",0.3,18,8,5,55.00,110.00,2,20,5,8,7,0,"C","01","R2"),
    # Cleaning & Maintenance
    ("SKU-4001","8901004000001","Floor Cleaner 5L","Industrial strength floor cleaner concentrate","Cleaning","Chemicals","Alpha Industrial","LTR",5.2,20,15,25,6.50,13.99,10,100,20,40,55,0,"A","02","R2"),
    ("SKU-4002","8901004000002","Mop & Bucket Set","Heavy duty mop with wringer bucket 25L","Cleaning","Equipment","Alpha Industrial","SET",2.8,40,35,90,12.00,24.99,5,50,10,20,18,0,"A","02","R2"),
    ("SKU-4003","8901004000003","Dust Masks N95 Box/20","N95 disposable respirator masks, box of 20","Safety Equipment","Respiratory","SafeGuard","BOX",0.25,20,15,8,9.00,19.99,20,200,40,80,0,0,"A","01","R1"),
]

for item in items:
    (sku,barcode,name,desc,cat,subcat,brand,uom,wkg,lcm,wcm,hcm,cost,price,minst,maxst,reord,reordqty,curstock,resstock,zone,aisle,rack) = item
    # find location_id
    cur.execute("SELECT id FROM warehouse_location WHERE zone=? AND aisle=? AND rack=?", (zone, aisle, rack))
    row = cur.fetchone()
    loc_id = row[0] if row else None
    # find supplier_id by brand match
    cur.execute("SELECT id FROM supplier WHERE name LIKE ?", (f"%{brand}%",))
    row = cur.fetchone()
    sup_id = row[0] if row else None

    cur.execute("""
        INSERT OR IGNORE INTO item (
            sku, barcode, name, description, category, sub_category, brand,
            unit_of_measure, weight_kg, length_cm, width_cm, height_cm,
            unit_cost, selling_price, min_stock_level, max_stock_level,
            reorder_level, reorder_qty, current_stock, reserved_stock,
            location_id, supplier_id, is_active, is_serialized, is_perishable,
            created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,0,0,?,?)
    """, (sku,barcode,name,desc,cat,subcat,brand,uom,wkg,lcm,wcm,hcm,
          cost,price,minst,maxst,reord,reordqty,curstock,resstock,
          loc_id,sup_id,now,now))

conn.commit()

# ─── Summary ─────────────────────────────────────────────────────────────────
print("\n── Seed Summary ──────────────────────────")
for tbl in ["unit_of_measure","supplier","warehouse_location","item"]:
    cur.execute(f"SELECT COUNT(*) FROM {tbl}")
    print(f"  {tbl:<25} {cur.fetchone()[0]} rows")
print("──────────────────────────────────────────")
print("Seed complete! Refresh your browser.")
conn.close()
