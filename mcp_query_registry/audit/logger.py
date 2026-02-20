import json
import logging
from logging.handlers import TimedRotatingFileHandler

from audit.record import AuditRecord
from config import settings

_audit_log = logging.getLogger("audit")
_audit_log.setLevel(logging.INFO)
_audit_log.propagate = False

_handler = TimedRotatingFileHandler(
    filename=settings.audit_log_path,
    when="midnight",
    backupCount=30,
    utc=True,
)
_audit_log.addHandler(_handler)


def log_audit(record: AuditRecord) -> None:
    _audit_log.info(json.dumps(record.to_dict()))
