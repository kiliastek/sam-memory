"""Memory layer (markdown read/write) tests."""

from __future__ import annotations

from pathlib import Path

from sam.memory import (
    append_atom,
    init_memory_dirs,
    read_atoms,
    read_persona,
    read_scene,
    write_persona,
    write_scene,
)
from sam.models import Persona


def test_init_creates_layers(tmp_path: Path) -> None:
    mem = init_memory_dirs(tmp_path)
    for sub in ("L0_raw", "L1_atoms", "L2_scenes", "L3_persona"):
        assert (mem / sub).is_dir()


def test_append_atom_writes_dated_line(tmp_path: Path) -> None:
    init_memory_dirs(tmp_path)
    append_atom(tmp_path, "acme", "Acme Corp", "Account opened.")
    append_atom(tmp_path, "acme", "Acme Corp", "Hypothesis set.", when="2026-05-28")
    text = read_atoms(tmp_path, "acme")
    assert "# L1 Atoms — Acme Corp" in text
    assert "- [2026-05-28] Hypothesis set." in text
    assert "Account opened." in text


def test_append_atom_newline_collapsed(tmp_path: Path) -> None:
    init_memory_dirs(tmp_path)
    append_atom(tmp_path, "acme", "Acme", "Multi\nline\nfact")
    text = read_atoms(tmp_path, "acme")
    # Newlines inside the fact should be collapsed to spaces so each atom stays one line.
    assert "Multi line fact" in text


def test_write_and_read_scene(tmp_path: Path) -> None:
    init_memory_dirs(tmp_path)
    write_scene(
        tmp_path,
        "acme",
        name="Acme Corp",
        key_stakeholder="Jane Doe, CTO",
        strategic_context="Post-merger platform consolidation.",
        sales_motion="Workflow spine.",
        entry_point="Warm intro via alumni.",
        last_touch="2026-05-15 connected on LinkedIn.",
        top_blocker="BMC incumbent.",
        next_action="Send Calendly link.",
    )
    text = read_scene(tmp_path, "acme")
    assert "# L2 Scene — Acme Corp" in text
    assert "Jane Doe, CTO" in text
    assert "Post-merger platform consolidation." in text


def test_scene_defaults_use_research_needed(tmp_path: Path) -> None:
    init_memory_dirs(tmp_path)
    write_scene(tmp_path, "globex", name="Globex Industries")
    text = read_scene(tmp_path, "globex")
    assert "Unknown — research needed" in text
    assert "None yet" in text


def test_persona_roundtrip(tmp_path: Path) -> None:
    init_memory_dirs(tmp_path)
    p = Persona(
        name="Jane Smith",
        role="AE",
        company="ExampleCo",
        territory="EMEA-1",
        methodology="MEDDPICC",
        first_touch_style="LinkedIn ≤300 chars",
        working_style="bottom-line first",
        pod={"ADR": "Sam"},
        partner_channels=["Globex Capital"],
    )
    write_persona(tmp_path, p)
    text = read_persona(tmp_path)
    assert "Jane Smith" in text
    assert "**Territory:** EMEA-1" in text
    assert "Sam" in text  # pod entry
    assert "Globex Capital" in text  # partner entry
