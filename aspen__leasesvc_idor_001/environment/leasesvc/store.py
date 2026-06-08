from __future__ import annotations
from leasesvc.models import Lease

_store: dict[str, Lease] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    tenant_name: str = "Unnamed Tenant",
    property_address: str = "",
    status: str = "draft",
    visibility: str = "private",
    collaborators: list | None = None,
    private_notes: str = "",
    clauses: list | None = None,
    attachments: dict | None = None,
) -> Lease:
    lease = Lease(
        owner_id=owner_id,
        tenant_name=tenant_name,
        property_address=property_address,
        status=status,
        visibility=visibility,
        collaborators=collaborators or [],
        private_notes=private_notes,
        clauses=clauses or [],
        attachments=attachments or {},
    )
    _store[lease.id] = lease
    return lease


def get(lease_id: str) -> Lease | None:
    return _store.get(lease_id)


def list_all() -> list[Lease]:
    return list(_store.values())


def update(lease_id: str, **kwargs) -> Lease | None:
    lease = _store.get(lease_id)
    if lease is None:
        return None
    data = lease.model_dump()
    data.update(kwargs)
    updated = Lease(**data)
    _store[lease_id] = updated
    return updated
