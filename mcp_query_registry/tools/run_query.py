import time

from audit.logger import log_audit
from audit.masking import mask_parameters
from audit.oracle_writer import write_audit_async
from audit.record import AuditRecord
from config import settings
from db.connection import get_connection
from db.registry import fetch_query
from validation.parameters import validate_and_bind


def run_query(
    name: str,
    parameters: dict,
    max_rows: int = 500,
) -> list[dict]:
    """
    Execute a registered query and return results as a list of row dicts.

    Fetches the named query from the registry, validates the caller-supplied
    parameters against the stored definition, binds them safely via
    python-oracledb, executes the SQL, and returns up to max_rows rows.

    Args:
        name: The query slug to execute.
        parameters: Key-value map of bind variable names to their values.
        max_rows: Maximum rows to return (default 500). The server enforces a
                  hard ceiling that this value cannot exceed.

    Returns:
        List of result rows, each represented as a dict keyed by column name.

    Raises:
        ValueError: If the query is not found or a required parameter is
                    missing / has a disallowed value.
        TypeError: If a parameter value cannot be coerced to the declared type.
    """
    query = fetch_query(name)
    start = time.monotonic()
    status, error, row_count = "SUCCESS", None, 0

    bind_dict = validate_and_bind(query.parameters, parameters)
    safe_params = mask_parameters(parameters, query.parameters, settings.environment)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query.sql_text, bind_dict)
                cols = [col[0] for col in cur.description]
                effective_limit = min(max_rows, settings.hard_max_rows)
                rows = cur.fetchmany(effective_limit)
                row_count = len(rows)
                return [dict(zip(cols, row)) for row in rows]
    except Exception as exc:
        status, error = "ERROR", str(exc)
        raise
    finally:
        record = AuditRecord(
            query_name=name,
            query_version=query.version,
            parameters=safe_params,
            status=status,
            error=error,
            row_count=row_count,
            duration_ms=round((time.monotonic() - start) * 1000),
        )
        log_audit(record)
        write_audit_async(record)
