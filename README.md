# Oracle MCP Query Registry

A dynamic SQL query registry backed by Oracle Database, exposed to AI clients through a [FastMCP](https://github.com/jlowin/fastmcp) server.

Queries are stored in Oracle and managed at runtime — no redeployment or code change required to add, update, or retire a query. The MCP server acts as a thin, stateless execution layer: it reads queries from the registry, validates parameters, binds them safely via [python-oracledb](https://python-oracledb.readthedocs.io/), executes against Oracle, and returns results. All query selection intelligence lives in the AI client.

---

## Features

- **Dynamic query registry** — store and version SQL in Oracle; activate or deactivate queries without touching application code
- **SQL injection prevention** — callers supply only a query name and parameter values; all SQL comes from the trusted registry
- **Typed parameter validation** — each query declares its bind variables with types (`NUMBER`, `VARCHAR2`, `DATE`, `TIMESTAMP`), required flags, allowed values, and defaults
- **DML guard** — data-modifying queries require an explicit `allow_dml=True` flag as a confirmation checkpoint
- **Dual-channel audit logging** — every execution is recorded to both a rotating JSON file log and an Oracle audit table (fire-and-forget, never blocks the response)
- **Environment-aware parameter masking** — sensitive parameter values are masked in audit records in upper environments (`uat`, `prod`) and logged verbatim in lower environments (`local`, `dev`, `sit`)
- **Versioned queries** — query history is preserved; rolling back is a single flag flip

---

## Project Structure

```
mcp_query_registry/
├── main.py                  # FastMCP server entry point
├── config.py                # Pydantic BaseSettings — env var loading
├── db/
│   ├── connection.py        # Oracle connection pool (python-oracledb)
│   └── registry.py          # Registry read queries
├── tools/
│   ├── list_queries.py      # MCP tool: discover available queries
│   ├── get_query.py         # MCP tool: inspect a single query
│   └── run_query.py         # MCP tool: execute a query
├── validation/
│   └── parameters.py        # Parameter type coercion and validation
└── audit/
    ├── record.py             # AuditRecord dataclass
    ├── masking.py            # Environment-aware parameter masking
    ├── logger.py             # Rotating JSON file logger
    └── oracle_writer.py      # Async Oracle audit table writer

sql/
└── ddl.sql                  # Oracle DDL for registry and audit tables

tests/                       # pytest suite (94% coverage)
```

---

## MCP Tools

### `list_queries`
Returns all active queries from the registry. The primary discovery tool — call this first to understand what is available.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tags` | `str` | No | Comma-separated tag filter (e.g. `"finance,orders"`) |

### `get_query`
Returns full detail for a single named query, including its SQL text and parameter definitions.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Query slug to look up |

### `run_query`
Executes a registered query and returns results as a list of row dicts.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Query slug to execute |
| `parameters` | `dict` | Yes | Bind variable values keyed by parameter name |
| `max_rows` | `int` | No | Row cap (default `500`, cannot exceed server hard ceiling) |
| `allow_dml` | `bool` | No | Must be `True` to run `DML` queries (default `False`) |

---

## Oracle Schema

Run [`sql/ddl.sql`](sql/ddl.sql) against your Oracle instance to create the registry and audit tables.

### `query_registry`
One row per query version. The `parameters` column is a JSON array describing each bind variable:

```json
[
  { "name": "customer_id", "type": "NUMBER",   "required": true,  "description": "..." },
  { "name": "status",      "type": "VARCHAR2", "required": true,  "allowed_values": ["OPEN", "CLOSED"] },
  { "name": "ssn",         "type": "VARCHAR2", "required": true,  "sensitive": true },
  { "name": "start_date",  "type": "DATE",     "required": false, "default": "SYSDATE - 30" }
]
```

Supported types: `NUMBER`, `VARCHAR2`, `DATE`, `TIMESTAMP`.

**Versioning:** never update a row in place. Set `is_active = 0` on the existing row and insert a new row with an incremented `version`. This preserves full history and makes rollback trivial.

### `query_audit_log`
Every `run_query` execution is recorded here asynchronously (fire-and-forget). The write never blocks the tool response; failures are swallowed and emitted to the file log as warnings.

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `ORACLE_USER` | — | Oracle username for the MCP server connection |
| `ORACLE_PASSWORD` | — | Oracle password |
| `ORACLE_DSN` | — | Oracle DSN (e.g. `host:port/service`) |
| `POOL_MIN` | `1` | Minimum connection pool size |
| `POOL_MAX` | `10` | Maximum connection pool size |
| `HARD_MAX_ROWS` | `2000` | Server-side ceiling on rows returned per call |
| `AUDIT_LOG_PATH` | `audit.log` | Path for the rotating JSON audit log |
| `ENVIRONMENT` | `local` | Controls parameter masking: `local` / `dev` / `sit` / `uat` / `prod` |

---

## Getting Started

### Prerequisites

- Python 3.13+
- Oracle Database (or Oracle Instant Client for thick mode)

### Setup

```bash
# Create and activate virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Oracle credentials

# Create Oracle objects
sqlplus user/pass@dsn @sql/ddl.sql
```

### Run the server

```bash
cd mcp_query_registry
python main.py
```

### Run the tests

```bash
pytest
```

Coverage report is written to `htmlcov/index.html`.

---

## Security Notes

- **No raw SQL from callers.** The server accepts only a query name and parameter values. All SQL originates exclusively from the trusted registry table.
- **Parameterised binding only.** Parameter values are bound via python-oracledb's named bind mechanism — never string-formatted into SQL.
- **Privilege separation.** The MCP server's Oracle user should hold `SELECT` on `query_registry`, `INSERT` on `query_audit_log`, and the minimum object privileges needed to run the registered queries. A separate privileged role manages registry administration.
- **Result set limits.** `max_rows` and `HARD_MAX_ROWS` cap result sets to prevent unbounded data exposure.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastmcp` | MCP server framework |
| `oracledb` | Oracle Database driver (python-oracledb) |
| `pydantic-settings` | Environment variable loading |
| `pydantic` | Data validation |
