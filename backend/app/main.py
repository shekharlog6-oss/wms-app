from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from .db import create_db_and_tables, get_session
from .models import User, Order, Pallet, Location, AuditLog
from .seed import seed
from .auth import create_token, require_role, current_user

app = FastAPI(title="Warehouse Prototype API")

# Allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    create_db_and_tables()
    seed()

@app.get("/")
def root():
    return {"ok": True, "service": "warehouse-prototype"}

# ---- Auth (DEV) ----
@app.post("/auth/login")
def login(payload: dict, session: Session = Depends(get_session)):
    username = payload.get("username")
    if not username:
        raise HTTPException(400, "username required")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(401, "unknown user")

    token = create_token(user_id=user.id, username=user.username, role=user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@app.get("/user/me")
def me(user=Depends(current_user)):
    return user

# ---- Dashboard ----
@app.get("/dashboard/summary")
def summary(session: Session = Depends(get_session)):
    orders = session.exec(select(Order)).all()
    pallets = session.exec(select(Pallet)).all()
    locations = session.exec(select(Location)).all()
    return {
        "orders": len(orders),
        "pallets": len(pallets),
        "tonnage": float(sum(o.tonnage for o in orders)),
        "locations": len(locations),
    }

# ---- Orders ----
@app.get("/orders")
def list_orders(status: str | None = None, session: Session = Depends(get_session)):
    q = select(Order)
    if status:
        q = q.where(Order.status == status)
    return session.exec(q).all()

@app.get("/orders/{order_id}")
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order

# ---- Receive workflow ----
@app.post("/workflows/receive")
def receive(payload: dict, user=Depends(require_role("operator")), session: Session = Depends(get_session)):
    order_id = payload.get("order_id")
    if not order_id:
        raise HTTPException(400, "order_id required")

    order = session.get(Order, int(order_id))
    if not order:
        raise HTTPException(404, "Order not found")

    # Prototype: create ONE pallet per receive call
    barcode = f"{order.order_no}-P{order.id}"
    pallet = Pallet(barcode=barcode, order_id=order.id, status="RECEIVED")
    session.add(pallet)
    session.commit()
    session.refresh(pallet)

    log = AuditLog(
        user_id=user["id"],
        action="receive",
        object_type="pallet",
        object_id=pallet.id,
        details=f"Received pallet {pallet.barcode} for order {order.order_no}",
    )
    session.add(log)
    session.commit()

    return {"pallets": [pallet]}

@app.post("/pallets/{pallet_id}/mark-qc")
def mark_qc(pallet_id: int, flag: bool = True, user=Depends(require_role("operator")), session: Session = Depends(get_session)):
    pallet = session.get(Pallet, pallet_id)
    if not pallet:
        raise HTTPException(404, "Pallet not found")
    pallet.qc_flag = flag
    session.add(pallet)

    log = AuditLog(
        user_id=user["id"],
        action="mark-qc",
        object_type="pallet",
        object_id=pallet.id,
        details=f"QC flag set to {flag}",
    )
    session.add(log)

    session.commit()
    session.refresh(pallet)
    return {"pallet": pallet}

# ---- Admin ----
@app.get("/admin/audit-logs")
def audit_logs(limit: int = 100, user=Depends(require_role("admin")), session: Session = Depends(get_session)):
    logs = session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)).all()
    return logs