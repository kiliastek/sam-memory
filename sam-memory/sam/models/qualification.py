"""Qualification — MEDDPICC state per Account."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, computed_field


class Qualification(BaseModel):
    """One MEDDPICC qualification per Account.

    Every field is optional because qualification is incremental — you
    rarely know all eight elements at first touch. `completeness_score`
    is the % of fields populated and gives a quick visual of where the
    gaps are.
    """

    account_slug: str
    metrics: str | None = None
    economic_buyer_id: int | None = None
    decision_criteria: str | None = None
    decision_process: str | None = None
    paper_process: str | None = None
    implied_pain: str | None = None
    champion_id: int | None = None
    competition: str | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field  # type: ignore[misc]
    @property
    def completeness_score(self) -> int:
        """Percentage of MEDDPICC fields populated (0-100)."""
        fields = [
            self.metrics,
            self.economic_buyer_id,
            self.decision_criteria,
            self.decision_process,
            self.paper_process,
            self.implied_pain,
            self.champion_id,
            self.competition,
        ]
        filled = sum(1 for f in fields if f not in (None, ""))
        return int(round(filled / len(fields) * 100))
