from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    vendor_code: str = ""
    discount_code: str = ""


class QuoteCreate(BaseModel):
    client_name: str = ""
    status: str = "draft"
    line_items: list[LineItem] = []
    internal_notes: str = ""
    terms: str = ""
    attachments: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class QuotePatch(BaseModel):
    client_name: Optional[str] = None
    status: Optional[str] = None
    terms: Optional[str] = None


class Quote(BaseModel):
    id: str
    owner_id: str
    client_name: str
    status: str
    line_items: list[LineItem]
    internal_notes: str
    terms: str
    attachments: dict[str, str]
    collaborators: list[str]
    visibility: str
