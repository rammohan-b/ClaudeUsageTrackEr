import logging

import click

from claude_tracker.collector import collect
from claude_tracker.db import get_db_path


@click.group()
@click.option("--verbose", "-v", is_flag=True)
def main(verbose: bool):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )


@main.command()
@click.option("--claude-dir", default=None, help="Path to ~/.claude (default: autodetect)")
def sync(claude_dir):
    """Scan ~/.claude JSONL files and load data into the database."""
    from pathlib import Path
    from claude_tracker.collector import collect as _collect

    n = _collect(Path(claude_dir) if claude_dir else None)
    click.echo(f"Processed {n} files. DB: {get_db_path()}")


@main.command()
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=5555, show_default=True)
@click.option("--sync-on-start/--no-sync-on-start", default=True, show_default=True,
              help="Run a sync before starting the server")
def serve(host, port, sync_on_start):
    """Start the dashboard web server."""
    if sync_on_start:
        click.echo("Syncing data…")
        collect()

    click.echo(f"Dashboard → http://{host}:{port}")
    from claude_tracker.server import run
    run(host=host, port=port)
