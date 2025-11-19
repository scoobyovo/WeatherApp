import sqlite3
from typing import Optional

class DBCM:

    def __init__(self, db_path: str, timeout: float = 5.0, detect_types: int = 0,
                 isolation_level: Optional[str] = None):
        self.db_path = db_path
        self.timeout = timeout
        self.detect_types = detect_types
        self.isolation_level = isolation_level
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Cursor:
        self._conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            detect_types=self.detect_types,
            isolation_level=self.isolation_level,
        )
        self._conn.row_factory = sqlite3.Row
        return self._conn.cursor()
    
    def __exit__(self, exc_type, exc, exc_tb):
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()

        return False