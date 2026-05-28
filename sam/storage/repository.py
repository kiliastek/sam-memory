"""Repository pattern for CRUD on SAM entities.

Every entity has the same shape of operations: ``create``, ``get``,
``update``, ``delete``, ``list``. The repository is a thin layer over
sqlite3 that handles JSON-typed columns (lists, dicts) and ISO-formatted
datetimes.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sam.models import (
    Account,
    Hypothesis,
    Meeting,
    OutreachThread,
    Persona,
    Qualification,
    Signal,
    Stakeholder,
    Touch,
    WarmRoute,
)
from sam.storage.db import Database


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse_dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def _json_dump(obj: Any) -> str | None:
    if obj in (None, [], {}):
        return None
    return json.dumps(obj)


def _json_load(s: str | None, default: Any) -> Any:
    if not s:
        return default
    return json.loads(s)


class Repository:
    """All CRUD operations on a SAM database."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ----- Account ------------------------------------------------------

    def upsert_account(self, account: Account) -> Account:
        account.updated_at = datetime.utcnow()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO account (slug, name, tier, vertical, hq, parent,
                    ownership, headcount, revenue_band, paused, paused_reason,
                    created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    name=excluded.name, tier=excluded.tier,
                    vertical=excluded.vertical, hq=excluded.hq,
                    parent=excluded.parent, ownership=excluded.ownership,
                    headcount=excluded.headcount,
                    revenue_band=excluded.revenue_band,
                    paused=excluded.paused, paused_reason=excluded.paused_reason,
                    updated_at=excluded.updated_at
                """,
                (
                    account.slug,
                    account.name,
                    account.tier,
                    account.vertical,
                    account.hq,
                    account.parent,
                    account.ownership,
                    account.headcount,
                    account.revenue_band,
                    int(account.paused),
                    account.paused_reason,
                    _iso(account.created_at),
                    _iso(account.updated_at),
                ),
            )
        return account

    def get_account(self, slug: str) -> Account | None:
        with self.db.cursor() as cur:
            row = cur.execute("SELECT * FROM account WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return None
        return Account(
            slug=row["slug"],
            name=row["name"],
            tier=row["tier"],
            vertical=row["vertical"],
            hq=row["hq"],
            parent=row["parent"],
            ownership=row["ownership"],
            headcount=row["headcount"],
            revenue_band=row["revenue_band"],
            paused=bool(row["paused"]),
            paused_reason=row["paused_reason"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )

    def list_accounts(
        self, *, tier: int | None = None, vertical: str | None = None
    ) -> list[Account]:
        sql = "SELECT * FROM account WHERE 1=1"
        params: list[Any] = []
        if tier is not None:
            sql += " AND tier = ?"
            params.append(tier)
        if vertical:
            sql += " AND vertical = ?"
            params.append(vertical)
        sql += " ORDER BY tier, name"
        with self.db.cursor() as cur:
            rows = cur.execute(sql, params).fetchall()
        return [self.get_account(r["slug"]) for r in rows]  # type: ignore[misc]

    # ----- Stakeholder --------------------------------------------------

    def add_stakeholder(self, s: Stakeholder) -> Stakeholder:
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO stakeholder (account_slug, name, title, email,
                    linkedin_url, meddpicc_role, tenure_months, prior_employers, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    s.account_slug,
                    s.name,
                    s.title,
                    s.email,
                    s.linkedin_url,
                    s.meddpicc_role.value,
                    s.tenure_months,
                    _json_dump(s.prior_employers),
                    s.notes,
                ),
            )
            s.id = cur.lastrowid
        return s

    def get_stakeholder(self, sid: int) -> Stakeholder | None:
        with self.db.cursor() as cur:
            row = cur.execute("SELECT * FROM stakeholder WHERE id = ?", (sid,)).fetchone()
        return self._row_to_stakeholder(row) if row else None

    def find_stakeholder(self, account_slug: str, name: str) -> Stakeholder | None:
        with self.db.cursor() as cur:
            row = cur.execute(
                "SELECT * FROM stakeholder WHERE account_slug = ? AND name = ?",
                (account_slug, name),
            ).fetchone()
        return self._row_to_stakeholder(row) if row else None

    def list_stakeholders(self, account_slug: str | None = None) -> list[Stakeholder]:
        with self.db.cursor() as cur:
            if account_slug:
                rows = cur.execute(
                    "SELECT * FROM stakeholder WHERE account_slug = ? ORDER BY name",
                    (account_slug,),
                ).fetchall()
            else:
                rows = cur.execute("SELECT * FROM stakeholder ORDER BY account_slug, name").fetchall()
        return [self._row_to_stakeholder(r) for r in rows]

    @staticmethod
    def _row_to_stakeholder(row: Any) -> Stakeholder:
        from sam.models.enums import MeddpiccRole

        return Stakeholder(
            id=row["id"],
            account_slug=row["account_slug"],
            name=row["name"],
            title=row["title"],
            email=row["email"],
            linkedin_url=row["linkedin_url"],
            meddpicc_role=MeddpiccRole(row["meddpicc_role"]),
            tenure_months=row["tenure_months"],
            prior_employers=_json_load(row["prior_employers"], []),
            notes=row["notes"],
        )

    # ----- OutreachThread + Touch --------------------------------------

    def open_thread(self, thread: OutreachThread) -> OutreachThread:
        thread.opened_at = thread.opened_at or datetime.utcnow()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO outreach_thread (stakeholder_id, channel, status,
                    opened_at, last_touch_at, next_review_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    thread.stakeholder_id,
                    thread.channel.value,
                    thread.status.value,
                    _iso(thread.opened_at),
                    _iso(thread.last_touch_at),
                    _iso(thread.next_review_at),
                ),
            )
            thread.id = cur.lastrowid
        return thread

    def log_touch(self, touch: Touch) -> Touch:
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO touch (thread_id, direction, sent_at, body, outcome)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    touch.thread_id,
                    touch.direction.value,
                    _iso(touch.sent_at),
                    touch.body,
                    touch.outcome,
                ),
            )
            touch.id = cur.lastrowid
            cur.execute(
                "UPDATE outreach_thread SET last_touch_at = ? WHERE id = ?",
                (_iso(touch.sent_at), touch.thread_id),
            )
        return touch

    def list_touches(self, thread_id: int) -> list[Touch]:
        from sam.models.enums import TouchDirection

        with self.db.cursor() as cur:
            rows = cur.execute(
                "SELECT * FROM touch WHERE thread_id = ? ORDER BY sent_at",
                (thread_id,),
            ).fetchall()
        return [
            Touch(
                id=r["id"],
                thread_id=r["thread_id"],
                direction=TouchDirection(r["direction"]),
                sent_at=_parse_dt(r["sent_at"]),
                body=r["body"],
                outcome=r["outcome"],
            )
            for r in rows
        ]

    # ----- Signal -------------------------------------------------------

    def add_signal(self, sig: Signal) -> Signal:
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signal (account_slug, detected_at, signal_type,
                    headline, source_url, relevance, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sig.account_slug,
                    _iso(sig.detected_at),
                    sig.signal_type.value,
                    sig.headline,
                    sig.source_url,
                    sig.relevance.value,
                    sig.notes,
                ),
            )
            sig.id = cur.lastrowid
        return sig

    def list_signals(self, account_slug: str) -> list[Signal]:
        from sam.models.enums import Relevance, SignalType

        with self.db.cursor() as cur:
            rows = cur.execute(
                "SELECT * FROM signal WHERE account_slug = ? ORDER BY detected_at DESC",
                (account_slug,),
            ).fetchall()
        return [
            Signal(
                id=r["id"],
                account_slug=r["account_slug"],
                detected_at=_parse_dt(r["detected_at"]),
                signal_type=SignalType(r["signal_type"]),
                headline=r["headline"],
                source_url=r["source_url"],
                relevance=Relevance(r["relevance"]),
                notes=r["notes"],
            )
            for r in rows
        ]

    # ----- Hypothesis ---------------------------------------------------

    def upsert_hypothesis(self, h: Hypothesis) -> Hypothesis:
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO hypothesis (account_slug, headline, falsification_test,
                    outcome_metric, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    h.account_slug,
                    h.headline,
                    h.falsification_test,
                    h.outcome_metric.value,
                    h.status.value,
                    _iso(h.created_at),
                ),
            )
            h.id = cur.lastrowid
        return h

    def list_hypotheses(self, account_slug: str) -> list[Hypothesis]:
        from sam.models.enums import HypothesisStatus, OutcomeMetric

        with self.db.cursor() as cur:
            rows = cur.execute(
                "SELECT * FROM hypothesis WHERE account_slug = ? ORDER BY created_at DESC",
                (account_slug,),
            ).fetchall()
        return [
            Hypothesis(
                id=r["id"],
                account_slug=r["account_slug"],
                headline=r["headline"],
                falsification_test=r["falsification_test"],
                outcome_metric=OutcomeMetric(r["outcome_metric"]),
                status=HypothesisStatus(r["status"]),
                created_at=_parse_dt(r["created_at"]),
            )
            for r in rows
        ]

    # ----- Qualification ------------------------------------------------

    def upsert_qualification(self, q: Qualification) -> Qualification:
        q.updated_at = datetime.utcnow()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO qualification (account_slug, metrics, economic_buyer_id,
                    decision_criteria, decision_process, paper_process, implied_pain,
                    champion_id, competition, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_slug) DO UPDATE SET
                    metrics=excluded.metrics,
                    economic_buyer_id=excluded.economic_buyer_id,
                    decision_criteria=excluded.decision_criteria,
                    decision_process=excluded.decision_process,
                    paper_process=excluded.paper_process,
                    implied_pain=excluded.implied_pain,
                    champion_id=excluded.champion_id,
                    competition=excluded.competition,
                    updated_at=excluded.updated_at
                """,
                (
                    q.account_slug,
                    q.metrics,
                    q.economic_buyer_id,
                    q.decision_criteria,
                    q.decision_process,
                    q.paper_process,
                    q.implied_pain,
                    q.champion_id,
                    q.competition,
                    _iso(q.updated_at),
                ),
            )
        return q

    def get_qualification(self, account_slug: str) -> Qualification | None:
        with self.db.cursor() as cur:
            row = cur.execute(
                "SELECT * FROM qualification WHERE account_slug = ?",
                (account_slug,),
            ).fetchone()
        if not row:
            return None
        return Qualification(
            account_slug=row["account_slug"],
            metrics=row["metrics"],
            economic_buyer_id=row["economic_buyer_id"],
            decision_criteria=row["decision_criteria"],
            decision_process=row["decision_process"],
            paper_process=row["paper_process"],
            implied_pain=row["implied_pain"],
            champion_id=row["champion_id"],
            competition=row["competition"],
            updated_at=_parse_dt(row["updated_at"]),
        )

    # ----- Meeting ------------------------------------------------------

    def add_meeting(self, m: Meeting) -> Meeting:
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO meeting (account_slug, stakeholder_ids, scheduled_at,
                    meeting_type, status, outcome, next_step)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    m.account_slug,
                    _json_dump(m.stakeholder_ids),
                    _iso(m.scheduled_at),
                    m.meeting_type.value,
                    m.status.value,
                    m.outcome,
                    m.next_step,
                ),
            )
            m.id = cur.lastrowid
        return m

    # ----- WarmRoute ----------------------------------------------------

    def add_warm_route(self, w: WarmRoute) -> WarmRoute:
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO warm_route (target_stakeholder_id, via, via_type,
                    status, notes, requested_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    w.target_stakeholder_id,
                    w.via,
                    w.via_type.value,
                    w.status.value,
                    w.notes,
                    _iso(w.requested_at),
                ),
            )
            w.id = cur.lastrowid
        return w

    # ----- Persona ------------------------------------------------------

    def upsert_persona(self, p: Persona) -> Persona:
        p.updated_at = datetime.utcnow()
        with self.db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO persona (id, name, role, company, territory, manager,
                    pod, methodology, first_touch_style, partner_channels,
                    working_style, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name, role=excluded.role,
                    company=excluded.company, territory=excluded.territory,
                    manager=excluded.manager, pod=excluded.pod,
                    methodology=excluded.methodology,
                    first_touch_style=excluded.first_touch_style,
                    partner_channels=excluded.partner_channels,
                    working_style=excluded.working_style,
                    updated_at=excluded.updated_at
                """,
                (
                    p.name,
                    p.role,
                    p.company,
                    p.territory,
                    p.manager,
                    _json_dump(p.pod),
                    p.methodology,
                    p.first_touch_style,
                    _json_dump(p.partner_channels),
                    p.working_style,
                    _iso(p.updated_at),
                ),
            )
        return p

    def get_persona(self) -> Persona | None:
        with self.db.cursor() as cur:
            row = cur.execute("SELECT * FROM persona WHERE id = 1").fetchone()
        if not row:
            return None
        return Persona(
            name=row["name"],
            role=row["role"],
            company=row["company"],
            territory=row["territory"],
            manager=row["manager"],
            pod=_json_load(row["pod"], {}),
            methodology=row["methodology"],
            first_touch_style=row["first_touch_style"],
            partner_channels=_json_load(row["partner_channels"], []),
            working_style=row["working_style"],
            updated_at=_parse_dt(row["updated_at"]),
        )

    # ----- Search -------------------------------------------------------

    def search_text(self, query: str) -> list[dict[str, Any]]:
        """Naive LIKE search across the text-y fields. v0.2 will add vector + BM25."""
        like = f"%{query}%"
        results: list[dict[str, Any]] = []
        with self.db.cursor() as cur:
            for sql, kind in [
                ("SELECT slug, name FROM account WHERE name LIKE ? OR vertical LIKE ?", "account"),
                ("SELECT id, name, account_slug FROM stakeholder WHERE name LIKE ? OR title LIKE ? OR notes LIKE ?", "stakeholder"),
                ("SELECT id, account_slug, headline FROM signal WHERE headline LIKE ? OR notes LIKE ?", "signal"),
                ("SELECT id, account_slug, headline FROM hypothesis WHERE headline LIKE ? OR falsification_test LIKE ?", "hypothesis"),
                ("SELECT id, thread_id, body FROM touch WHERE body LIKE ?", "touch"),
            ]:
                params = [like] * sql.count("?")
                for row in cur.execute(sql, params).fetchall():
                    results.append({"kind": kind, **dict(row)})
        return results
