import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AuditRecord:
    query_name: str
    query_version: int
    parameters: dict
    status: str          # 'SUCCESS' | 'ERROR'
    error: str | None
    row_count: int
    duration_ms: int
    caller_id: str | None = None
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def parameters_json(self) -> str:
        return json.dumps(self.parameters)

    def to_dict(self) -> dict:
        return {
            "query_name": self.query_name,
            "query_version": self.query_version,
            "executed_at": self.executed_at.isoformat(),
            "parameters": self.parameters,
            "status": self.status,
            "error": self.error,
            "row_count": self.row_count,
            "duration_ms": self.duration_ms,
            "caller_id": self.caller_id,
        }
