"""Smoke test the CLI via typer.testing."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from sam.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "sam" in result.stdout


def test_init_and_account_lifecycle(tmp_path: Path) -> None:
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0, result.output

        result = runner.invoke(
            app,
            [
                "account", "add",
                "--slug", "acme-corp",
                "--name", "Acme Corp",
                "--tier", "1",
                "--vertical", "Telco",
            ],
        )
        assert result.exit_code == 0, result.output

        result = runner.invoke(app, ["account", "list", "--format", "json"])
        assert result.exit_code == 0
        assert "acme-corp" in result.stdout

        result = runner.invoke(
            app,
            [
                "stakeholder", "add",
                "--account", "acme-corp",
                "--name", "Jane Doe",
                "--title", "CTO",
                "--meddpicc", "Champion",
            ],
        )
        assert result.exit_code == 0, result.output

        result = runner.invoke(app, ["stakeholder", "list", "--account", "acme-corp"])
        assert result.exit_code == 0
        assert "Jane Doe" in result.stdout

        result = runner.invoke(app, ["atoms", "acme-corp"])
        assert result.exit_code == 0
        assert "Acme" in result.stdout
    finally:
        os.chdir(cwd)
