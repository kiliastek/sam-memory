# SAM Schemas

Every entity in SAM is a pydantic v2 model. The model is the contract: validation, JSON serialisation, and SQLite mapping all flow from it.

## Core entities

### Account

The unit of pursuit. One per company in the territory.

| Field | Type | Required | Notes |
|---|---|---|---|
| `slug` | str | yes | URL-safe identifier (e.g. `acme-corp`). Primary key. |
| `name` | str | yes | Human-readable name. |
| `tier` | int (1–3) | yes | Pursuit tier. 1 = active outreach, 2 = qualification, 3 = watch. |
| `vertical` | str | no | TMT, FinServ, HealthSciences, etc. |
| `hq` | str | no | HQ city / country. |
| `parent` | str | no | Parent company slug if subsidiary. |
| `ownership` | str | no | Public, PE-backed (with sponsor name), family-owned, etc. |
| `headcount` | int | no | Latest known headcount. |
| `revenue_band` | str | no | "<$50M", "$50M-$500M", "$500M-$5B", ">$5B". |
| `paused` | bool | default False | True if temporarily out of pursuit. |
| `paused_reason` | str | no | Free text — required if `paused=True`. |
| `created_at` | datetime | auto | Set on insert. |
| `updated_at` | datetime | auto | Updated on every change. |

### Stakeholder

A person at an Account. Contacts.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `account_slug` | str | yes | FK to `Account.slug`. |
| `name` | str | yes | Full name. |
| `title` | str | yes | Job title. |
| `email` | str | no | Verified email if available. |
| `linkedin_url` | str | no | Public profile URL. |
| `meddpicc_role` | enum | no | `EconomicBuyer` / `Champion` / `Coach` / `Influencer` / `User` / `Blocker` / `Unknown`. |
| `tenure_months` | int | no | Months in current seat. |
| `prior_employers` | list[str] | no | Useful for warm-route lookups. |
| `notes` | str | no | Free text. |

### OutreachThread

A relationship channel with a specific stakeholder. A stakeholder can have multiple threads (LinkedIn + email + InMail).

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `stakeholder_id` | int | yes | FK to `Stakeholder.id`. |
| `channel` | enum | yes | `LinkedIn` / `Email` / `InMail` / `Phone` / `InPerson`. |
| `status` | enum | yes | `Drafted` / `Sent` / `Connected` / `Awaiting` / `Replied` / `Withdrawn` / `Bounced` / `Closed`. |
| `opened_at` | datetime | no | First touch in this channel. |
| `last_touch_at` | datetime | no | Most recent activity. |
| `next_review_at` | datetime | no | When to re-evaluate (e.g. day-14 follow-up). |

### Touch

A single message in an OutreachThread. Append-only.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `thread_id` | int | yes | FK to `OutreachThread.id`. |
| `direction` | enum | yes | `Outbound` / `Inbound`. |
| `sent_at` | datetime | yes | When the touch happened. |
| `body` | str | yes | The message text (or a summary if long). |
| `outcome` | str | no | Brief result tag — `delivered`, `bounced`, `connected`, `replied`, `meeting_booked`. |

### Meeting

A scheduled or completed conversation with one or more stakeholders.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `account_slug` | str | yes | FK to `Account.slug`. |
| `stakeholder_ids` | list[int] | yes | Attendees. |
| `scheduled_at` | datetime | yes | Meeting time. |
| `meeting_type` | enum | yes | `Discovery` / `Demo` / `Workshop` / `EBR` / `Closing` / `FollowUp`. |
| `status` | enum | yes | `Scheduled` / `Completed` / `NoShow` / `Cancelled`. |
| `outcome` | str | no | Filled post-meeting. Free text. |
| `next_step` | str | no | Filled post-meeting. |

### Signal

A dated commercial trigger about an Account — earnings, M&A, hire, RFP, leadership change.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `account_slug` | str | yes | FK to `Account.slug`. |
| `detected_at` | datetime | yes | When the signal landed in our world. |
| `signal_type` | enum | yes | `Earnings` / `Funding` / `MA` / `LeadershipMove` / `RFP` / `Layoffs` / `ProductLaunch` / `PressMention` / `RegulatoryAction` / `Other`. |
| `headline` | str | yes | Short description. |
| `source_url` | str | no | Primary source citation. |
| `relevance` | enum | yes | `High` / `Medium` / `Low`. |
| `notes` | str | no | Free text. |

### Hypothesis

