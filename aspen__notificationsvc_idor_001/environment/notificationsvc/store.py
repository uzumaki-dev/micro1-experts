from __future__ import annotations
import uuid
from notificationsvc.models import Notification, DeliveryEntry

_notifications: dict[str, Notification] = {}


def reset() -> None:
    _notifications.clear()


def create(
    owner_id: str,
    subject: str,
    recipient: str = "",
    status: str = "draft",
    private_body: str = "",
    delivery_log: list[DeliveryEntry] | None = None,
    attachments: dict[str, str] | None = None,
    shared_with: list[str] | None = None,
    visibility: str = "private",
) -> Notification:
    notif = Notification(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        subject=subject,
        recipient=recipient,
        status=status,
        private_body=private_body,
        delivery_log=delivery_log or [],
        attachments=attachments or {},
        shared_with=shared_with or [],
        visibility=visibility,
    )
    _notifications[notif.id] = notif
    return notif


def get(notification_id: str) -> Notification | None:
    return _notifications.get(notification_id)


def list_all() -> list[Notification]:
    return list(_notifications.values())


def update(notification_id: str, **kwargs) -> Notification | None:
    notif = _notifications.get(notification_id)
    if notif is None:
        return None
    updated = notif.model_copy(update={k: v for k, v in kwargs.items()})
    _notifications[notification_id] = updated
    return updated
