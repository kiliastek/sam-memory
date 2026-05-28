"""Read and write the L0/L1/L2/L3 markdown layers."""

from __future__ import annotations

from datetime import date as _date
from pathlib import Path

from sam.memory.templates import L1_ATOMS_HEADER, render_persona, render_scene
from sam.models import Persona

MEMORY_SUBDIRS = ("L0_raw", "L1_atoms", "L2_scenes", "L3_persona")


def init_memory_dirs(root: Path) -> Path:
    """Create the .sam/memory/L*/ tree under `root` if missing.

    Returns the memory root path so the caller can stash it.
    """
    mem = root / ".sam" / "memory"
    for sub in MEMORY_SUBDIRS:
        (mem / sub).mkdir(parents=True, exist_ok=True)
    return mem


def _memory_root(root: Path) -> Path:
    return root / ".sam" / "memory"


# ----- L1 atoms -------------------------------------------------------------

def append_atom(root: Path, slug: str, account_name: str, fact: str, *, when: str | None = None) -> Path:
    """Append a single dated atom to memory/L1_atoms/<slug>_atoms.md.

    `when` should be an ISO date string ('YYYY-MM-DD') or 'date-unknown'.
    `fact` is enforced to be a single line and ≤ ~140 chars (soft cap —
    we don't truncate, we just warn). The 20-word target is a guideline
    for the writer, not a hard validator.
    """
    if when is None:
        when = _date.today().isoformat()
    line = f"- [{when}] {fact.strip().replace(chr(10), ' ')}\n"

    path = _memory_root(root) / "L1_atoms" / f"{slug}_atoms.md"
    if not path.exists():
        path.write_text(L1_ATOMS_HEADER.format(name=account_name))
    with path.open("a") as f:
        f.write(line)
    return path


def read_atoms(root: Path, slug: str) -> str:
    path = _memory_root(root) / "L1_atoms" / f"{slug}_atoms.md"
    if not path.exists():
        return ""
    return path.read_text()


# ----- L2 scenes ------------------------------------------------------------

def write_scene(
    root: Path,
    slug: str,
    *,
    name: str,
    **fields: str,
) -> Path:
    """Write a fresh L2 scene markdown file. Overwrites if it exists."""
    path = _memory_root(root) / "L2_scenes" / f"{slug}.md"
    path.write_text(render_scene(name=name, **fields))
    return path


def read_scene(root: Path, slug: str) -> str:
    path = _memory_root(root) / "L2_scenes" / f"{slug}.md"
    if not path.exists():
        return ""
    return path.read_text()


# ----- L3 persona -----------------------------------------------------------

def write_persona(root: Path, persona: Persona) -> Path:
    """Render the persona to markdown under L3."""
    safe_name = persona.name.lower().replace(" ", "_")
    path = _memory_root(root) / "L3_persona" / f"{safe_name}.md"
    path.write_text(render_persona(persona))
    return path


def read_persona(root: Path) -> str:
    """Read the first persona file found in L3.

    SAM v0.1 assumes a single persona per memory store. If multiple files
    are present, the first one alphabetically is returned and the caller
    should log a warning.
    """
    persona_dir = _memory_root(root) / "L3_persona"
    if not persona_dir.exists():
        return ""
    files = sorted(p for p in persona_dir.glob("*.md"))
    return files[0].read_text() if files else ""
