from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    display_name: Optional[str] = None
    role: str  # "admin" or "operator"
    theme_pref: str = "light"
    language_pref: str = "en"

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_no: str
    status: str = "PENDING"
    tonnage: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Pallet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    barcode: str
    order_id: int = Field(foreign_key="order.id")
    location: Optional[str] = None
    qc_flag: bool = False
    status: str = "CREATED"

class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str
    capacity: float = 0.0

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    action: str
    object_type: str
    object_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)