"""Stakeholder — a person at an Account."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from sam.models.enums import MeddpiccRole


class Stakeholder(BaseModel):
    """A contact at an Account.

    A stakeholder belongs to exactly one Account. A person who genuinely
    works at two of your accounts (rare, but possible — e.g. board overlap)
    should be modelled as two Stakeholder records.
    """

    id: int | None = None
    account_slug: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    email: str | None = None
    linkedin_url: str | None = None
    meddpicc_role: MeddpiccRole = MeddpiccRole.UNKNOWN
    tenure_months: Annotated[int | None, Field(default=None, ge=0)] = None
    prior_employers: list[str] = Field(default_factory=list)
    notes: str | None = None
