from contextlib import closing

import pymysql
import pymysql.cursors
from dbutils.pooled_db import PooledDB

from .config import (
    DB_CONFIG,
    DB_POOL_MAX_CACHED,
    DB_POOL_MIN_CACHED,
    logger,
)


POOL = PooledDB(
    creator=pymysql,
    mincached=DB_POOL_MIN_CACHED,
    maxcached=DB_POOL_MAX_CACHED,
    blocking=True,
    cursorclass=pymysql.cursors.DictCursor,
    **DB_CONFIG,
)


def get_db_connection():
    return POOL.connection()


def ensure_db_schema():
    try:
        with closing(get_db_connection()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS api_requests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        method VARCHAR(10) NOT NULL,
                        url VARCHAR(500) NOT NULL,
                        status_code INT NOT NULL,
                        request_body TEXT,
                        response_body TEXT,
                        tags VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                _ensure_trace_index(cursor)
            connection.commit()
        logger.info("Table 'api_requests' exists or was created successfully")
    except pymysql.Error:
        logger.exception("Unable to ensure api_requests table exists")
        raise


INSERT_API_REQUEST_SQL = """
INSERT INTO api_requests (method, url, status_code, request_body, response_body, tags)
VALUES (%s, %s, %s, %s, %s, %s)
"""

SELECT_ALL_REQUESTS_SQL = """
SELECT id, method, url, status_code, request_body, response_body, tags,
       DATE_FORMAT(created_at, "%Y-%m-%d %H:%i:%s") as created_at
FROM api_requests
ORDER BY created_at DESC
"""

TRACE_INDEX_NAME = "idx_api_requests_created_at"
SELECT_REQUEST_BY_ID_SQL = """
SELECT id, method, url, status_code, request_body, response_body, tags,
       DATE_FORMAT(created_at, "%Y-%m-%d %H:%i:%s") as created_at
FROM api_requests
WHERE id = %s
"""
CREATE_TRACE_INDEX_SQL = f"""
CREATE INDEX {TRACE_INDEX_NAME}
ON api_requests (created_at)
"""


def _ensure_trace_index(cursor):
    try:
        cursor.execute(CREATE_TRACE_INDEX_SQL)
    except pymysql.err.InternalError as exc:
        if not exc.args or exc.args[0] != 1061:
            raise


def insert_api_request(method, url, status_code, request_body, response_body, tags):
    with closing(get_db_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                INSERT_API_REQUEST_SQL,
                (method, url, status_code, request_body, response_body, tags),
            )
            trace_id = cursor.lastrowid
        connection.commit()
    return trace_id


def fetch_api_requests():
    with closing(get_db_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_ALL_REQUESTS_SQL)
            return cursor.fetchall()


def fetch_api_request_by_id(request_id):
    with closing(get_db_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_REQUEST_BY_ID_SQL, (request_id,))
            return cursor.fetchone()
