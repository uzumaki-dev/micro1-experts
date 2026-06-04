from __future__ import annotations
from expensesvc.models import Expense

_store: dict[str, Expense] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    merchant: str = "Unknown",
    status: str = "draft",
    line_items: list | None = None,
    private_notes: str = "",
    policy_code: str = "",
    receipts: dict | None = None,
    collaborators: list | None = None,
    visibility: str = "private",
) -> Expense:
    exp = Expense(
        owner_id=owner_id,
        merchant=merchant,
        status=status,
        line_items=line_items or [],
        private_notes=private_notes,
        policy_code=policy_code,
        receipts=receipts or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _store[exp.id] = exp
    return exp


def get(expense_id: str) -> Expense | None:
    return _store.get(expense_id)


def list_all() -> list[Expense]:
    return list(_store.values())


def update(expense_id: str, **kwargs) -> Expense | None:
    exp = _store.get(expense_id)
    if exp is None:
        return None
    data = exp.model_dump()
    data.update(kwargs)
    updated = Expense(**data)
    _store[expense_id] = updated
    return updated
