from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class BudgetItem(BaseModel):
    description: str
    amount: float = 0.0
    allocation_code: str = ""
    discount_code: str = ""


class BudgetCreate(BaseModel):
    name: str
    status: str = "draft"
    items: list[BudgetItem] = []
    budget_memo: str = ""
    fiscal_code: str = ""
    attachments: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class BudgetPatch(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    budget_memo: Optional[str] = None
    collaborators: Optional[list[str]] = None
    visibility: Optional[str] = None


class Budget(BaseModel):
    id: str
    owner_id: str
    name: str
    status: str
    items: list[BudgetItem]
    budget_memo: str
    fiscal_code: str
    attachments: dict[str, str]
    collaborators: list[str]
    visibility: str
