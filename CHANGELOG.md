# Changelog

All notable changes to SAM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-05-28

### Added
- Initial release.
- Pydantic v2 schemas for the sales-native entity graph: `Account`, `Stakeholder`, `OutreachThread`, `Touch`, `Meeting`, `Signal`, `Hypothesis`, `Qualification` (MEDDPICC), `WarmRoute`.
- SQLite-backed storage layer (`sam.storage`) with repository-pattern CRUD on every entity. No external DB dependencies.
- 4-tier memory layer (`sam.memory`): L0 raw / L1 atoms / L2 scenes / L3 persona. Markdown files on disk, indexed by SQLite.
- Typer CLI (`sam`) with subcommands for `init`, `account`, `stakeholder`, `touch`, `signal`, `meeting`, `qualify`, `scene`, `persona`, `search`.
- Markdown templates for L2 scenes + L3 persona.
- Example fictional dataset (Acme Corp) under `examples/`.
- Pytest smoke tests under `tests/`.
- Architecture, schemas, and quickstart documentation.

### Roadmap
- v0.2 — vector embeddings + BM25 + RRF fusion retrieval.
- v0.3 — MCP server.
- v0.4 — capture hooks (Outlook, Gmail, calendar, news).
- v0.5 — LLM compression for L0 → L1 → L2 auto-extraction.
- v1.0 — knowledge graph traversal.
