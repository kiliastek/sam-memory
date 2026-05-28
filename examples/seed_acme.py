"""Seed the example dataset — fictional Acme Corp + Globex Industries.

Run from a directory where you want a SAM store to live:

    python examples/seed_acme.py

This will create .sam/ under the current working directory and populate
it with two fictional accounts, a few stakeholders each, one signal,
one hypothesis, one MEDDPICC update, one warm route, and one persona.

Useful for kicking the tyres of the CLI:

    sam account list
    sam scene acme-corp
    sam qualify show acme-corp

Everything in this script is fictional. Any resemblance to real
companies or people is coincidental.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sam.memory import (
    append_atom,
    init_memory_dirs,
    write_persona,
    write_scene,
)
from sam.models import (
    Account,
    Channel,
    Hypothesis,
    HypothesisStatus,
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
    WarmRoute,
    WarmRouteStatus,
    WarmRouteType,
)
from sam.storage import Repository, get_db
from pathlib import Path


def main() -> None:
    root = Path.cwd()
    init_memory_dirs(root)
    repo = Repository(get_db())

    # ----- Persona -------------------------------------------------------
    persona = Persona(
        name="Jane Smith",
        role="Enterprise Account Executive",
        company="ExampleCo",
        territory="EMEA-NORTH-1",
        manager="Alex Rivera",
        pod={"ADR": "Sam Kim", "SC": "Priya Patel", "Legal": "Chris Doe"},
        methodology="MEDDPICC",
        first_touch_style="LinkedIn ≤300 chars, peer-level, no product mention, anchored on a specific verifiable public signal.",
        partner_channels=["Globex Capital — Tomas Lee", "Initech Partners — Robin Park"],
        working_style="Bottom-line first, then rationale. Client-ready by default. No buzzwords without substance.",
    )
    repo.upsert_persona(persona)
    write_persona(root, persona)

    # ----- Account 1: Acme Corp ------------------------------------------
    acme = Account(
        slug="acme-corp",
        name="Acme Corp",
        tier=1,
        vertical="Telco",
        hq="London, UK",
        ownership="Public — LSE: ACME",
        headcount=4500,
        revenue_band="$500M-$5B",
    )
    repo.upsert_account(acme)
    append_atom(root, acme.slug, acme.name, "Account opened at Tier 1; Telco vertical.")

    jane = repo.add_stakeholder(
        Stakeholder(
            account_slug=acme.slug,
            name="Jane Doe",
            title="Chief Technology Officer",
            email="jane.doe@acme.example.com",
            linkedin_url="https://www.linkedin.com/in/jane-doe-example",
            meddpicc_role=MeddpiccRole.CHAMPION,
            tenure_months=14,
            prior_employers=["Globex Industries", "Initech Ltd"],
            notes="Ex-Globex platform-consolidation lead; spoke at AcmeTech 2025.",
        )
    )
    jordan = repo.add_stakeholder(
        Stakeholder(
            account_slug=acme.slug,
            name="Jordan Lee",
            title="Chief Financial Officer",
            email="jordan.lee@acme.example.com",
            meddpicc_role=MeddpiccRole.ECONOMIC_BUYER,
            tenure_months=2,
            prior_employers=["Globex Industries"],
        )
    )
    append_atom(root, acme.slug, acme.name, "Identified Jane Doe (CTO) as Champion candidate.")
    append_atom(root, acme.slug, acme.name, "New CFO Jordan Lee — Economic Buyer; ex-Globex.")

    repo.add_signal(
        Signal(
            account_slug=acme.slug,
            detected_at=datetime.utcnow() - timedelta(days=10),
            signal_type=SignalType.LEADERSHIP_MOVE,
            headline="New CFO Jordan Lee appointed (ex-Globex)",
            source_url="https://example.com/press/jordan-lee",
            relevance=Relevance.HIGH,
        )
    )
    repo.add_signal(
        Signal(
            account_slug=acme.slug,
            detected_at=datetime.utcnow() - timedelta(days=3),
            signal_type=SignalType.EARNINGS,
            headline="Acme Q2 results: revenue +4%, op-margin -120bps",
            source_url="https://example.com/press/acme-q2",
            relevance=Relevance.MEDIUM,
        )
    )

    repo.upsert_hypothesis(
        Hypothesis(
            account_slug=acme.slug,
            headline=(
                "Acme's Q3 platform-consolidation programme creates demand for a workflow spine "
                "that lets the post-merger ops function as one motion."
            ),
            falsification_test=(
                "If Jane says each subsidiary keeps its own back-office tooling and the consolidation "
                "is scoped to customer-facing systems only, the hypothesis is dead."
            ),
            outcome_metric=OutcomeMetric.OPERATIONAL_RESILIENCE,
            status=HypothesisStatus.ACTIVE,
        )
    )

    repo.upsert_qualification(
        Qualification(
            account_slug=acme.slug,
            metrics="20% reduction in incident MTTR by FY27.",
            economic_buyer_id=jordan.id,
            champion_id=jane.id,
            implied_pain="Three-acquisition platform sprawl; manual triage burning ops headcount.",
            competition="Incumbent: BMC. Also evaluating Atlassian JSM.",
            decision_criteria="TCO over 5 yrs + time-to-integrate new acquisitions.",
        )
    )

    # Outbound LinkedIn touch
    thread = repo.open_thread(
        OutreachThread(stakeholder_id=jane.id, channel=Channel.LINKEDIN, status=ThreadStatus.CONNECTED)
    )
    repo.log_touch(
        Touch(
            thread_id=thread.id,
            direction=TouchDirection.OUTBOUND,
            body=(
                "Hi Jane — saw your interview on Q3 platform consolidation. Would love to compare "
                "notes peer-level. No sales agenda, 15 mins."
            ),
            outcome="connected",
        )
    )
    repo.log_touch(
        Touch(
            thread_id=thread.id,
            direction=TouchDirection.INBOUND,
            body="Sure, send a Calendly link.",
            outcome="replied",
        )
    )

    repo.add_warm_route(
        WarmRoute(
            target_stakeholder_id=jane.id,
            via="Sam Patel (ex-Globex colleague)",
            via_type=WarmRouteType.ALUMNI,
            status=WarmRouteStatus.DELIVERED,
            notes="Sam worked with Jane at Globex 2019-2022. Intro made 2026-05-15.",
            requested_at=datetime.utcnow() - timedelta(days=18),
        )
    )

    write_scene(
        root,
        acme.slug,
        name=acme.name,
        key_stakeholder="Jane Doe, CTO — Champion candidate, ex-Globex platform-consolidation lead.",
        strategic_context="Acme is mid-way through a post-merger Q3 platform consolidation programme; new CFO ex-Globex.",
        sales_motion="Position as the workflow spine underneath the consolidation programme.",
        entry_point="Active LinkedIn thread with Jane (connected); warm intro via Sam Patel delivered.",
        last_touch="2026-05-15 — Jane replied 'Sure, send a Calendly link' on LinkedIn.",
        top_blocker="BMC incumbent in ITSM; Atlassian JSM in evaluation.",
        next_action="Send Calendly link for 15-min discovery; pre-call brief Tuesday.",
    )

    # ----- Account 2: Globex Industries ---------------------------------
    globex = Account(
        slug="globex-industries",
        name="Globex Industries",
        tier=2,
        vertical="Manufacturing",
        hq="Frankfurt, DE",
        ownership="PE-backed (Atlas Partners)",
        headcount=12000,
        revenue_band="$500M-$5B",
    )
    repo.upsert_account(globex)
    append_atom(root, globex.slug, globex.name, "Account opened at Tier 2; Manufacturing vertical.")

    chris = repo.add_stakeholder(
        Stakeholder(
            account_slug=globex.slug,
            name="Chris Müller",
            title="VP IT Operations",
            email="chris.mueller@globex.example.com",
            meddpicc_role=MeddpiccRole.COACH,
            tenure_months=36,
        )
    )
    write_scene(
        root,
        globex.slug,
        name=globex.name,
        key_stakeholder="Chris Müller, VP IT Operations — Coach altitude, ex-customer at Initech.",
        strategic_context="Globex is in the second year of an Atlas Partners exit-prep cycle.",
        sales_motion="Operating-platform consolidation; target operational resilience metric.",
        entry_point="Cold LinkedIn — no warm route yet.",
        last_touch="None yet",
        top_blocker="No identified Economic Buyer.",
        next_action="LinkedIn first-touch to Chris anchored on Atlas exit-prep timing.",
    )

    print(f"Seeded {root}/.sam/ with Acme Corp + Globex Industries fictional dataset.")
    print("Try:  sam account list  |  sam scene acme-corp  |  sam qualify show acme-corp")


if __name__ == "__main__":
    main()
