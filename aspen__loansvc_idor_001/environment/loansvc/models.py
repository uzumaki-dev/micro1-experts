from typing import Optional
from pydantic import BaseModel


class FeeItem(BaseModel):
    description: str
    amount: float
    fee_code: str


class LoanCreate(BaseModel):
    applicant_name: str
    underwriter_notes: str = ""
    fees: list[FeeItem] = []
    documents: dict[str, str] = {}
    private_rate: float = 0.0
    co_applicants: list[str] = []
    visibility: str = "private"


class LoanPatch(BaseModel):
    applicant_name: Optional[str] = None
    underwriter_notes: Optional[str] = None
    private_rate: Optional[float] = None
    co_applicants: Optional[list[str]] = None
    visibility: Optional[str] = None
