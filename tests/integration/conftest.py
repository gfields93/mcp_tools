"""
Integration test fixtures.

Provides an in-memory SQLite database that mimics the Oracle registry
schema, plus a connection adapter that bridges the python-oracledb API
used throughout the project to sqlite3.

Why SQLite?
- python-oracledb requires a live Oracle instance; SQLite ships with Python
- SQLite supports named bind variables (:name) natively
- The one Oracle-specific construct used internally is
  "FETCH FIRST N ROWS ONLY", which the adapter rewrites to "LIMIT N"
- For DML queries the adapter transparently converts Oracle positional
  bind syntax (:1, :2, ...) to SQLite positional syntax (?, ?, ...)
"""
import json
import re
import sqlite3
import uuid
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# SQL adaptation helpers
# ---------------------------------------------------------------------------

_FETCH_FIRST = re.compile(
    r"\bFETCH\s+FIRST\s+(\d+)\s+ROWS?\s+ONLY\b", re.IGNORECASE
)
_ORACLE_POSITIONAL = re.compile(r":\d+")


def _adapt_sql(sql: str, params) -> tuple[str, object]:
    """Rewrite Oracle-specific SQL constructs for SQLite."""
    sql = _FETCH_FIRST.sub(r"LIMIT \1", sql)
    if isinstance(params, list):
        # Oracle positional style: VALUES (:1, :2, ...) → VALUES (?, ?, ...)
        sql = _ORACLE_POSITIONAL.sub("?", sql)
    return sql, params


# ---------------------------------------------------------------------------
# sqlite3 ↔ oracledb interface adapters
# ---------------------------------------------------------------------------


class SQLiteCursorAdapter:
    """Wraps sqlite3.Cursor to match the python-oracledb cursor interface."""

    def __init__(self, cur: sqlite3.Cursor) -> None:
        self._cur = cur

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql: str, params=None) -> None:
        adapted_sql, adapted_params = _adapt_sql(sql, params)
        if adapted_params is None:
            self._cur.execute(adapted_sql)
        else:
            self._cur.execute(adapted_sql, adapted_params)

    @property
    def description(self):
        return self._cur.description

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, n: int):
        return self._cur.fetchmany(n)


class SQLiteConnAdapter:
    """Wraps sqlite3.Connection to match the python-oracledb connection interface."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *args):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        return False

    def cursor(self) -> SQLiteCursorAdapter:
        return SQLiteCursorAdapter(self._conn.cursor())

    def commit(self) -> None:
        self._conn.commit()


# ---------------------------------------------------------------------------
# Schema & seed helpers
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE query_registry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT    NOT NULL,
    sql_text    TEXT    NOT NULL,
    parameters  TEXT,
    version     INTEGER DEFAULT 1 NOT NULL,
    is_active   INTEGER DEFAULT 1,
    tags        TEXT
);

CREATE TABLE query_audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    query_name    TEXT    NOT NULL,
    query_version INTEGER NOT NULL,
    executed_at   TEXT    DEFAULT CURRENT_TIMESTAMP,
    parameters    TEXT,
    status        TEXT    NOT NULL,
    error         TEXT,
    row_count     INTEGER DEFAULT 0,
    duration_ms   INTEGER,
    caller_id     TEXT
);

-- Lookup table used by integration test queries
CREATE TABLE employees (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    department TEXT NOT NULL
);
"""

_EMPLOYEES = [
    (1, "Alice", "Engineering"),
    (2, "Bob",   "Finance"),
    (3, "Carol", "Engineering"),
]

_REGISTRY_ROWS = [
    (
        "get_employee_by_id",
        "Fetch one employee by primary key",
        "SELECT id, name, department FROM employees WHERE id = :id",
        json.dumps([{"name": "id", "type": "NUMBER", "required": True}]),
        1, 1, "hr,employees",
    ),
    (
        "list_by_department",
        "List employees in a given department",
        "SELECT id, name FROM employees WHERE department = :department",
        json.dumps([
            {
                "name": "department",
                "type": "VARCHAR2",
                "required": True,
                "allowed_values": ["Engineering", "Finance"],
            }
        ]),
        1, 1, "hr,employees",
    ),
    (
        "list_all_employees",
        "Return every employee — no parameters required",
        "SELECT id, name, department FROM employees ORDER BY id",
        None,
        1, 1, "hr",
    ),
    (
        "list_employees_optional_dept",
        "List employees with an optional department filter",
        "SELECT id, name, department FROM employees/*[ WHERE department = :department]*/ ORDER BY id",
        json.dumps([
            {
                "name": "department",
                "type": "VARCHAR2",
                "required": False,
                "allowed_values": ["Engineering", "Finance"],
            }
        ]),
        1, 1, "hr,employees",
    ),
    (
        "inactive_query",
        "Retired query — should never be visible",
        "SELECT 1",
        None,
        1, 0, None,
    ),
]


def _setup(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_SQL)
    conn.executemany("INSERT INTO employees VALUES (?, ?, ?)", _EMPLOYEES)
    conn.executemany(
        """INSERT INTO query_registry
               (name, description, sql_text, parameters,
                version, is_active, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        _REGISTRY_ROWS,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry():
    """
    Pytest fixture that:
    1. Creates a fresh in-memory SQLite database per test.
    2. Sets up the registry schema and seeds test data.
    3. Patches db.registry.get_connection and tools.run_query.get_connection
       to return SQLite-backed adapters, so the full tool code runs against
       the in-memory database without needing Oracle.
    4. Mocks log_audit and write_audit_async to keep tests hermetic.

    Yields the raw sqlite3.Connection so individual tests can inspect or
    modify data directly.
    """
    # Unique URI ensures test isolation (each test gets its own in-memory DB)
    db_uri = f"file:inttest_{uuid.uuid4().hex}?mode=memory&cache=shared"

    conn = sqlite3.connect(db_uri, uri=True, check_same_thread=False)
    _setup(conn)

    def _make_conn():
        return SQLiteConnAdapter(
            sqlite3.connect(db_uri, uri=True, check_same_thread=False)
        )

    with (
        patch("db.registry.get_connection", side_effect=_make_conn),
        patch("tools.run_query.get_connection", side_effect=_make_conn),
        patch("tools.run_query.log_audit"),
        patch("tools.run_query.write_audit_async"),
    ):
        yield conn

    conn.close()
