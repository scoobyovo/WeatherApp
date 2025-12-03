"""

dbcm
----

Provides the DBCM context manager for managing SQLite database connections.
"""


import logging
import sqlite3
from typing import Optional

LOGGER = logging.getLogger(__name__)


class DBCM:
    def __init__(self, db_path: str, timeout: float = 5.0, detect_types: int = 0,
                 isolation_level: Optional[str] = None):
        self.db_path = db_path
        self.timeout = timeout
        self.detect_types = detect_types
        self.isolation_level = isolation_level
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Cursor:
        try:
            self._conn = sqlite3.connect(
                self.db_path,
                timeout=self.timeout,
                detect_types=self.detect_types,
                isolation_level=self.isolation_level,
            )
            self._conn.row_factory = sqlite3.Row
            LOGGER.debug("Opened database connection to %s", self.db_path)
            return self._conn.cursor()
        except Exception as exc:
            LOGGER.exception("Failed to open database connection: %s", exc)
            raise
    
    def __exit__(self, exc_type, exc, exc_tb):
        try:
            if self._conn is None:
                return False

            if exc_type is None:
                self._conn.commit()
                LOGGER.debug("Commited for %s", self.db_path)
            else:
                self._conn.rollback()
                LOGGER.error("Rolled back for %s due to exception: %s", self.db_path, exc)
        finally:
            self._conn.close()
            LOGGER.debug("Database connection to %s closed", self.db_path)

        return False