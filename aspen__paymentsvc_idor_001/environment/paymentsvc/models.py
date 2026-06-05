from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class LineItem(BaseModel):
    description: str = ""
    amount: float = 0.0
    fee_code: str = ""
    category_code: str = ""


class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    merchant: str = "Unknown"
    status: str = "pending"
    line_items: list[LineItem] = []
    private_notes: str = ""
    reference_code: str = ""
    documents: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class PaymentCreate(BaseModel):
    merchant: str = "Unknown"
    status: str = "pending"
    line_items: list[LineItem] = []
    private_notes: str = ""
    reference_code: str = ""
    documents: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class PaymentPatch(BaseModel):
    merchant: Optional[str] = None
    status: Optional[str] = None
    private_notes: Optional[str] = None
    reference_code: Optional[str] = None
