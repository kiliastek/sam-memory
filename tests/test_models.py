"""Pydantic model validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sam.models import (
    Account,
    Hypothesis,
    MeddpiccRole,
    OutcomeMetric,
    Qualification,
    Stakeholder,
)


class TestAccount:
    def test_valid_slug(self) -> None:
        a = Account(slug="acme-corp", name="Acme Corp", tier=1)
        assert a.slug == "acme-corp"
        assert a.paused is False

    def test_slug_must_be_url_safe(self) -> None:
        with pytest.raises(ValidationError):
            Account(slug="Acme Corp!", name="Acme Corp", tier=1)

    def test_slug_starts_with_alnum(self) -> None:
        with pytest.raises(ValidationError):
            Account(slug="-leading-hyphen", name="x", tier=1)

    def test_tier_bounds(self) -> None:
        with pytest.raises(ValidationError):
            Account(slug="acme", name="Acme", tier=0)
        with pytest.raises(ValidationError):
            Account(slug="acme", name="Acme", tier=4)

    def test_paused_requires_reason(self) -> None:
        with pytest.raises(ValidationError):
            Account(slug="acme", name="Acme", tier=2, paused=True)
        a = Account(slug="acme", name="Acme", tier=2, paused=True, paused_reason="Out of territory")
        assert a.paused_reason == "Out of territory"


class TestStakeholder:
    def test_defaults(self) -> None:
        s = Stakeholder(account_slug="acme", name="Jane", title="CTO")
        assert s.meddpicc_role == MeddpiccRole.UNKNOWN
        assert s.prior_employers == []

    def test_meddpicc_enum(self) -> None:
        s = Stakeholder(
            account_slug="acme", name="Jane", title="CTO", meddpicc_role=MeddpiccRole.CHAMPION
        )
        assert s.meddpicc_role == MeddpiccRole.CHAMPION


class TestHypothesis:
    def test_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            Hypothesis(
                account_slug="acme",
                headline="x",
                outcome_metric=OutcomeMetric.COST_REDUCTION,
            )  # type: ignore[call-arg]
            # missing falsification_test


class TestQualification:
    def test_completeness_score_zero(self) -> None:
        q = Qualification(account_slug="acme")
        assert q.completeness_score == 0

    def test_completeness_score_partial(self) -> None:
        q = Qualification(
            account_slug="acme",
            metrics="MTTR -20%",
            economic_buyer_id=1,
            champion_id=2,
            implied_pain="manual triage",
        )
        # 4 of 8 fields filled = 50
        assert q.completeness_score == 50

    def test_completeness_score_full(self) -> None:
        q = Qualification(
            account_slug="acme",
            metrics="m",
            economic_buyer_id=1,
            decision_criteria="d",
            decision_process="p",
            paper_process="pp",
            implied_pain="ip",
            champion_id=2,
            competition="c",
        )
        assert q.completeness_score == 100
