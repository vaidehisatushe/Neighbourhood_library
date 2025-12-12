# server/db.py
import os
from psycopg2 import pool
from contextlib import contextmanager
from server.logger import get_logger

logger = get_logger('db')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/library')

_pool = None

def init_pool(minconn=1, maxconn=10):
    global _pool
    if _pool is None:
        logger.info('init_pool', extra={'minconn': minconn, 'maxconn': maxconn})
        _pool = pool.SimpleConnectionPool(minconn, maxconn, DATABASE_URL)
    return _pool

@contextmanager
def get_conn():
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)
