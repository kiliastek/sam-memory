"""Typer CLI for SAM v0.1.

NOTE: this module deliberately does NOT use `from __future__ import annotations`.
Typer introspects parameter annotations at runtime to build the click option
machinery, and PEP 604 union syntax (`Optional[str]`) requires Python 3.10+ at
runtime. We use ``Optional[X]`` here so the CLI works on 3.9.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

import typer
from rich.console import Console
from rich.table import Table

from sam import __version__
from sam.memory import (
    append_atom,
    init_memory_dirs,
    read_atoms,
    read_persona,
    read_scene,
    write_persona,
    write_scene,
)
from sam.models import (
    Account,
    Channel,
    Hypothesis,
    HypothesisStatus,
    MeddpiccRole,
    Meeting,
    MeetingStatus,
    MeetingType,
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

app = typer.Typer(
    help="SAM — Sales Agent Memory. Persistent, layered memory for AI sales agents.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
console = Console()


# ----- helpers --------------------------------------------------------------

def _repo() -> Repository:
    return Repository(get_db())


def _root() -> Path:
    return Path.cwd()


def _emit(obj: Any, fmt: str) -> None:
    if fmt == "json":
        if hasattr(obj, "model_dump"):
            data = obj.model_dump(mode="json")
        elif isinstance(obj, list) and obj and hasattr(obj[0], "model_dump"):
            data = [o.model_dump(mode="json") for o in obj]
        else:
            data = obj
        typer.echo(json.dumps(data, default=str, indent=2))
    else:
        console.print(obj)


# ----- top-level ------------------------------------------------------------

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", is_eager=True, help="Show the SAM version and exit."
    ),
) -> None:
    if version:
        typer.echo(f"sam {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def init() -> None:
    """Initialise a SAM memory store in the current directory."""
    root = _root()
    init_memory_dirs(root)
    _repo()  # forces DB creation
    console.print(f"[green]Initialised SAM memory store at[/green] {root}/.sam/")
    console.print("Next: [bold]sam persona set ...[/bold] then [bold]sam account add ...[/bold]")


# ----- account --------------------------------------------------------------

account_app = typer.Typer(help="Manage accounts.", no_args_is_help=True)
app.add_typer(account_app, name="account")


@account_app.command("add")
def account_add(
    slug: str = typer.Option(..., help="URL-safe identifier, e.g. acme-corp"),
    name: str = typer.Option(..., help="Account display name"),
    tier: int = typer.Option(..., min=1, max=3, help="1=active, 2=qualification, 3=watch"),
    vertical: Optional[str] = typer.Option(None),
    hq: Optional[str] = typer.Option(None),
    parent: Optional[str] = typer.Option(None),
    ownership: Optional[str] = typer.Option(None),
    headcount: Optional[int] = typer.Option(None),
    revenue_band: Optional[str] = typer.Option(None),
) -> None:
    """Add or update an account."""
    a = Account(
        slug=slug,
        name=name,
        tier=tier,
        vertical=vertical,
        hq=hq,
        parent=parent,
        ownership=ownership,
        headcount=headcount,
        revenue_band=revenue_band,
    )
    _repo().upsert_account(a)
    append_atom(_root(), slug, name, f"Account added at Tier {tier}.")
    console.print(f"[green]Saved account[/green] [bold]{slug}[/bold] ({name})")


@account_app.command("list")
def account_list(
    tier: Optional[int] = typer.Option(None, min=1, max=3),
    vertical: Optional[str] = typer.Option(None),
    format: str = typer.Option("table", "--format"),
) -> None:
    """List accounts."""
    accounts = _repo().list_accounts(tier=tier, vertical=vertical)
    if format == "json":
        _emit(accounts, "json")
        return
    table = Table(title="Accounts")
    table.add_column("Slug", style="cyan")
    table.add_column("Name")
    table.add_column("Tier", justify="right")
    table.add_column("Vertical")
    table.add_column("Paused")
    for a in accounts:
        table.add_row(a.slug, a.name, str(a.tier), a.vertical or "—", "yes" if a.paused else "no")
    console.print(table)


@account_app.command("show")
def account_show(slug: str, format: str = typer.Option("table", "--format")) -> None:
    """Show a single account."""
    a = _repo().get_account(slug)
    if not a:
        typer.echo(f"No account with slug {slug}", err=True)
        raise typer.Exit(1)
    _emit(a, format)


# ----- stakeholder ----------------------------------------------------------

stakeholder_app = typer.Typer(help="Manage stakeholders.", no_args_is_help=True)
app.add_typer(stakeholder_app, name="stakeholder")


@stakeholder_app.command("add")
def stakeholder_add(
    account: str = typer.Option(..., help="Account slug"),
    name: str = typer.Option(...),
    title: str = typer.Option(...),
    email: Optional[str] = typer.Option(None),
    linkedin: Optional[str] = typer.Option(None, "--linkedin"),
    meddpicc: MeddpiccRole = typer.Option(MeddpiccRole.UNKNOWN),
    tenure_months: Optional[int] = typer.Option(None),
    prior_employers: Optional[str] = typer.Option(
        None, help="Comma-separated list of prior employers"
    ),
    notes: Optional[str] = typer.Option(None),
) -> None:
    """Add a stakeholder to an account."""
    prior = [p.strip() for p in (prior_employers or "").split(",") if p.strip()]
    s = Stakeholder(
        account_slug=account,
        name=name,
        title=title,
        email=email,
        linkedin_url=linkedin,
        meddpicc_role=meddpicc,
        tenure_months=tenure_months,
        prior_employers=prior,
        notes=notes,
    )
    saved = _repo().add_stakeholder(s)
    acct = _repo().get_account(account)
    if acct:
        append_atom(_root(), account, acct.name, f"Stakeholder {name} ({title}) added; MEDDPICC role {meddpicc.value}.")
    console.print(f"[green]Added stakeholder[/green] [bold]{name}[/bold] (id={saved.id})")


@stakeholder_app.command("list")
def stakeholder_list(
    account: Optional[str] = typer.Option(None),
    format: str = typer.Option("table", "--format"),
) -> None:
    rows = _repo().list_stakeholders(account)
    if format == "json":
        _emit(rows, "json")
        return
    table = Table(title=f"Stakeholders{(' — ' + account) if account else ''}")
    table.add_column("ID", justify="right")
    table.add_column("Account")
    table.add_column("Name")
    table.add_column("Title")
    table.add_column("MEDDPICC")
    for s in rows:
        table.add_row(str(s.id), s.account_slug, s.name, s.title, s.meddpicc_role.value)
    console.print(table)


# ----- touch ----------------------------------------------------------------

touch_app = typer.Typer(help="Log outreach touches.", no_args_is_help=True)
app.add_typer(touch_app, name="touch")


@touch_app.command("log")
def touch_log(
    account: str = typer.Option(...),
    stakeholder: str = typer.Option(..., help="Stakeholder name (as stored)"),
    channel: Channel = typer.Option(...),
    direction: TouchDirection = typer.Option(...),
    body: str = typer.Option(..., help="Message body or summary"),
    outcome: Optional[str] = typer.Option(None),
) -> None:
    """Log a single message; opens a thread on first touch."""
    repo = _repo()
    sh = repo.find_stakeholder(account, stakeholder)
    if not sh:
        typer.echo(f"No stakeholder {stakeholder!r} on {account}", err=True)
        raise typer.Exit(1)
    # Find or open thread for this stakeholder + channel.
    threads = [
        t for t in [
            *(
                row for row in _list_threads_by_stakeholder(repo, sh.id) if row.channel == channel
            )
        ]
    ]
    if threads:
        thread = threads[0]
    else:
        thread = repo.open_thread(
            OutreachThread(stakeholder_id=sh.id, channel=channel, status=ThreadStatus.SENT)
        )
    touch = repo.log_touch(
        Touch(
            thread_id=thread.id,
            direction=direction,
            sent_at=datetime.utcnow(),
            body=body,
            outcome=outcome,
        )
    )
    acct = repo.get_account(account)
    append_atom(
        _root(),
        account,
        acct.name if acct else account,
        f"{direction.value} {channel.value} touch with {stakeholder}"
        + (f" — outcome: {outcome}." if outcome else "."),
    )
    console.print(
        f"[green]Logged touch[/green] id={touch.id} on thread {thread.id} ({channel.value}, {direction.value})"
    )


def _list_threads_by_stakeholder(repo: Repository, sid: int) -> list[OutreachThread]:
    with repo.db.cursor() as cur:
        rows = cur.execute(
            "SELECT * FROM outreach_thread WHERE stakeholder_id = ?", (sid,)
        ).fetchall()
    return [
        OutreachThread(
            id=r["id"],
            stakeholder_id=r["stakeholder_id"],
            channel=Channel(r["channel"]),
            status=ThreadStatus(r["status"]),
        )
        for r in rows
    ]


# ----- signal ---------------------------------------------------------------

signal_app = typer.Typer(help="Record commercial signals.", no_args_is_help=True)
app.add_typer(signal_app, name="signal")


@signal_app.command("add")
def signal_add(
    account: str = typer.Option(...),
    type: SignalType = typer.Option(..., "--type"),
    headline: str = typer.Option(...),
    source: Optional[str] = typer.Option(None),
    relevance: Relevance = typer.Option(Relevance.MEDIUM),
    notes: Optional[str] = typer.Option(None),
) -> None:
    """Record a dated commercial signal about an account."""
    sig = Signal(
        account_slug=account,
        detected_at=datetime.utcnow(),
        signal_type=type,
        headline=headline,
        source_url=source,
        relevance=relevance,
        notes=notes,
    )
    _repo().add_signal(sig)
    acct = _repo().get_account(account)
    append_atom(
        _root(),
        account,
        acct.name if acct else account,
        f"{type.value} signal ({relevance.value}): {headline}",
    )
    console.print(f"[green]Recorded {type.value} signal[/green] for {account}: {headline}")


# ----- hypothesis -----------------------------------------------------------

hypothesis_app = typer.Typer(help="Set + manage commercial hypotheses.", no_args_is_help=True)
app.add_typer(hypothesis_app, name="hypothesis")


@hypothesis_app.command("set")
def hypothesis_set(
    account: str = typer.Option(...),
    headline: str = typer.Option(...),
    falsification: str = typer.Option(...),
    outcome: OutcomeMetric = typer.Option(...),
    status: HypothesisStatus = typer.Option(HypothesisStatus.ACTIVE),
) -> None:
    """Set or replace the commercial hypothesis for an account."""
    h = Hypothesis(
        account_slug=account,
        headline=headline,
        falsification_test=falsification,
        outcome_metric=outcome,
        status=status,
    )
    saved = _repo().upsert_hypothesis(h)
    acct = _repo().get_account(account)
    append_atom(
        _root(),
        account,
        acct.name if acct else account,
        f"Hypothesis set ({outcome.value}): {headline}",
    )
    console.print(f"[green]Saved hypothesis[/green] id={saved.id} for {account}")


# ----- qualification --------------------------------------------------------

qualify_app = typer.Typer(help="MEDDPICC qualification.", no_args_is_help=True)
app.add_typer(qualify_app, name="qualify")


@qualify_app.command("update")
def qualify_update(
    account: str = typer.Option(...),
    metrics: Optional[str] = typer.Option(None),
    economic_buyer: Optional[str] = typer.Option(None, help="Stakeholder name"),
    decision_criteria: Optional[str] = typer.Option(None),
    decision_process: Optional[str] = typer.Option(None),
    paper_process: Optional[str] = typer.Option(None),
    implied_pain: Optional[str] = typer.Option(None),
    champion: Optional[str] = typer.Option(None, help="Stakeholder name"),
    competition: Optional[str] = typer.Option(None),
) -> None:
    """Update MEDDPICC fields for an account. Only provided fields change."""
    repo = _repo()
    current = repo.get_qualification(account) or Qualification(account_slug=account)
    if metrics is not None:
        current.metrics = metrics
    if decision_criteria is not None:
        current.decision_criteria = decision_criteria
    if decision_process is not None:
        current.decision_process = decision_process
    if paper_process is not None:
        current.paper_process = paper_process
    if implied_pain is not None:
        current.implied_pain = implied_pain
    if competition is not None:
        current.competition = competition
    if economic_buyer:
        s = repo.find_stakeholder(account, economic_buyer)
        if s:
            current.economic_buyer_id = s.id
    if champion:
        s = repo.find_stakeholder(account, champion)
        if s:
            current.champion_id = s.id
    saved = repo.upsert_qualification(current)
    acct = repo.get_account(account)
    append_atom(
        _root(),
        account,
        acct.name if acct else account,
        f"MEDDPICC updated; completeness {saved.completeness_score}%.",
    )
    console.print(
        f"[green]Updated MEDDPICC[/green] for {account}; completeness {saved.completeness_score}%"
    )


@qualify_app.command("show")
def qualify_show(account: str, format: str = typer.Option("table", "--format")) -> None:
    q = _repo().get_qualification(account)
    if not q:
        typer.echo(f"No qualification yet for {account}", err=True)
        raise typer.Exit(1)
    _emit(q, format)


# ----- meeting --------------------------------------------------------------

meeting_app = typer.Typer(help="Schedule and complete meetings.", no_args_is_help=True)
app.add_typer(meeting_app, name="meeting")


@meeting_app.command("add")
def meeting_add(
    account: str = typer.Option(...),
    stakeholder: List[str] = typer.Option(..., "--stakeholder", help="Repeat for each attendee"),
    scheduled: datetime = typer.Option(..., help="ISO datetime"),
    type: MeetingType = typer.Option(..., "--type"),
    status: MeetingStatus = typer.Option(MeetingStatus.SCHEDULED),
) -> None:
    """Add a meeting."""
    repo = _repo()
    ids: list[int] = []
    for n in stakeholder:
        s = repo.find_stakeholder(account, n)
        if not s:
            typer.echo(f"No stakeholder {n!r} on {account}", err=True)
            raise typer.Exit(1)
        ids.append(s.id)
    m = Meeting(
        account_slug=account,
        stakeholder_ids=ids,
        scheduled_at=scheduled,
        meeting_type=type,
        status=status,
    )
    saved = repo.add_meeting(m)
    acct = repo.get_account(account)
    append_atom(
        _root(),
        account,
        acct.name if acct else account,
        f"{type.value} meeting scheduled {scheduled.date().isoformat()} with {', '.join(stakeholder)}.",
    )
    console.print(f"[green]Scheduled meeting[/green] id={saved.id}")


# ----- warm route -----------------------------------------------------------

route_app = typer.Typer(help="Track warm-route introductions.", no_args_is_help=True)
app.add_typer(route_app, name="route")


@route_app.command("add")
def route_add(
    target: str = typer.Option(..., help="Target stakeholder name"),
    account: str = typer.Option(..., help="Target stakeholder's account slug"),
    via: str = typer.Option(..., help="Intermediary's name"),
    type: WarmRouteType = typer.Option(..., "--type"),
    status: WarmRouteStatus = typer.Option(WarmRouteStatus.IDENTIFIED),
    notes: Optional[str] = typer.Option(None),
) -> None:
    """Record a warm route to a stakeholder."""
    repo = _repo()
    s = repo.find_stakeholder(account, target)
    if not s:
        typer.echo(f"No stakeholder {target!r} on {account}", err=True)
        raise typer.Exit(1)
    w = WarmRoute(
        target_stakeholder_id=s.id,
        via=via,
        via_type=type,
        status=status,
        notes=notes,
        requested_at=datetime.utcnow() if status == WarmRouteStatus.REQUESTED else None,
    )
    saved = repo.add_warm_route(w)
    acct = repo.get_account(account)
    append_atom(
        _root(),
        account,
        acct.name if acct else account,
        f"Warm route to {target} via {via} ({type.value}) — status {status.value}.",
    )
    console.print(f"[green]Logged warm route[/green] id={saved.id}")


# ----- scene + atoms + persona + search ------------------------------------

@app.command()
def scene(
    slug: str,
    write: bool = typer.Option(False, "--write", help="Render and persist a fresh L2 scene file."),
) -> None:
    """Show (and optionally regenerate) the L2 scene for an account."""
    if write:
        repo = _repo()
        a = repo.get_account(slug)
        if not a:
            typer.echo(f"No account {slug}", err=True)
            raise typer.Exit(1)
        # Compose simple defaults from current data.
        stakeholders = repo.list_stakeholders(slug)
        champions = [s for s in stakeholders if s.meddpicc_role == MeddpiccRole.CHAMPION]
        key = (
            f"{champions[0].name}, {champions[0].title}"
            if champions
            else (f"{stakeholders[0].name}, {stakeholders[0].title}" if stakeholders else "Unknown — research needed")
        )
        signals = repo.list_signals(slug)
        context = signals[0].headline if signals else "Unknown — research needed"
        hyps = repo.list_hypotheses(slug)
        motion = hyps[0].headline if hyps else "Unknown — research needed"
        path = write_scene(
            _root(),
            slug,
            name=a.name,
            key_stakeholder=key,
            strategic_context=context,
            sales_motion=motion,
        )
        console.print(f"[green]Wrote scene[/green] {path}")
    text = read_scene(_root(), slug)
    if not text:
        typer.echo(f"No scene yet for {slug}. Run with --write to generate one.", err=True)
        raise typer.Exit(1)
    console.print(text)


@app.command()
def atoms(slug: str) -> None:
    """Print the L1 atoms file for an account."""
    text = read_atoms(_root(), slug)
    if not text:
        typer.echo(f"No atoms yet for {slug}.", err=True)
        raise typer.Exit(1)
    console.print(text)


persona_app = typer.Typer(help="Manage the persona (L3).", no_args_is_help=False, invoke_without_command=True)
app.add_typer(persona_app, name="persona")


@persona_app.callback(invoke_without_command=True)
def persona_show(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return
    text = read_persona(_root())
    if not text:
        typer.echo("No persona set. Run `sam persona set ...`", err=True)
        raise typer.Exit(1)
    console.print(text)


@persona_app.command("set")
def persona_set(
    name: str = typer.Option(...),
    role: str = typer.Option(...),
    company: str = typer.Option(...),
    territory: str = typer.Option(...),
    manager: Optional[str] = typer.Option(None),
    methodology: str = typer.Option("MEDDPICC"),
    first_touch_style: str = typer.Option(...),
    working_style: str = typer.Option(...),
) -> None:
    """Set or replace the persona for this memory store."""
    p = Persona(
        name=name,
        role=role,
        company=company,
        territory=territory,
        manager=manager,
        methodology=methodology,
        first_touch_style=first_touch_style,
        working_style=working_style,
    )
    _repo().upsert_persona(p)
    path = write_persona(_root(), p)
    console.print(f"[green]Saved persona[/green] {path}")


@app.command()
def search(query: str, format: str = typer.Option("table", "--format")) -> None:
    """Full-text search across accounts, stakeholders, signals, hypotheses, touches."""
    hits = _repo().search_text(query)
    if format == "json":
        _emit(hits, "json")
        return
    if not hits:
        console.print("[yellow]No matches.[/yellow]")
        return
    table = Table(title=f'Search "{query}"')
    table.add_column("Kind", style="cyan")
    table.add_column("Match")
    for h in hits:
        kind = h["kind"]
        if kind == "account":
            row = f"{h['name']} ({h['slug']})"
        elif kind == "stakeholder":
            row = f"{h['name']} @ {h['account_slug']}"
        elif kind in ("signal", "hypothesis"):
            row = f"{h['headline']} @ {h['account_slug']}"
        elif kind == "touch":
            row = h["body"][:80] + ("..." if len(h["body"]) > 80 else "")
        else:
            row = str(h)
        table.add_row(kind, row)
    console.print(table)


if __name__ == "__main__":
    sys.exit(app())