The one-sentence commercial framing for why an Account is in pursuit, with a falsification test.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `account_slug` | str | yes | FK. One Hypothesis per Account is the common pattern; multiple allowed. |
| `headline` | str | yes | One-sentence framing. |
| `falsification_test` | str | yes | Specific public signal that would invalidate the hypothesis. |
| `outcome_metric` | enum | yes | `RevenueGrowth` / `CostReduction` / `OperationalResilience` / `TimeToMarket`. |
| `status` | enum | yes | `Active` / `Confirmed` / `Falsified` / `Stale`. |
| `created_at` | datetime | auto | Set on insert. |

### Qualification (MEDDPICC)

One row per Account capturing the eight MEDDPICC elements.

| Field | Type | Required | Notes |
|---|---|---|---|
| `account_slug` | str | yes | PK. One Qualification per Account. |
| `metrics` | str | no | What measurable outcome the buyer cares about. |
| `economic_buyer_id` | int | no | FK to `Stakeholder.id` once identified. |
| `decision_criteria` | str | no | How they'll choose. |
| `decision_process` | str | no | Approval chain. |
| `paper_process` | str | no | Legal / procurement / SLA path. |
| `implied_pain` | str | no | What hurts today. |
| `champion_id` | int | no | FK to `Stakeholder.id`. |
| `competition` | str | no | Incumbent + competing vendors. |
| `completeness_score` | int (0–100) | auto | Derived: % of fields populated. |
| `updated_at` | datetime | auto | Updated on every change. |

### WarmRoute

A path to a Stakeholder through a partner, internal colleague, mutual connection, or alumni link.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | int | auto | Primary key. |
| `target_stakeholder_id` | int | yes | The stakeholder you want to reach. |
| `via` | str | yes | The intermediary's name. |
| `via_type` | enum | yes | `Partner` / `Internal` / `Alumni` / `Mutual` / `Customer`. |
| `status` | enum | yes | `Identified` / `Requested` / `InProgress` / `Delivered` / `Declined`. |
| `notes` | str | no | Free text. |
| `requested_at` | datetime | no | When the intro was asked for. |

## Persona

Persona is a singleton (one per memory store). Stored as a markdown file under `memory/L3_persona/` and shadowed in SQLite.

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | str | yes | AE name. |
| `role` | str | yes | Job title. |
| `company` | str | yes | Employer. |
| `territory` | str | yes | Territory ID / scope. |
| `manager` | str | no | Direct manager. |
| `pod` | dict[str, str] | no | `{"ADR": "...", "SC": "...", ...}`. |
| `methodology` | str | yes | E.g. `MEDDPICC`. |
| `first_touch_style` | str | yes | E.g. "LinkedIn ≤300 chars, peer-level, no product mention". |
| `partner_channels` | list[str] | no | Active partner contacts. |
| `working_style` | str | yes | Brief comms preferences. |

## Memory layers (markdown)

### L0 Raw

Path: `memory/L0_raw/<account_slug>/<YYYY-MM-DD>-<source>.<ext>`

Format: any. Email exports as `.eml`, call notes as `.md`, transcripts as `.txt`.

### L1 Atoms

Path: `memory/L1_atoms/<slug>_atoms.md` (per account) and `memory/L1_atoms/_territory_atoms.md` (cross-cutting).

Format: append-only list, one line per atom:

```markdown
# L1 Atoms — <Account Name>
_Auto-populated. Do not edit manually._

- [YYYY-MM-DD] <concise fact, max 20 words>
- [YYYY-MM-DD] <concise fact>
- [date-unknown] <concise fact>
```

### L2 Scenes

Path: `memory/L2_scenes/<slug>.md`

Format: structured markdown — see `sam/memory/templates.py` for the canonical template.

```markdown
# L2 Scene — <Account Name>
_Updated: <YYYY-MM-DD>_

## Key Stakeholder
- Name, title, why they matter

## Strategic Context
- What is driving change at this account right now

## ServiceNow Motion
- Which product/workflow we are positioning and why
(Replace "ServiceNow" with your vendor of choice in the template.)

## Entry Point
- How we get in (partner, warm intro, direct outreach)

## Last Touch
- Date and outcome of most recent contact (or "None yet")

## Top Blocker
- Main obstacle to moving forward

## Next Action
- Single most important next step
```

### L3 Persona

Path: `memory/L3_persona/<persona_slug>.md`

Format: structured markdown — see `sam/memory/templates.py` for the canonical template.

## Sample JSON for every entity

See `docs/quickstart.md` for `sam <subcommand> --help` outputs and JSON examples produced by `--format json`.
