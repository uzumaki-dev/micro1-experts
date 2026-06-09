from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class DeliveryEntry(BaseModel):
    timestamp: str = ""
    status: str = "pending"
    channel_code: str = ""


class NotificationCreate(BaseModel):
    subject: str
    recipient: str = ""
    private_body: str = ""
    delivery_log: list[DeliveryEntry] = []
    attachments: dict[str, str] = {}
    shared_with: list[str] = []
    visibility: str = "private"


class NotificationPatch(BaseModel):
    subject: Optional[str] = None
    recipient: Optional[str] = None
    private_body: Optional[str] = None
    shared_with: Optional[list[str]] = None
    visibility: Optional[str] = None
    status: Optional[str] = None


class Notification(BaseModel):
    id: str
    owner_id: str
    subject: str
    recipient: str
    status: str
    private_body: str
    delivery_log: list[DeliveryEntry]
    attachments: dict[str, str]
    shared_with: list[str]
    visibility: str
