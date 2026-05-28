"""Hypothesis — the commercial framing for why an Account is in pursuit."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from sam.models.enums import HypothesisStatus, OutcomeMetric


class Hypothesis(BaseModel):
    """A one-sentence commercial framing with a falsification test.

    If you can't articulate the falsification test, you don't have a
    hypothesis — you have a wish. The whole point of this entity is to
    force the discipline of saying what would make you walk away.
    """

    id: int | None = None
    account_slug: str
    headline: str
    falsification_test: str
    outcome_metric: OutcomeMetric
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
