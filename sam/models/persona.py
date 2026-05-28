"""Persona — the AE running this memory store (L3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """The AE this memory store belongs to.

    One Persona per memory store. The persona is what L3 holds — the
    stable identity layer that every other lookup loads against.
    """

    name: str
    role: str
    company: str
    territory: str
    manager: str | None = None
    pod: dict[str, str] = Field(default_factory=dict)
    methodology: str = "MEDDPICC"
    first_touch_style: str
    partner_channels: list[str] = Field(default_factory=list)
    working_style: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
