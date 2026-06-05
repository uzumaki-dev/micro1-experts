from __future__ import annotations
import uuid
from budgetsvc.models import Budget, BudgetItem

_budgets: dict[str, Budget] = {}


def reset() -> None:
    _budgets.clear()


def create(
    owner_id: str,
    name: str,
    status: str = "draft",
    items: list[BudgetItem] | None = None,
    budget_memo: str = "",
    fiscal_code: str = "",
    attachments: dict[str, str] | None = None,
    collaborators: list[str] | None = None,
    visibility: str = "private",
) -> Budget:
    b = Budget(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        name=name,
        status=status,
        items=items or [],
        budget_memo=budget_memo,
        fiscal_code=fiscal_code,
        attachments=attachments or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _budgets[b.id] = b
    return b


def get(budget_id: str) -> Budget | None:
    return _budgets.get(budget_id)


def list_all() -> list[Budget]:
    return list(_budgets.values())


def update(budget_id: str, **kwargs) -> Budget | None:
    b = _budgets.get(budget_id)
    if b is None:
        return None
    updated = b.model_copy(update={k: v for k, v in kwargs.items()})
    _budgets[budget_id] = updated
    return updated
