import json
from dataclasses import dataclass

from db.connection import get_connection


def _read_lob(value) -> str:
    """Read a LOB value or return the string as-is."""
    if hasattr(value, "read"):
        return value.read()
    return value or ""


@dataclass
class QueryRecord:
    id: int
    name: str
    description: str
    sql_text: str
    parameters: list[dict]
    version: int
    tags: str | None


def fetch_query(name: str) -> QueryRecord:
    """Fetch the active version of a named query from the registry."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description, sql_text, parameters,
                       version, tags
                FROM query_registry
                WHERE name = :name AND is_active = 1
                FETCH FIRST 1 ROW ONLY
                """,
                {"name": name},
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"No active query found with name: {name!r}")

            id_, name_, desc, sql_lob, params_lob, version, tags = row
            sql_text = _read_lob(sql_lob)
            params_raw = _read_lob(params_lob)
            parameters = json.loads(params_raw) if params_raw else []

            return QueryRecord(
                id=id_,
                name=name_,
                description=desc,
                sql_text=sql_text,
                parameters=parameters,
                version=version,
                tags=tags,
            )


def fetch_all_queries(tags: str | None = None) -> list[dict]:
    """Fetch all active queries, optionally filtered by one or more tags."""
    sql = """
        SELECT name, description, parameters, tags
        FROM query_registry
        WHERE is_active = 1
    """
    bind: dict = {}

    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        conditions = " OR ".join(f"tags LIKE :tag{i}" for i in range(len(tag_list)))
        sql += f" AND ({conditions})"
        for i, tag in enumerate(tag_list):
            bind[f"tag{i}"] = f"%{tag}%"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, bind)
            rows = cur.fetchall()

    result = []
    for name, desc, params_lob, tags_val in rows:
        params_raw = _read_lob(params_lob)
        parameters = json.loads(params_raw) if params_raw else []
        result.append(
            {
                "name": name,
                "description": desc,
                "tags": [t.strip() for t in tags_val.split(",")] if tags_val else [],
                "parameters": parameters,
            }
        )
    return result
