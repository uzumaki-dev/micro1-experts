from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class LineItem(BaseModel):
    description: str = ""
    amount: float = 0.0
    cost_code: str = ""
    discount_code: str = ""


class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    merchant: str = "Unknown"
    status: str = "draft"
    line_items: list[LineItem] = []
    private_notes: str = ""
    policy_code: str = ""
    receipts: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ExpenseCreate(BaseModel):
    merchant: str = "Unknown"
    status: str = "draft"
    line_items: list[LineItem] = []
    private_notes: str = ""
    policy_code: str = ""
    receipts: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ExpensePatch(BaseModel):
    merchant: Optional[str] = None
    status: Optional[str] = None
    private_notes: Optional[str] = None
    policy_code: Optional[str] = None
