"""Markdown templates for L2 scenes and L3 persona files."""

from __future__ import annotations

from datetime import date

from sam.models import Persona

L2_SCENE_TEMPLATE = """# L2 Scene — {name}
_Updated: {updated}_

## Key Stakeholder
- {key_stakeholder}

## Strategic Context
- {strategic_context}

## Sales Motion
- {sales_motion}

## Entry Point
- {entry_point}

## Last Touch
- {last_touch}

## Top Blocker
- {top_blocker}

## Next Action
- {next_action}
"""


L1_ATOMS_HEADER = """# L1 Atoms — {name}
_Auto-populated. Do not edit manually._

"""


def render_scene(
    *,
    name: str,
    key_stakeholder: str = "Unknown — research needed",
    strategic_context: str = "Unknown — research needed",
    sales_motion: str = "Unknown — research needed",
    entry_point: str = "Unknown — research needed",
    last_touch: str = "None yet",
    top_blocker: str = "Unknown — research needed",
    next_action: str = "Unknown — research needed",
    updated: str | None = None,
) -> str:
    """Render an L2 scene as markdown.

    Any field left blank gets the explicit "Unknown — research needed"
    sentinel, which is more useful than a blank line because it tells the
    reader that the gap is known but not yet filled.
    """
    return L2_SCENE_TEMPLATE.format(
        name=name,
        updated=updated or date.today().isoformat(),
        key_stakeholder=key_stakeholder,
        strategic_context=strategic_context,
        sales_motion=sales_motion,
        entry_point=entry_point,
        last_touch=last_touch,
        top_blocker=top_blocker,
        next_action=next_action,
    )


def render_persona(p: Persona) -> str:
    """Render the persona singleton as markdown."""
    pod = "\n".join(f"- **{role}:** {name}" for role, name in p.pod.items()) or "- _Not set._"
    partners = "\n".join(f"- {c}" for c in p.partner_channels) or "- _Not set._"
    return (
        f"# L3 Persona — {p.name}\n"
        f"_Updated: {p.updated_at.date().isoformat()}_\n\n"
        f"## Identity\n"
        f"- **Name:** {p.name}\n"
        f"- **Role:** {p.role}\n"
        f"- **Company:** {p.company}\n"
        f"- **Territory:** {p.territory}\n"
        f"- **Manager:** {p.manager or '_Not set._'}\n\n"
        f"## Pod\n{pod}\n\n"
        f"## Methodology + first-touch style\n"
        f"- **Methodology:** {p.methodology}\n"
        f"- **First-touch style:** {p.first_touch_style}\n\n"
        f"## Partner channels\n{partners}\n\n"
        f"## Working style + comms preferences\n"
        f"{p.working_style}\n"
    )
