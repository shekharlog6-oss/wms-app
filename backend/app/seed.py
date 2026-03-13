from sqlmodel import Session, select
from .db import engine
from .models import User, Order, Location

def seed() -> None:
    with Session(engine) as s:
        # Users
        if not s.exec(select(User).where(User.username == "admin")).first():
            s.add(User(username="admin", display_name="Administrator", role="admin"))
        if not s.exec(select(User).where(User.username == "operator")).first():
            s.add(User(username="operator", display_name="Operator", role="operator"))

        # Locations
        if not s.exec(select(Location)).first():
            s.add(Location(code="A1", capacity=1000))
            s.add(Location(code="B1", capacity=500))

        # Orders
        if not s.exec(select(Order)).first():
            s.add(Order(order_no="ORD-1001", status="PENDING", tonnage=12.5))
            s.add(Order(order_no="ORD-1002", status="PENDING", tonnage=5.0))

        s.commit()