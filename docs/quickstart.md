# SAM Quickstart

A 10-minute tour of SAM v0.1 using the fictional Acme Corp example dataset.

## Install

```bash
git clone https://github.com/<you>/sam-memory.git
cd sam-memory
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Verify:

```bash
sam --version
# sam, version 0.1.0
```

## Initialise a memory store

In whatever directory you want to keep your memory (probably a separate repo from sam-memory itself):

```bash
cd ~/my-territory
sam init
```

This creates:

```
.sam/
├── sam.db                  # SQLite index
└── memory/
    ├── L0_raw/
    ├── L1_atoms/
    ├── L2_scenes/
    └── L3_persona/
```

`.sam/` is git-ignored by default — your memory store is local. To version-control it, remove the entry from `.gitignore` and add `.sam/` to your repo (markdown diffs cleanly).

## Set your persona

```bash
sam persona set \
  --name "Jane Smith" \
  --role "Enterprise Account Executive" \
  --company "ExampleCo" \
  --territory "EMEA-NORTH-1" \
  --manager "Alex Rivera" \
  --methodology "MEDDPICC" \
  --first-touch-style "LinkedIn under 300 chars, peer-level, no product mention" \
  --working-style "Bottom-line first, then rationale; commercially grounded"
```

Read back:

```bash
sam persona
```

## Add an account

```bash
sam account add \
  --slug acme-corp \
  --name "Acme Corp" \
  --tier 1 \
  --vertical "Telco" \
  --hq "London, UK" \
  --ownership "Public — LSE: ACME" \
  --headcount 4500 \
  --revenue-band "$500M-$5B"
```

List accounts:

```bash
sam account list
```

## Add a stakeholder

```bash
sam stakeholder add \
  --account acme-corp \
  --name "Jane Doe" \
  --title "Chief Technology Officer" \
  --email "jane.doe@acme.example.com" \
  --linkedin "https://www.linkedin.com/in/jane-doe-example" \
  --meddpicc Champion \
  --tenure-months 14 \
  --prior-employers "Globex,Initech"
```

List stakeholders for an account:

```bash
sam stakeholder list --account acme-corp
```

## Record a signal

```bash
sam signal add \
  --account acme-corp \
  --type LeadershipMove \
  --headline "New CFO Jordan Lee appointed (ex-Globex)" \
  --source "https://example.com/press/jordan-lee" \
  --relevance High
```

## Log an outreach touch

```bash
sam touch log \
  --account acme-corp \
  --stakeholder "Jane Doe" \
  --channel LinkedIn \
  --direction Outbound \
  --body "Hi Jane — saw your interview on Q3 platform consolidation. Would love to compare notes peer-level. No sales agenda, 15 mins." \
  --outcome connected
```

Subsequent touches in the same thread:

```bash
sam touch log \
  --account acme-corp \
  --stakeholder "Jane Doe" \
  --channel LinkedIn \
  --direction Inbound \
  --body "Sure, send a Calendly link" \
  --outcome replied
```

## Schedule a meeting

```bash
sam meeting add \
  --account acme-corp \
  --stakeholder "Jane Doe" \
  --scheduled "2026-06-10T10:30:00" \
  --type Discovery \
  --status Scheduled
```

After the meeting:

```bash
sam meeting complete <meeting_id> \
  --outcome "Confirmed Jane is the Champion. Q3 platform consolidation real. Introducing me to CIO." \
  --next-step "CIO intro this week; pre-call brief Tuesday."
```

## Set the commercial hypothesis

```bash
sam hypothesis set \
  --account acme-corp \
  --headline "Acme's Q3 platform consolidation programme creates demand for a workflow spine that lets the post-merger ops function as one." \
  --falsification "If Jane says each subsidiary keeps its own back-office tooling, hypothesis is dead." \
  --outcome OperationalResilience
```

## Update MEDDPICC

```bash
sam qualify update \
  --account acme-corp \
  --metrics "20% reduction in incident MTTR by FY27" \
  --champion "Jane Doe" \
  --implied-pain "Three-acquisition operating-platform sprawl; manual triage burning ops headcount." \
  --competition "ServiceNow (us) vs BMC (incumbent); also evaluating Atlassian JSM."
```

Read the qualification state:

```bash
sam qualify show acme-corp
```

## Add a warm route

```bash
sam route add \
  --target "Jane Doe" \
  --account acme-corp \
  --via "Sam Patel (ex-Globex colleague)" \
  --type Alumni \
  --status Requested \
  --notes "Sam worked with Jane at Globex 2019-2022. Asked Sam for warm intro 2026-05-25."
```

## Read the account scene

This composes the latest L2 view from everything you've logged:

```bash
sam scene acme-corp
```

You can also write it to disk:

```bash
sam scene acme-corp --write
# Writes memory/L2_scenes/acme-corp.md
```

## Search across everything

```bash
sam search "platform consolidation"
```

v0.1 returns matches in scenes, atoms, hypotheses, and touch bodies. v0.2 will add semantic search.

## JSON output

Every read command supports `--format json` for piping into other tools:

```bash
sam account list --format json | jq '.[] | select(.tier == 1)'
sam stakeholder list --account acme-corp --format json
```

## Atoms — read

```bash
sam atoms acme-corp
```

Atoms are auto-populated as you log signals, touches, meetings, hypotheses, etc. You shouldn't need to edit `memory/L1_atoms/acme-corp_atoms.md` manually — but it's plain markdown if you want to.

## Bulk import the example dataset

```bash
sam import examples/
```

This loads the fictional Acme Corp + Globex + Initech accounts with full state. Useful for kicking the tyres without typing 50 CLI calls.

## What's next

- v0.2 will add vector search + BM25 retrieval to replace the grep-based `sam search`.
- v0.3 will expose all of the above as MCP tools so Claude / Cursor / Codex can call SAM directly.
- v0.4 will add capture hooks so logging happens automatically from Outlook, Gmail, and calendar events.

In the meantime: log religiously, write hypotheses you can falsify, and treat the L2 scene as the artefact that survives every conversation.
