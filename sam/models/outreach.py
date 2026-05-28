"""OutreachThread — a relationship channel; Touch — a single message in it."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from sam.models.enums import Channel, ThreadStatus, TouchDirection


class OutreachThread(BaseModel):
    """A persistent relationship channel with a single stakeholder.

    A stakeholder may have multiple threads (one per channel — LinkedIn,
    Email, InMail). Each thread tracks its own lifecycle.
    """

    id: int | None = None
    stakeholder_id: int
    channel: Channel
    status: ThreadStatus = ThreadStatus.DRAFTED
    opened_at: datetime | None = None
    last_touch_at: datetime | None = None
    next_review_at: datetime | None = None


class Touch(BaseModel):
    """A single message inside an OutreachThread. Append-only.

    Touches are never edited — if a sent message bounces, log a new
    inbound touch with `outcome='bounced'` rather than mutating the
    original.
    """

    id: int | None = None
    thread_id: int
    direction: TouchDirection
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    body: str
    outcome: str | None = None
