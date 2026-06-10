import copy
from typing import Optional

_loans: dict[str, dict] = {}


def reset() -> None:
    _loans.clear()


def get_loan(loan_id: str) -> Optional[dict]:
    loan = _loans.get(loan_id)
    return copy.deepcopy(loan) if loan is not None else None


def save_loan(loan: dict) -> None:
    _loans[loan["id"]] = copy.deepcopy(loan)


def all_loans() -> list[dict]:
    return [copy.deepcopy(v) for v in _loans.values()]
