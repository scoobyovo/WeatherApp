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
    """
    Context manager for SQLite database connections.

    Opens a connection on entry and returns a cursor. On exit, commits the
    transaction if no exception occurred, otherwise rolls back. The connection
    is always closed.
    """
    def __init__(self, db_path: str, timeout: float = 5.0, detect_types: int = 0,
                 isolation_level: Optional[str] = None):
        """
        Initialize a DBCM instance.

        Parameters
        ----------
        db_path : str
            Path to the SQLite database file.
        timeout : float, optional
            Connection timeout in seconds. Defaults to 5.0.
        detect_types : int, optional
            sqlite3 detect_types flag. Defaults to 0.
        isolation_level : str, optional
            sqlite3 isolation level. Defaults to None.
        """
        self.db_path = db_path
        self.timeout = timeout
        self.detect_types = detect_types
        self.isolation_level = isolation_level
        self._conn: Optional[sqlite3.Connection] = None


    def __enter__(self) -> sqlite3.Cursor:
        """
        Open a SQLite connection and return a cursor.

        Returns
        -------
        sqlite3.Cursor
            A cursor object with row_factory set to sqlite3.Row.
        """
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
        """
        Commit the transaction on success, roll back on error, and close
        the database connection.

        Parameters
        ----------
        exc_type, exc, exc_tb
            Exception information, if an exception occurred inside the
            context block.

        Returns
        -------
        bool
            Always False so that exceptions are not suppressed.
        """
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