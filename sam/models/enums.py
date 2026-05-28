"""Enumerations used across SAM schemas.

These vocabularies are deliberately small. If you need more states, fork
this file — but think hard before adding a new value, because every
downstream report and search filter has to know about it.
"""

from __future__ import annotations

from enum import Enum


class MeddpiccRole(str, Enum):
    """Role of a stakeholder in the MEDDPICC qualification model."""

    ECONOMIC_BUYER = "EconomicBuyer"
    CHAMPION = "Champion"
    COACH = "Coach"
    INFLUENCER = "Influencer"
    USER = "User"
    BLOCKER = "Blocker"
    UNKNOWN = "Unknown"


class Channel(str, Enum):
    """Outreach channel."""

    LINKEDIN = "LinkedIn"
    EMAIL = "Email"
    INMAIL = "InMail"
    PHONE = "Phone"
    IN_PERSON = "InPerson"


class ThreadStatus(str, Enum):
    """Lifecycle state of an outreach thread."""

    DRAFTED = "Drafted"
    SENT = "Sent"
    CONNECTED = "Connected"
    AWAITING = "Awaiting"
    REPLIED = "Replied"
    WITHDRAWN = "Withdrawn"
    BOUNCED = "Bounced"
    CLOSED = "Closed"


class TouchDirection(str, Enum):
    """Direction of a single touch within a thread."""

    OUTBOUND = "Outbound"
    INBOUND = "Inbound"


class MeetingType(str, Enum):
    DISCOVERY = "Discovery"
    DEMO = "Demo"
    WORKSHOP = "Workshop"
    EBR = "EBR"
    CLOSING = "Closing"
    FOLLOW_UP = "FollowUp"


class MeetingStatus(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    NO_SHOW = "NoShow"
    CANCELLED = "Cancelled"


class SignalType(str, Enum):
    EARNINGS = "Earnings"
    FUNDING = "Funding"
    MA = "MA"
    LEADERSHIP_MOVE = "LeadershipMove"
    RFP = "RFP"
    LAYOFFS = "Layoffs"
    PRODUCT_LAUNCH = "ProductLaunch"
    PRESS_MENTION = "PressMention"
    REGULATORY_ACTION = "RegulatoryAction"
    OTHER = "Other"


class Relevance(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class OutcomeMetric(str, Enum):
    """The measurable business outcome a hypothesis targets."""

    REVENUE_GROWTH = "RevenueGrowth"
    COST_REDUCTION = "CostReduction"
    OPERATIONAL_RESILIENCE = "OperationalResilience"
    TIME_TO_MARKET = "TimeToMarket"


class HypothesisStatus(str, Enum):
    ACTIVE = "Active"
    CONFIRMED = "Confirmed"
    FALSIFIED = "Falsified"
    STALE = "Stale"


class WarmRouteType(str, Enum):
    PARTNER = "Partner"
    INTERNAL = "Internal"
    ALUMNI = "Alumni"
    MUTUAL = "Mutual"
    CUSTOMER = "Customer"


class WarmRouteStatus(str, Enum):
    IDENTIFIED = "Identified"
    REQUESTED = "Requested"
    IN_PROGRESS = "InProgress"
    DELIVERED = "Delivered"
    DECLINED = "Declined"
