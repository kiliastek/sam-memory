"""Allow `python -m sam ...` as an alias for the `sam` CLI."""

from sam.cli import app

if __name__ == "__main__":
    app()
