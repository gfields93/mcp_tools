import logging
import threading

from audit.record import AuditRecord
from db.connection import get_connection

_log = logging.getLogger(__name__)


def write_audit_async(record: AuditRecord) -> None:
    """Fire-and-forget — spawns a daemon thread to avoid blocking the caller."""
    t = threading.Thread(target=_write, args=(record,), daemon=True)
    t.start()


def _write(record: AuditRecord) -> None:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO query_audit_log
                        (query_name, query_version, parameters, status,
                         error, row_count, duration_ms, caller_id)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
                    """,
                    [
                        record.query_name,
                        record.query_version,
                        record.parameters_json,
                        record.status,
                        record.error,
                        record.row_count,
                        record.duration_ms,
                        record.caller_id,
                    ],
                )
            conn.commit()
    except Exception as exc:
        _log.warning("Audit write to Oracle failed: %s", exc)
