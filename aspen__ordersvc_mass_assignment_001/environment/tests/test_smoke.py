"""Smoke tests — encodes the normal-operation surface. Not the bug.

Teaches the agent:
  - Regular users create orders; status starts at 'pending', discount_pct at 0.0
  - Owners can PATCH non-privileged fields (shipping_address, notes)
  - Admin is the ONLY caller who can legitimately set status and discount_pct via PATCH
  - Owners can cancel their own orders via POST /orders/{id}/cancel
  - Strangers cannot PATCH an order they do not own (403)
"""
from fastapi.testclient import TestClient
from ordersvc.app import app

client = TestClient(app)

ITEMS = [{"name": "Widget", "qty": 2, "unit_price": 9.99}]


def test_create_order_defaults():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "1 Main St"},
        headers={"x-user-id": "alice"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "pending"
    assert data["discount_pct"] == 0.0
    assert data["payment_status"] == "unpaid"
    assert data["owner_id"] == "alice"


def test_owner_patch_shipping_address():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "1 Main St"},
        headers={"x-user-id": "bob"},
    )
    oid = r.json()["id"]
    r2 = client.patch(
        f"/orders/{oid}",
        json={"shipping_address": "2 Oak Ave"},
        headers={"x-user-id": "bob"},
    )
    assert r2.status_code == 200
    assert r2.json()["shipping_address"] == "2 Oak Ave"


def test_owner_patch_notes():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "3 Elm St"},
        headers={"x-user-id": "carol"},
    )
    oid = r.json()["id"]
    r2 = client.patch(
        f"/orders/{oid}",
        json={"notes": "leave at door"},
        headers={"x-user-id": "carol"},
    )
    assert r2.status_code == 200
    assert r2.json()["notes"] == "leave at door"


def test_admin_can_confirm_order():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "4 Pine Rd"},
        headers={"x-user-id": "dave"},
    )
    oid = r.json()["id"]
    r2 = client.post(f"/orders/{oid}/confirm", headers={"x-user-id": "admin"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "confirmed"


def test_admin_can_set_discount():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "5 Birch Ln"},
        headers={"x-user-id": "eve"},
    )
    oid = r.json()["id"]
    r2 = client.patch(
        f"/orders/{oid}",
        json={"discount_pct": 15.0},
        headers={"x-user-id": "admin"},
    )
    assert r2.status_code == 200
    assert r2.json()["discount_pct"] == 15.0


def test_owner_can_cancel_order():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "6 Cedar Way"},
        headers={"x-user-id": "frank"},
    )
    oid = r.json()["id"]
    r2 = client.post(f"/orders/{oid}/cancel", headers={"x-user-id": "frank"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "cancelled"


def test_stranger_cannot_patch_order():
    r = client.post(
        "/orders",
        json={"items": ITEMS, "shipping_address": "7 Maple Dr"},
        headers={"x-user-id": "grace"},
    )
    oid = r.json()["id"]
    r2 = client.patch(
        f"/orders/{oid}",
        json={"notes": "hijacked"},
        headers={"x-user-id": "mallory"},
    )
    assert r2.status_code == 403
