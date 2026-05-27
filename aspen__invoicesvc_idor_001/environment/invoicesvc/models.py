from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class LineItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float = 0.0
    cost_code: str = ""
    discount_code: str = ""


class InvoiceCreate(BaseModel):
    client_name: str
    status: str = "draft"
    line_items: list[LineItem] = []
    internal_notes: str = ""
    attachments: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class InvoicePatch(BaseModel):
    client_name: Optional[str] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None
    collaborators: Optional[list[str]] = None
    visibility: Optional[str] = None


class Invoice(BaseModel):
    id: str
    owner_id: str
    client_name: str
    status: str
    line_items: list[LineItem]
    internal_notes: str
    attachments: dict[str, str]
    collaborators: list[str]
    visibility: str
