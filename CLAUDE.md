# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python tool that collects Claude Code CLI usage from `~/.claude/projects/**/*.jsonl`, stores it in SQLite, and serves a Chart.js dashboard at `http://localhost:5555`.

## Setup & Commands

```bash
# Install (editable) with uv
uv pip install -e ".[dev]"

# Sync data from ~/.claude then open dashboard
claude-tracker serve

# Sync only (no server)
claude-tracker sync

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_collector.py::test_parse_jsonl_extracts_assistant_messages
```

## Architecture

Three modules + a CLI entry point:

**`collector.py`** — reads `~/.claude/projects/**/*.jsonl`, extracts `type=assistant` records that have a `message.usage` block, and calls `db.upsert_messages()`. Uses `INSERT OR IGNORE` so repeated runs are safe.

**`db.py`** — owns the SQLite schema and all queries. DB lives at `~/.claude/usage_tracker.db` by default. All public query functions accept an optional `db_path` and a `days` parameter (0 = all time). The `days` parameter maps to a SQLite `datetime('now', '-N days')` offset.

**`server.py`** — thin Flask app. All data endpoints accept `?days=N`. The `POST /api/sync` endpoint triggers a live re-collect without restarting the server.

**`cli.py`** — Click commands: `sync` and `serve`. `serve` runs `collect()` on start by default.

## Data Source

`~/.claude/projects/<encoded-path>/<session-id>.jsonl` — one file per session. Each line is a JSON record. Only `type=assistant` lines with a `message.usage` block carry token counts:

```json
{
  "type": "assistant",
  "uuid": "...",
  "sessionId": "...",
  "cwd": "/home/user/project",
  "timestamp": "2026-04-17T06:07:35.793Z",
  "message": {
    "model": "claude-sonnet-4-6",
    "usage": {
      "input_tokens": 3,
      "output_tokens": 398,
      "cache_creation_input_tokens": 9881,
      "cache_read_input_tokens": 11715
    }
  }
}
```

## Background Sync (systemd)

Copy the units and enable:
```bash
cp systemd/claude-tracker.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now claude-tracker.timer
```
