from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class LineItem(BaseModel):
    name: str
    qty: int
    unit_price: float


class Order(BaseModel):
    id: str
    owner_id: str
    status: str
    items: List[LineItem]
    shipping_address: str
    notes: str
    discount_pct: float
    payment_status: str


class OrderCreate(BaseModel):
    items: List[LineItem]
    shipping_address: str
    notes: str = ""
    # Privileged fields — should be ignored for non-admin at creation time.
    # BUG: server accepts these from any caller without a role check.
    status: str = "pending"
    discount_pct: float = 0.0
    payment_status: str = "unpaid"


class OrderPatch(BaseModel):
    # User-settable fields
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    # Privileged fields — should only be accepted from admin.
    # BUG: no role check; any authenticated caller can set these via PATCH.
    status: Optional[str] = None
    discount_pct: Optional[float] = None
    payment_status: Optional[str] = None
