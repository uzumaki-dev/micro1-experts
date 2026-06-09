from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from notificationsvc import store
from notificationsvc.models import Notification, NotificationCreate, NotificationPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/notifications", status_code=201)
def create_notification(body: NotificationCreate, x_user_id: str = Header(...)) -> Notification:
    return store.create(
        owner_id=x_user_id,
        subject=body.subject,
        recipient=body.recipient,
        private_body=body.private_body,
        delivery_log=body.delivery_log,
        attachments=body.attachments,
        shared_with=body.shared_with,
        visibility=body.visibility,
    )


@app.get("/notifications")
def list_notifications(x_user_id: str = Header(...)) -> list[Notification]:
    # BUG: returns all notifications regardless of ownership
    return store.list_all()


@app.get("/notifications/search")
def search_notifications(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Notification]:
    # BUG: searches across all notifications regardless of ownership
    q_lower = q.lower()
    return [
        notif
        for notif in store.list_all()
        if q_lower in notif.subject.lower() or q_lower in notif.private_body.lower()
    ]


@app.get("/notifications/{notification_id}")
def get_notification(notification_id: str, x_user_id: str = Header(...)) -> Notification:
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any notification
    return notif


@app.get("/notifications/{notification_id}/delivery-log")
def get_delivery_log(notification_id: str, x_user_id: str = Header(...)):
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return notif.delivery_log


@app.get("/notifications/{notification_id}/export")
def export_notification(
    notification_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "subject", "recipient", "status", "private_body",
            "dl_timestamp", "dl_status", "channel_code",
        ])
        for entry in notif.delivery_log:
            writer.writerow([
                notif.id, notif.subject, notif.recipient, notif.status,
                notif.private_body,
                entry.timestamp, entry.status, entry.channel_code,
            ])
        if not notif.delivery_log:
            writer.writerow([
                notif.id, notif.subject, notif.recipient, notif.status,
                notif.private_body, "", "", "",
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return notif


@app.get("/notifications/{notification_id}/attachments")
def get_attachment(
    notification_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = notif.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all notifications
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_notif in store.list_all():
                other_content = other_notif.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.post("/notifications/{notification_id}/duplicate", status_code=201)
def duplicate_notification(notification_id: str, x_user_id: str = Header(...)) -> Notification:
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits private_body, delivery_log, and attachments without scrubbing
    return store.create(
        owner_id=x_user_id,
        subject=notif.subject,
        recipient=notif.recipient,
        status="draft",
        private_body=notif.private_body,      # BUG: copies private body
        delivery_log=notif.delivery_log,       # BUG: copies delivery log with channel_codes
        attachments=notif.attachments,         # BUG: copies private attachments
        shared_with=[],
        visibility="private",
    )


@app.patch("/notifications/{notification_id}")
def patch_notification(
    notification_id: str, body: NotificationPatch, x_user_id: str = Header(...)
) -> Notification:
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and notif.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    return store.update(notification_id, **updates)  # type: ignore[return-value]


@app.post("/notifications/{notification_id}/forward")
def forward_notification(notification_id: str, x_user_id: str = Header(...)) -> Notification:
    notif = store.get(notification_id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and notif.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # BUG: response returns notification with private_body intact (no scrubbing on forward)
    return store.update(notification_id, status="forwarded")  # type: ignore[return-value]
