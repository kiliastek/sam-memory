"""WarmRoute — a path to a Stakeholder through an intermediary."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from sam.models.enums import WarmRouteStatus, WarmRouteType


class WarmRoute(BaseModel):
    """A way to reach a Stakeholder that isn't cold outreach.

    Partner-mediated, internal-colleague-mediated, alumni network, mutual
    connection, existing customer. The intermediary is the `via` field;
    they don't need to be a Stakeholder themselves.
    """

    id: int | None = None
    target_stakeholder_id: int
    via: str
    via_type: WarmRouteType
    status: WarmRouteStatus = WarmRouteStatus.IDENTIFIED
    notes: str | None = None
    requested_at: datetime | None = None
