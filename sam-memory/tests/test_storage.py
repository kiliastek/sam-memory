"""SQLite storage smoke tests."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from sam.models import (
    Account,
    Channel,
    Hypothesis,
    MeddpiccRole,
    OutcomeMetric,
    OutreachThread,
    Persona,
    Qualification,
    Relevance,
    Signal,
    SignalType,
    Stakeholder,
    ThreadStatus,
    Touch,
    TouchDirection,
)
from sam.storage import Repository
from sam.storage.db import Database


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    db = Database(tmp_path / "sam.db")
    return Repository(db)


def test_account_roundtrip(repo: Repository) -> None:
    a = Account(slug="acme", name="Acme Corp", tier=1, vertical="Telco")
    repo.upsert_account(a)
    loaded = repo.get_account("acme")
    assert loaded is not None
    assert loaded.name == "Acme Corp"
    assert loaded.tier == 1
    assert loaded.vertical == "Telco"


def test_account_list_filters(repo: Repository) -> None:
    repo.upsert_account(Account(slug="acme", name="Acme", tier=1, vertical="Telco"))
    repo.upsert_account(Account(slug="globex", name="Globex", tier=2, vertical="Manufacturing"))
    repo.upsert_account(Account(slug="initech", name="Initech", tier=2, vertical="Telco"))
    t2 = repo.list_accounts(tier=2)
    assert {a.slug for a in t2} == {"globex", "initech"}
    telco = repo.list_accounts(vertical="Telco")
    assert {a.slug for a in telco} == {"acme", "initech"}


def test_stakeholder_lifecycle(repo: Repository) -> None:
    repo.upsert_account(Account(slug="acme", name="Acme", tier=1))
    s = repo.add_stakeholder(
        Stakeholder(
            account_slug="acme",
            name="Jane Doe",
            title="CTO",
            meddpicc_role=MeddpiccRole.CHAMPION,
            prior_employers=["Globex", "Initech"],
        )
    )
    assert s.id is not None
    found = repo.find_stakeholder("acme", "Jane Doe")
    assert found is not None
    assert found.meddpicc_role == MeddpiccRole.CHAMPION
    assert found.prior_employers == ["Globex", "Initech"]


def test_thread_and_touch_logging(repo: Repository) -> None:
    repo.upsert_account(Account(slug="acme", name="Acme", tier=1))
    s = repo.add_stakeholder(Stakeholder(account_slug="acme", name="Jane", title="CTO"))
    t = repo.open_thread(
        OutreachThread(stakeholder_id=s.id, channel=Channel.LINKEDIN, status=ThreadStatus.SENT)
    )
    repo.log_touch(
        Touch(thread_id=t.id, direction=TouchDirection.OUTBOUND, body="Hi Jane.", outcome="sent")
    )
    repo.log_touch(
        Touch(thread_id=t.id, direction=TouchDirection.INBOUND, body="Hi back.", outcome="replied")
    )
    touches = repo.list_touches(t.id)
    assert len(touches) == 2
    assert touches[0].direction == TouchDirection.OUTBOUND
    assert touches[1].direction == TouchDirection.INBOUND


def test_signal_and_hypothesis(repo: Repository) -> None:
    repo.upsert_account(Account(slug="acme", name="Acme", tier=1))
    repo.add_signal(
        Signal(
            account_slug="acme",
            detected_at=datetime.utcnow(),
            signal_type=SignalType.EARNINGS,
            headline="Q2 revenue +4%",
            relevance=Relevance.MEDIUM,
        )
    )
    assert len(repo.list_signals("acme")) == 1
    repo.upsert_hypothesis(
        Hypothesis(
            account_slug="acme",
            headline="Platform consolidation hypothesis.",
            falsification_test="Subsidiaries keep their own back-office stacks.",
            outcome_metric=OutcomeMetric.OPERATIONAL_RESILIENCE,
        )
    )
    assert len(repo.list_hypotheses("acme")) == 1


def test_qualification_upsert_score(repo: Repository) -> None:
    repo.upsert_account(Account(slug="acme", name="Acme", tier=1))
    s = repo.add_stakeholder(
        Stakeholder(account_slug="acme", name="Jane", title="CTO", meddpicc_role=MeddpiccRole.CHAMPION)
    )
    q = repo.upsert_qualification(
        Qualification(
            account_slug="acme",
            metrics="MTTR -20%",
            champion_id=s.id,
            implied_pain="manual triage",
        )
    )
    # 3 of 8 fields = 37.5%; Python's banker's-rounding turns this into 38.
    assert q.completeness_score == 38
    loaded = repo.get_qualification("acme")
    assert loaded is not None
    assert loaded.metrics == "MTTR -20%"
    # Re-upsert overwrites
    repo.upsert_qualification(
        Qualification(
            account_slug="acme",
            metrics="MTTR -25%",
            champion_id=s.id,
            implied_pain="manual triage",
            competition="BMC + Atlassian",
        )
    )
    again = repo.get_qualification("acme")
    assert again is not None
    assert again.metrics == "MTTR -25%"
    assert again.competition == "BMC + Atlassian"


def test_persona_singleton(repo: Repository) -> None:
    p = Persona(
        name="Jane Smith",
        role="AE",
        company="ExampleCo",
        territory="EMEA-1",
        methodology="MEDDPICC",
        first_touch_style="LinkedIn ≤300 chars",
        working_style="bottom-line first",
    )
    repo.upsert_persona(p)
    loaded = repo.get_persona()
    assert loaded is not None
    assert loaded.name == "Jane Smith"
    # Upsert preserves singleton invariant
    p2 = p.model_copy(update={"name": "Jane Smith Jr"})
    repo.upsert_persona(p2)
    loaded2 = repo.get_persona()
    assert loaded2 is not None
    assert loaded2.name == "Jane Smith Jr"


def test_search_text(repo: Repository) -> None:
    repo.upsert_account(Account(slug="acme", name="Acme Corp", tier=1, vertical="Telco"))
    s = repo.add_stakeholder(
        Stakeholder(account_slug="acme", name="Jane Doe", title="CTO", notes="ex-Globex")
    )
    repo.add_signal(
        Signal(
            account_slug="acme",
            detected_at=datetime.utcnow(),
            signal_type=SignalType.LEADERSHIP_MOVE,
            headline="New CFO ex-Globex",
        )
    )
    hits = repo.search_text("Globex")
    kinds = {h["kind"] for h in hits}
    assert "stakeholder" in kinds
    assert "signal" in kinds
