"""SQLite connection management and schema initialisation.

The database is a single file at ``.sam/sam.db`` (by default). It mirrors
what's in markdown — never the canonical store. If you delete sam.db,
``sam reindex`` rebuilds it from the markdown files.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_DIR = ".sam"
DEFAULT_DB_NAME = "sam.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS account (
    slug          TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    tier          INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 3),
    vertical      TEXT,
    hq            TEXT,
    parent        TEXT,
    ownership     TEXT,
    headcount     INTEGER,
    revenue_band  TEXT,
    paused        INTEGER NOT NULL DEFAULT 0,
    paused_reason TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_account_tier ON account(tier);
CREATE INDEX IF NOT EXISTS idx_account_vertical ON account(vertical);

CREATE TABLE IF NOT EXISTS stakeholder (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_slug    TEXT NOT NULL REFERENCES account(slug) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    title           TEXT NOT NULL,
    email           TEXT,
    linkedin_url    TEXT,
    meddpicc_role   TEXT NOT NULL DEFAULT 'Unknown',
    tenure_months   INTEGER,
    prior_employers TEXT,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_stakeholder_account ON stakeholder(account_slug);
CREATE INDEX IF NOT EXISTS idx_stakeholder_role    ON stakeholder(meddpicc_role);

CREATE TABLE IF NOT EXISTS outreach_thread (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stakeholder_id  INTEGER NOT NULL REFERENCES stakeholder(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Drafted',
    opened_at       TEXT,
    last_touch_at   TEXT,
    next_review_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_thread_stakeholder ON outreach_thread(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_thread_status      ON outreach_thread(status);

CREATE TABLE IF NOT EXISTS touch (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id  INTEGER NOT NULL REFERENCES outreach_thread(id) ON DELETE CASCADE,
    direction  TEXT NOT NULL,
    sent_at    TEXT NOT NULL,
    body       TEXT NOT NULL,
    outcome    TEXT
);

CREATE INDEX IF NOT EXISTS idx_touch_thread ON touch(thread_id);
CREATE INDEX IF NOT EXISTS idx_touch_sent   ON touch(sent_at);

CREATE TABLE IF NOT EXISTS meeting (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    account_slug     TEXT NOT NULL REFERENCES account(slug) ON DELETE CASCADE,
    stakeholder_ids  TEXT,
    scheduled_at     TEXT NOT NULL,
    meeting_type     TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Scheduled',
    outcome          TEXT,
    next_step        TEXT
);

CREATE INDEX IF NOT EXISTS idx_meeting_account ON meeting(account_slug);
CREATE INDEX IF NOT EXISTS idx_meeting_when    ON meeting(scheduled_at);

CREATE TABLE IF NOT EXISTS signal (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    account_slug  TEXT NOT NULL REFERENCES account(slug) ON DELETE CASCADE,
    detected_at   TEXT NOT NULL,
    signal_type   TEXT NOT NULL,
    headline      TEXT NOT NULL,
    source_url    TEXT,
    relevance     TEXT NOT NULL DEFAULT 'Medium',
    notes         TEXT
);

CREATE INDEX IF NOT EXISTS idx_signal_account ON signal(account_slug);
CREATE INDEX IF NOT EXISTS idx_signal_type    ON signal(signal_type);

CREATE TABLE IF NOT EXISTS hypothesis (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    account_slug        TEXT NOT NULL REFERENCES account(slug) ON DELETE CASCADE,
    headline            TEXT NOT NULL,
    falsification_test  TEXT NOT NULL,
    outcome_metric      TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'Active',
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hypothesis_account ON hypothesis(account_slug);

CREATE TABLE IF NOT EXISTS qualification (
    account_slug       TEXT PRIMARY KEY REFERENCES account(slug) ON DELETE CASCADE,
    metrics            TEXT,
    economic_buyer_id  INTEGER REFERENCES stakeholder(id),
    decision_criteria  TEXT,
    decision_process   TEXT,
    paper_process      TEXT,
    implied_pain       TEXT,
    champion_id        INTEGER REFERENCES stakeholder(id),
    competition        TEXT,
    updated_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warm_route (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    target_stakeholder_id  INTEGER NOT NULL REFERENCES stakeholder(id) ON DELETE CASCADE,
    via                    TEXT NOT NULL,
    via_type               TEXT NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'Identified',
    notes                  TEXT,
    requested_at           TEXT
);

CREATE INDEX IF NOT EXISTS idx_route_target ON warm_route(target_stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_route_status ON warm_route(status);

CREATE TABLE IF NOT EXISTS persona (
    id                 INTEGER PRIMARY KEY CHECK (id = 1),
    name               TEXT NOT NULL,
    role               TEXT NOT NULL,
    company            TEXT NOT NULL,
    territory          TEXT NOT NULL,
    manager            TEXT,
    pod                TEXT,
    methodology        TEXT NOT NULL,
    first_touch_style  TEXT NOT NULL,
    partner_channels   TEXT,
    working_style      TEXT NOT NULL,
    updated_at         TEXT NOT NULL
);
"""


class Database:
    """Thin wrapper around sqlite3 with foreign-key enforcement."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    def close(self) -> None:
        self._conn.close()


def get_db(root: Path | str | None = None) -> Database:
    """Return a Database located under <root>/.sam/sam.db.

    If `root` is None, uses the current working directory.
    """
    root_path = Path(root) if root else Path.cwd()
    db_path = root_path / DEFAULT_DB_DIR / DEFAULT_DB_NAME
    return Database(db_path)
