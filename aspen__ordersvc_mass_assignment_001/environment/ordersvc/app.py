from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException

from ordersvc import store
from ordersvc.models import Order, OrderCreate, OrderPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/orders", status_code=201)
def create_order(body: OrderCreate, x_user_id: str = Header(...)) -> Order:
    # BUG: body.status, body.discount_pct, and body.payment_status are accepted
    # from the request body without any role check — a regular user can create
    # an order with status="shipped" or discount_pct=100.0 at creation time.
    return store.create(
        owner_id=x_user_id,
        status=body.status,
        items=body.items,
        shipping_address=body.shipping_address,
        notes=body.notes,
        discount_pct=body.discount_pct,
        payment_status=body.payment_status,
    )


@app.get("/orders")
def list_orders(x_user_id: str = Header(...)):
    return store.list_all()


@app.get("/orders/{order_id}")
def get_order(order_id: str, x_user_id: str = Header(...)) -> Order:
    order = store.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Not found")
    return order


@app.patch("/orders/{order_id}")
def patch_order(
    order_id: str, body: OrderPatch, x_user_id: str = Header(...)
) -> Order:
    order = store.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and order.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # BUG: no field-level role check — OrderPatch includes privileged fields
    # (status, discount_pct, payment_status) and all non-None values are applied
    # without verifying the caller has permission to set those fields.
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = store.update(order_id, **updates)
    return updated


@app.post("/orders/{order_id}/confirm", status_code=200)
def confirm_order(order_id: str, x_user_id: str = Header(...)) -> Order:
    order = store.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(order_id, status="confirmed")
    return updated


@app.post("/orders/{order_id}/cancel", status_code=200)
def cancel_order(order_id: str, x_user_id: str = Header(...)) -> Order:
    order = store.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and order.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(order_id, status="cancelled")
    return updated
