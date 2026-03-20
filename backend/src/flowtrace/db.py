from contextlib import closing

import pymysql
import pymysql.cursors

from .config import DB_CONFIG, logger


def get_db_connection():
    connection_kwargs = dict(DB_CONFIG)
    connection_kwargs["cursorclass"] = pymysql.cursors.DictCursor
    return pymysql.connect(**connection_kwargs)


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
            connection.commit()
        logger.info("Table 'api_requests' exists or was created successfully")
    except pymysql.Error:
        logger.exception("Unable to ensure api_requests table exists")
        raise
