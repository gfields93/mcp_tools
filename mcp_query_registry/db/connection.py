import oracledb
from config import settings

_pool: oracledb.ConnectionPool | None = None


def get_pool() -> oracledb.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=settings.oracle_user,
            password=settings.oracle_password,
            dsn=settings.oracle_dsn,
            min=settings.pool_min,
            max=settings.pool_max,
            increment=1,
        )
    return _pool


def get_connection():
    return get_pool().acquire()
