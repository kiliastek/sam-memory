"""Meeting — a scheduled or completed conversation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from sam.models.enums import MeetingStatus, MeetingType


class Meeting(BaseModel):
    """A meeting with one or more stakeholders at a single account."""

    id: int | None = None
    account_slug: str
    stakeholder_ids: list[int] = Field(default_factory=list)
    scheduled_at: datetime
    meeting_type: MeetingType
    status: MeetingStatus = MeetingStatus.SCHEDULED
    outcome: str | None = None
    next_step: str | None = None
