import json
import logging
from pathlib import Path

from claude_tracker.db import init_db, upsert_messages

logger = logging.getLogger(__name__)


def default_claude_dir() -> Path:
    return Path.home() / ".claude"


def find_jsonl_files(claude_dir: Path) -> list[Path]:
    return sorted((claude_dir / "projects").glob("**/*.jsonl"))


def parse_jsonl_file(path: Path) -> list[dict]:
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("type") != "assistant":
                    continue

                msg = record.get("message", {})
                usage = msg.get("usage")
                if not usage:
                    continue

                uuid = record.get("uuid")
                if not uuid:
                    continue

                rows.append({
                    "uuid": uuid,
                    "session_id": record.get("sessionId", ""),
                    "project_path": record.get("cwd", ""),
                    "timestamp": record.get("timestamp", ""),
                    "model": msg.get("model", ""),
                    "input_tokens": usage.get("input_tokens", 0) or 0,
                    "output_tokens": usage.get("output_tokens", 0) or 0,
                    "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0) or 0,
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0) or 0,
                    "source_file": str(path),
                })
    except OSError as e:
        logger.warning("Could not read %s: %s", path, e)
    return rows


def collect(claude_dir: Path | None = None, db_path: Path | None = None) -> int:
    """Scan all JSONL files and upsert new messages. Returns count of files processed."""
    base = claude_dir or default_claude_dir()
    init_db(db_path)

    files = find_jsonl_files(base)
    if not files:
        logger.warning("No JSONL files found under %s/projects/", base)
        return 0

    total_rows = 0
    for path in files:
        rows = parse_jsonl_file(path)
        if rows:
            upsert_messages(rows, db_path)
            total_rows += len(rows)
        logger.debug("Processed %s: %d messages", path.name, len(rows))

    logger.info("Collected %d messages from %d files", total_rows, len(files))
    return len(files)
