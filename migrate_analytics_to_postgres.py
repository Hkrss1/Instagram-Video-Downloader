#!/usr/bin/env python
"""
One-click migration from local SQLite analytics.db to Postgres (Supabase).

Usage:
  python migrate_analytics_to_postgres.py

Optional:
  python migrate_analytics_to_postgres.py --sqlite-path analytics.db --database-url "postgresql://..."
"""

import argparse
import os
import sqlite3
import sys
from typing import Iterable, List, Tuple

try:
    import psycopg2
    from psycopg2.extras import execute_values
except Exception as exc:  # pragma: no cover
    print(f"ERROR: psycopg2 not installed: {exc}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS request_logs (
    id BIGSERIAL PRIMARY KEY,
    ts BIGINT NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    endpoint TEXT,
    ip TEXT,
    ua TEXT,
    status INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL
)
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_request_logs_ts ON request_logs(ts)",
    "CREATE INDEX IF NOT EXISTS idx_request_logs_path ON request_logs(path)",
    "CREATE INDEX IF NOT EXISTS idx_request_logs_ip ON request_logs(ip)",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate analytics.db (SQLite) to Postgres")
    parser.add_argument("--sqlite-path", default="analytics.db", help="Path to SQLite analytics DB")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Postgres URL (defaults to DATABASE_URL env var)",
    )
    parser.add_argument("--batch-size", type=int, default=1000, help="Bulk insert batch size")
    return parser.parse_args()


def normalize_database_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def fetch_sqlite_rows(sqlite_path: str) -> List[Tuple]:
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite file not found: {sqlite_path}")

    conn = sqlite3.connect(sqlite_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, ts, method, path, endpoint, ip, ua, status, latency_ms
            FROM request_logs
            ORDER BY id ASC
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


def batched(rows: List[Tuple], size: int) -> Iterable[List[Tuple]]:
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def migrate(rows: List[Tuple], database_url: str, batch_size: int) -> None:
    conn = psycopg2.connect(database_url)
    inserted = 0
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)
                for sql in CREATE_INDEX_SQL:
                    cur.execute(sql)

                if not rows:
                    print("No rows found in SQLite. Schema verified on Postgres.")
                    return

                insert_sql = """
                    INSERT INTO request_logs (id, ts, method, path, endpoint, ip, ua, status, latency_ms)
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING
                """

                for batch in batched(rows, batch_size):
                    execute_values(cur, insert_sql, batch)
                    inserted += len(batch)

                cur.execute("SELECT COALESCE(MAX(id), 1) FROM request_logs")
                max_id = int(cur.fetchone()[0])
                cur.execute("SELECT setval(pg_get_serial_sequence('request_logs', 'id'), %s, true)", (max_id,))

        print(f"Migration complete. Processed rows: {len(rows)}")
        print("Idempotent mode: duplicate IDs are skipped on re-run.")
    finally:
        conn.close()


def main() -> int:
    args = parse_args()
    db_url = normalize_database_url(args.database_url.strip())
    if not db_url:
        print("ERROR: DATABASE_URL is required. Pass --database-url or set DATABASE_URL env var.")
        return 1

    try:
        rows = fetch_sqlite_rows(args.sqlite_path)
    except Exception as exc:
        print(f"ERROR reading SQLite: {exc}")
        return 1

    try:
        migrate(rows, db_url, args.batch_size)
        return 0
    except Exception as exc:
        print(f"ERROR migrating data: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
