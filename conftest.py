"""
Root conftest — runs before any test file is imported.

Sets sys.path and required environment variables so that project modules
(config, audit, db, tools, validation) are importable and Settings() can
be constructed without a real .env file or Oracle connection.
"""
import os
import sys
import tempfile

# Make mcp_query_registry/ the import root so project-internal imports work
# (e.g. `from config import settings`, `from db.connection import ...`).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp_query_registry"))

# Provide all required env vars BEFORE any project module is imported.
# Using os.environ[] (not setdefault) ensures test values always win.
os.environ["ORACLE_USER"] = "test_user"
os.environ["ORACLE_PASSWORD"] = "test_password"
os.environ["ORACLE_DSN"] = "localhost:1521/TESTDB"
os.environ["ENVIRONMENT"] = "local"
os.environ["HARD_MAX_ROWS"] = "2000"

# audit/logger.py creates a TimedRotatingFileHandler at import time;
# point it at a throw-away temp file so tests don't touch the filesystem.
_tmp = tempfile.NamedTemporaryFile(suffix=".log", delete=False)
_tmp.close()
os.environ["AUDIT_LOG_PATH"] = _tmp.name
