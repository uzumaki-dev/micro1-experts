from __future__ import annotations
import uuid
from typing import Dict, List, Optional

from ordersvc.models import LineItem, Order

_db: Dict[str, dict] = {}


def create(
    owner_id: str,
    status: str,
    items: List[LineItem],
    shipping_address: str,
    notes: str,
    discount_pct: float,
    payment_status: str,
) -> Order:
    oid = str(uuid.uuid4())
    record = {
        "id": oid,
        "owner_id": owner_id,
        "status": status,
        "items": [i.model_dump() for i in items],
        "shipping_address": shipping_address,
        "notes": notes,
        "discount_pct": discount_pct,
        "payment_status": payment_status,
    }
    _db[oid] = record
    return Order(**record)


def get(order_id: str) -> Optional[Order]:
    rec = _db.get(order_id)
    return Order(**rec) if rec else None


def list_all() -> List[Order]:
    return [Order(**r) for r in _db.values()]


def update(order_id: str, **kwargs) -> Optional[Order]:
    rec = _db.get(order_id)
    if rec is None:
        return None
    for k, v in kwargs.items():
        if v is not None:
            rec[k] = v
    return Order(**rec)
