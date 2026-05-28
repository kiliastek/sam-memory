"""Signal — a dated commercial trigger about an Account."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from sam.models.enums import Relevance, SignalType


class Signal(BaseModel):
    """A commercial signal — earnings, M&A, hire, RFP, leadership move.

    Signals are the raw fuel of sales hypotheses. Anything that would
    change how you think about the account, with a date and a source.
    """

    id: int | None = None
    account_slug: str
    detected_at: datetime
    signal_type: SignalType
    headline: str
    source_url: str | None = None
    relevance: Relevance = Relevance.MEDIUM
    notes: str | None = None
