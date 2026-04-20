# ClaudeUsageTrackEr

Track and visualize your [Claude Code](https://claude.ai/code) CLI usage — token consumption, session activity, model breakdown, and correlated git commits — through a local dark-mode dashboard.

---

## What it does

- **Parses** `~/.claude/projects/**/*.jsonl` session logs produced by the Claude Code CLI
- **Stores** extracted token counts in a local SQLite database (`~/.claude/usage_tracker.db`)
- **Serves** an interactive Chart.js dashboard at `http://localhost:5555`

### Dashboard features

| Feature | Details |
|---|---|
| Summary cards | Total tokens, sessions, projects, models used |
| Daily token chart | Stacked bar: input / output / cache-read / cache-creation |
| Hourly heatmap | Usage by hour of day across the selected window |
| Day drilldown | Click any bar to see hourly breakdown for that day |
| Git activity | Commits made during each session hour, per project |
| Projects table | Token spend ranked by project path |
| Model breakdown | Token split across Claude model versions |
| Time filter | Last 7 / 30 / 90 days or all-time |
| Live sync | Re-scan logs without restarting via the Sync button |

---

## Requirements

- Linux, macOS, or WSL2
- Claude Code CLI installed and used at least once (so `~/.claude/projects/` exists)

---

## Installation

### Option A — one-liner (downloads a pre-built binary)

```bash
curl -fsSL https://raw.githubusercontent.com/rammohan-b/ClaudeUsageTrackEr/master/install.sh | bash
```

The script detects your platform (Linux x86_64, macOS arm64, macOS x86_64), downloads the correct binary from the [latest release](https://github.com/rammohan-b/ClaudeUsageTrackEr/releases/latest), and installs it to `~/.local/bin`.

### Option B — build from source

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/rammohan-b/ClaudeUsageTrackEr.git
cd ClaudeUsageTrackEr
uv pip install -e ".[dev]"
```

---

## Usage

```bash
# Sync data then open the dashboard (default: http://localhost:5555)
claude-tracker serve

# Use a custom port
claude-tracker serve --port 8080

# Sync only — no server
claude-tracker sync

# Point at a non-default ~/.claude directory
claude-tracker sync --claude-dir /path/to/.claude

# Skip the initial sync on server start
claude-tracker serve --no-sync-on-start

# Verbose logging
claude-tracker --verbose serve
```

The dashboard is available at `http://localhost:5555` (or whichever port you chose).  
Use the **Sync** button in the UI to pull in new session data without restarting.

---

## Background sync (systemd — Linux / WSL2)

To sync automatically every 15 minutes:

```bash
cp systemd/claude-tracker.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now claude-tracker.timer
```

Check status:

```bash
systemctl --user status claude-tracker.timer
journalctl --user -u claude-tracker.service
```

---

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_collector.py::test_parse_jsonl_extracts_assistant_messages
```

### Project layout

```
src/claude_tracker/
├── cli.py          # Click entry point (sync, serve commands)
├── collector.py    # Parses ~/.claude JSONL → row dicts
├── db.py           # SQLite schema + all query functions
├── server.py       # Flask app + API endpoints
├── git_activity.py # git log queries per project/date/hour
└── templates/
    └── index.html  # Self-contained Chart.js dashboard
```

---

## License

[MIT](LICENSE)
