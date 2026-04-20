import json
import tempfile
from pathlib import Path

from claude_tracker.collector import parse_jsonl_file
from claude_tracker.db import init_db, query_summary, upsert_messages


def make_jsonl(path: Path, records: list[dict]):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


ASSISTANT_MSG = {
    "type": "assistant",
    "uuid": "test-uuid-1",
    "sessionId": "sess-1",
    "cwd": "/home/user/project",
    "timestamp": "2026-01-15T10:30:00.000Z",
    "message": {
        "model": "claude-sonnet-4-6",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_creation_input_tokens": 200,
            "cache_read_input_tokens": 300,
        },
    },
}


def test_parse_jsonl_extracts_assistant_messages(tmp_path):
    f = tmp_path / "session.jsonl"
    make_jsonl(f, [
        {"type": "user", "uuid": "u1", "message": {"role": "user", "content": "hi"}},
        ASSISTANT_MSG,
        {"type": "permission-mode", "permissionMode": "default"},
    ])
    rows = parse_jsonl_file(f)
    assert len(rows) == 1
    row = rows[0]
    assert row["uuid"] == "test-uuid-1"
    assert row["input_tokens"] == 100
    assert row["output_tokens"] == 50
    assert row["cache_creation_tokens"] == 200
    assert row["cache_read_tokens"] == 300
    assert row["model"] == "claude-sonnet-4-6"


def test_parse_jsonl_skips_messages_without_usage(tmp_path):
    msg = {**ASSISTANT_MSG, "uuid": "no-usage", "message": {"model": "claude-sonnet-4-6"}}
    f = tmp_path / "session.jsonl"
    make_jsonl(f, [msg])
    assert parse_jsonl_file(f) == []


def test_parse_jsonl_handles_malformed_lines(tmp_path):
    f = tmp_path / "session.jsonl"
    f.write_text('not json\n' + json.dumps(ASSISTANT_MSG) + '\n')
    rows = parse_jsonl_file(f)
    assert len(rows) == 1


def test_upsert_is_idempotent(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    row = {
        "uuid": "abc",
        "session_id": "s1",
        "project_path": "/proj",
        "timestamp": "2026-01-15T10:00:00.000Z",
        "model": "claude-sonnet-4-6",
        "input_tokens": 10,
        "output_tokens": 5,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "source_file": "/path/to/file.jsonl",
    }
    upsert_messages([row], db)
    upsert_messages([row], db)  # second insert should be ignored
    summary = query_summary(days=0, db_path=db)
    assert summary["total_messages"] == 1
