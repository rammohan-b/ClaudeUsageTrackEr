import sqlite3
from contextlib import contextmanager
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    uuid             TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    project_path     TEXT NOT NULL,
    timestamp        TEXT NOT NULL,
    model            TEXT,
    input_tokens     INTEGER DEFAULT 0,
    output_tokens    INTEGER DEFAULT 0,
    cache_creation_tokens INTEGER DEFAULT 0,
    cache_read_tokens     INTEGER DEFAULT 0,
    source_file      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_timestamp   ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_project     ON messages(project_path);
CREATE INDEX IF NOT EXISTS idx_session     ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_model       ON messages(model);
"""


def get_db_path() -> Path:
    default = Path.home() / ".claude" / "usage_tracker.db"
    return default


@contextmanager
def get_conn(db_path: Path | None = None):
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path | None = None):
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)


def upsert_messages(rows: list[dict], db_path: Path | None = None):
    sql = """
    INSERT OR IGNORE INTO messages
        (uuid, session_id, project_path, timestamp, model,
         input_tokens, output_tokens, cache_creation_tokens,
         cache_read_tokens, source_file)
    VALUES
        (:uuid, :session_id, :project_path, :timestamp, :model,
         :input_tokens, :output_tokens, :cache_creation_tokens,
         :cache_read_tokens, :source_file)
    """
    with get_conn(db_path) as conn:
        conn.executemany(sql, rows)


def query_daily(days: int = 30, db_path: Path | None = None) -> list[dict]:
    sql = """
    SELECT
        date(timestamp) AS day,
        SUM(input_tokens)          AS input_tokens,
        SUM(output_tokens)         AS output_tokens,
        SUM(cache_creation_tokens) AS cache_creation_tokens,
        SUM(cache_read_tokens)     AS cache_read_tokens,
        COUNT(*)                   AS message_count
    FROM messages
    WHERE timestamp >= datetime('now', :offset)
    GROUP BY day
    ORDER BY day
    """
    offset = f"-{days} days" if days > 0 else "-9999 days"
    with get_conn(db_path) as conn:
        rows = conn.execute(sql, {"offset": offset}).fetchall()
    return [dict(r) for r in rows]


def query_hourly(days: int = 30, db_path: Path | None = None) -> list[dict]:
    sql = """
    SELECT
        CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
        SUM(input_tokens + output_tokens)          AS total_tokens,
        SUM(input_tokens)                          AS input_tokens,
        SUM(output_tokens)                         AS output_tokens,
        COUNT(*)                                   AS message_count
    FROM messages
    WHERE timestamp >= datetime('now', :offset)
    GROUP BY hour
    ORDER BY hour
    """
    offset = f"-{days} days" if days > 0 else "-9999 days"
    with get_conn(db_path) as conn:
        rows = conn.execute(sql, {"offset": offset}).fetchall()
    return [dict(r) for r in rows]


def query_hourly_for_date(date: str, db_path: Path | None = None) -> list[dict]:
    sql = """
    SELECT
        CAST(strftime('%H', timestamp) AS INTEGER) AS hour,
        SUM(input_tokens + output_tokens)          AS total_tokens,
        SUM(input_tokens)                          AS input_tokens,
        SUM(output_tokens)                         AS output_tokens,
        COUNT(*)                                   AS message_count
    FROM messages
    WHERE date(timestamp) = :date
    GROUP BY hour
    ORDER BY hour
    """
    with get_conn(db_path) as conn:
        rows = conn.execute(sql, {"date": date}).fetchall()
    return [dict(r) for r in rows]


def query_projects_for_date(date: str, db_path: Path | None = None) -> list[str]:
    sql = "SELECT DISTINCT project_path FROM messages WHERE date(timestamp) = :date"
    with get_conn(db_path) as conn:
        rows = conn.execute(sql, {"date": date}).fetchall()
    return [r[0] for r in rows]


def query_projects(days: int = 30, db_path: Path | None = None) -> list[dict]:
    sql = """
    SELECT
        project_path,
        SUM(input_tokens + output_tokens)  AS total_tokens,
        SUM(input_tokens)                  AS input_tokens,
        SUM(output_tokens)                 AS output_tokens,
        COUNT(DISTINCT session_id)         AS sessions,
        COUNT(*)                           AS message_count
    FROM messages
    WHERE timestamp >= datetime('now', :offset)
    GROUP BY project_path
    ORDER BY total_tokens DESC
    LIMIT 20
    """
    offset = f"-{days} days" if days > 0 else "-9999 days"
    with get_conn(db_path) as conn:
        rows = conn.execute(sql, {"offset": offset}).fetchall()
    return [dict(r) for r in rows]


def query_models(days: int = 30, db_path: Path | None = None) -> list[dict]:
    sql = """
    SELECT
        model,
        SUM(input_tokens + output_tokens)  AS total_tokens,
        COUNT(*)                           AS message_count
    FROM messages
    WHERE timestamp >= datetime('now', :offset)
    GROUP BY model
    ORDER BY total_tokens DESC
    """
    offset = f"-{days} days" if days > 0 else "-9999 days"
    with get_conn(db_path) as conn:
        rows = conn.execute(sql, {"offset": offset}).fetchall()
    return [dict(r) for r in rows]


def query_summary(days: int = 30, db_path: Path | None = None) -> dict:
    sql = """
    SELECT
        COUNT(*)                                   AS total_messages,
        SUM(input_tokens)                          AS total_input,
        SUM(output_tokens)                         AS total_output,
        SUM(cache_creation_tokens)                 AS total_cache_creation,
        SUM(cache_read_tokens)                     AS total_cache_read,
        COUNT(DISTINCT session_id)                 AS total_sessions,
        COUNT(DISTINCT project_path)               AS total_projects,
        COUNT(DISTINCT model)                      AS total_models,
        MIN(date(timestamp))                       AS first_day,
        MAX(date(timestamp))                       AS last_day
    FROM messages
    WHERE timestamp >= datetime('now', :offset)
    """
    offset = f"-{days} days" if days > 0 else "-9999 days"
    with get_conn(db_path) as conn:
        row = conn.execute(sql, {"offset": offset}).fetchone()
    return dict(row) if row else {}
