"""Account — the unit of pursuit."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]{0,63}$")


class Account(BaseModel):
    """A target company.

    One per company in the territory. `slug` is the primary key and must be
    URL-safe (lowercase alphanumeric + hyphens). It's used in markdown file
    paths, CLI args, and foreign keys, so changing it later is painful.
    """

    slug: Annotated[str, Field(min_length=1, max_length=64)]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    tier: Annotated[int, Field(ge=1, le=3)]
    vertical: str | None = None
    hq: str | None = None
    parent: str | None = None
    ownership: str | None = None
    headcount: Annotated[int | None, Field(default=None, ge=0)] = None
    revenue_band: str | None = None
    paused: bool = False
    paused_reason: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, v: str) -> str:
        if not _SLUG_PATTERN.match(v):
            raise ValueError(
                "slug must be lowercase alphanumeric with hyphens "
                "(e.g. 'acme-corp'), 1-64 chars, starting with a letter or digit"
            )
        return v

    @model_validator(mode="after")
    def _require_reason_if_paused(self) -> "Account":
        if self.paused and not self.paused_reason:
            raise ValueError("paused_reason is required when paused=True")
        return self
