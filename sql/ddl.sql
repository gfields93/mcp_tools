-- =============================================================================
-- Oracle MCP Query Registry — DDL
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Query Registry
-- ---------------------------------------------------------------------------
CREATE SEQUENCE query_registry_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE query_registry (
    id          NUMBER         DEFAULT query_registry_seq.NEXTVAL PRIMARY KEY,
    name        VARCHAR2(200)  NOT NULL,
    description VARCHAR2(1000) NOT NULL,
    sql_text    CLOB           NOT NULL,
    parameters  CLOB           CHECK (parameters IS NULL OR parameters IS JSON),
    query_type  VARCHAR2(10)   DEFAULT 'SELECT'
                               CHECK (query_type IN ('SELECT', 'DML')),
    version     NUMBER         DEFAULT 1 NOT NULL,
    is_active   NUMBER(1)      DEFAULT 1 CHECK (is_active IN (0, 1)),
    tags        VARCHAR2(500),
    created_at  TIMESTAMP      DEFAULT SYSTIMESTAMP,
    updated_at  TIMESTAMP      DEFAULT SYSTIMESTAMP,
    CONSTRAINT uq_name_version UNIQUE (name, version)
);

-- Fast lookup for active queries by name
CREATE INDEX idx_qr_name_active ON query_registry (name, is_active);

-- ---------------------------------------------------------------------------
-- Audit Log
-- ---------------------------------------------------------------------------
CREATE SEQUENCE query_audit_log_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE query_audit_log (
    id             NUMBER        DEFAULT query_audit_log_seq.NEXTVAL PRIMARY KEY,
    query_name     VARCHAR2(200) NOT NULL,
    query_version  NUMBER        NOT NULL,
    executed_at    TIMESTAMP     DEFAULT SYSTIMESTAMP NOT NULL,
    parameters     CLOB          CHECK (parameters IS NULL OR parameters IS JSON),
    status         VARCHAR2(10)  NOT NULL CHECK (status IN ('SUCCESS', 'ERROR')),
    error          CLOB,
    row_count      NUMBER        DEFAULT 0,
    duration_ms    NUMBER,
    caller_id      VARCHAR2(500)
);

-- Support time-range queries and per-query history lookups
CREATE INDEX idx_aql_executed_at ON query_audit_log (executed_at);
CREATE INDEX idx_aql_query_name  ON query_audit_log (query_name, executed_at);
