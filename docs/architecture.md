# SAM Architecture

## Design principles

1. **Files are the source of truth.** Markdown on disk, diff in git, read on a phone. SQLite is an index, never the canonical store.
2. **Sales-native vocabulary.** Entities and fields use the language an AE uses in a real conversation — `commercial_trigger`, `entry_point`, `top_blocker`, `next_action`, `meddpicc_role` — not generic `Session` / `Observation`.
3. **Append-only at L1.** Atomic facts never get rewritten; they accumulate. Compression happens upward (L1 → L2 → L3), not in place.
4. **Pluggable retrieval.** v0.1 ships markdown grep + SQLite filters. v0.2 will add vector + BM25 + RRF without touching the schema or the file layout.
5. **Open-source by default.** Nothing in the core depends on a proprietary CRM, a specific LLM, or a hosted vector DB.

## The 4-tier memory model

Ported from [agentmemory](https://github.com/rohitg00/agentmemory)'s working/episodic/semantic/procedural model, but renamed for sales:

| Tier | Role | Granularity | Update rhythm | Lifetime |
|---|---|---|---|---|
| **L0 Raw** | Unprocessed source material — email drafts, call notes, transcripts, CRM exports | Whole document | Per event | Until compressed / archived |
| **L1 Atoms** | Dated facts, one line each, ≤20 words | Single fact | Append-only on event | Permanent |
| **L2 Scenes** | Per-account narrative — stakeholder, context, motion, entry point, last touch, blocker, next action | Whole-account view | Refreshed weekly or on material change | Living document |
| **L3 Persona** | Who the AE is — role, pod, methodology, territory, partner channels, working style | Single document | Refreshed on personal change | Living document |

Why these names instead of agentmemory's:
- **L0/L1/L2/L3** maps cleanly to "raw → atomic → scenic → personal" without dev jargon.
- AEs already think in atomic facts (the bullet on the post-call note) and scenes (the account brief).
- The numeric tiering makes load order obvious: L3 always loads first (cheapest, most stable), then L2 for the account in focus, then L1 for recency, then L0 only if needed.

## The entity graph

```
                     ┌──────────────┐
                     │   Persona    │  ← L3
                     └──────┬───────┘
                            │ owns
                            ▼
                     ┌──────────────┐    ┌────────────┐
                     │   Account    │◄───┤  Signal    │  commercial trigger
                     │  (slug, tier,│    │ (dated)    │  (earnings, M&A, hire)
                     │   vertical)  │    └────────────┘
                     └──┬─────┬─────┘
                        │     │
            ┌───────────┘     └─────────┐
            │                            │
            ▼                            ▼
     ┌──────────────┐          ┌────────────────────┐
     │ Stakeholder  │          │   OutreachThread   │
     │  (name,role, │◄─────────┤  (channel, status, │
     │  meddpicc)   │ contact  │   stakeholder)     │
     └──────┬───────┘          └─────────┬──────────┘
            │                            │
            │                            ▼
            │                    ┌────────────────┐
            │                    │     Touch      │
            │                    │ (one message,  │
            │                    │  direction,    │
            │                    │  date, body)   │
            │                    └────────────────┘
            │
            ├────────────► ┌──────────────┐
            │              │   Meeting    │
            │              │ (date, type, │
            │              │  outcome)    │
            │              └──────────────┘
            │
            └────────────► ┌────────────────┐    ┌────────────────┐
                           │  Qualification │    │   Hypothesis   │
                           │   (MEDDPICC,   │    │ (one-sentence  │
                           │    per acct)   │    │  framing +     │
                           └────────────────┘    │  falsification)│
                                                 └────────────────┘

                          ┌──────────────┐
                          │  WarmRoute   │  ← partner / internal / mutual contact
                          │  (channel,   │     into a specific stakeholder
                          │   status)    │
                          └──────────────┘
```

## Write paths

Every entity write follows the same pattern:

1. **Validate via pydantic.** Any external input — CLI arg, MCP call, hook event — passes through a pydantic model.
2. **Persist to SQLite.** `sam.storage.repository` provides typed CRUD per model.
3. **Mirror to markdown (where applicable).** Atoms append a line to `memory/L1_atoms/<slug>_atoms.md`. Scene updates regenerate `memory/L2_scenes/<slug>.md`. Persona writes regenerate `memory/L3_persona/<persona>.md`. L0 raw drops the source file under `memory/L0_raw/<slug>/<date>.md` (or `.txt` / `.eml`).

The markdown stays human-readable. The SQLite copy enables fast filtered queries (e.g. "all stakeholders with `meddpicc_role = Champion` and `account.tier = 1` and `account.vertical = Telco`").

## Read paths

v0.1 read paths in order of cost:

1. **`sam persona`** → load the single L3 markdown file. ~0.5KB.
2. **`sam scene <slug>`** → load one L2 markdown file. ~1–2KB.
3. **`sam atoms <slug>`** → load one L1 atoms file. ~2–5KB.
4. **`sam search "<term>"`** → SQLite full-text search across entities + grep across markdown.

v0.2 will replace step 4 with hybrid BM25 + vector + RRF retrieval.

## Why SQLite + markdown, not just one or the other?

| | SQLite only | Markdown only | Both (SAM) |
|---|---|---|---|
| Diffable in git | ❌ binary blob | ✅ readable diff | ✅ markdown diffs |
| Fast filtered query | ✅ indexed | ❌ grep is O(n) | ✅ via SQLite |
| Human-editable on a phone | ❌ | ✅ | ✅ |
| Survives if SQLite breaks | ❌ data loss | ✅ files remain | ✅ files are canonical |
| Schema enforcement | partial | ❌ | ✅ via pydantic |

The markdown is always rebuildable from SQLite, and SQLite is always rebuildable from the markdown via `sam reindex`. Neither side is irreplaceable; both add value.

## What's deliberately out of scope for v0.1

- **No vector embeddings.** Coming in v0.2.
- **No MCP server.** Coming in v0.3. The schemas are already MCP-friendly (pydantic JSON schemas).
- **No capture hooks.** Coming in v0.4. The CLI is the only entry point in v0.1.
- **No LLM compression.** Coming in v0.5. All compression in v0.1 is manual via `sam scene update`.
- **No knowledge-graph traversal.** Coming in v1.0. Foreign keys are in place; the traversal layer isn't.

This keeps v0.1 small enough that you can read the whole package in an afternoon and judge whether the shape works for you before more pieces land on top.
