"""
db_operations.py

Provides the DBOperations class, which handles all SQLite operations for
the weather database (initialize, save, fetch, purge, and export to CSV).
11/16/25
Param Kotak & Katie Sanders
"""


import logging
import sqlite3
import pandas as pd
from dbcm import DBCM
from scrape_weather import WeatherScraper

LOGGER = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weather (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_date DATETIME NOT NULL,
    location    TEXT     NOT NULL,
    min_temp    REAL,
    max_temp    REAL,
    avg_temp    REAL,
    CONSTRAINT uq_date_loc UNIQUE (sample_date, location)
);
"""

CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_weather_date ON weather(sample_date);"


class DBOperations():
    """
    Handles database operations such as initialization, saving, fetching, and purging weather data.
    """

    def __init__(self, db_path: str = "weather.sqlite"):
        """
        Initialize a new DBOperations object.

        Parameters
        ----------
        db_path : str
            Path or filename of the SQLite database. Defaults to "weather.sqlite".
        """

        self.db_path = db_path


    def initialize_db(self) -> None:
        """
        Create database tables and indexes if they do not already exist.

        This method should be called once at application startup, before any
        save or fetch operations are performed.

        Returns
        -------
        None
        """
        try:
            with DBCM(self.db_path) as cur:
                cur.execute(CREATE_TABLE_SQL)
                cur.execute(CREATE_INDEX_SQL)
            LOGGER.info("Database initialized at %s", self.db_path)
        except Exception as exc:
            LOGGER.exception("Error initializing database: %s", exc)
            raise


    def save_data(self, weather_dict, chunk_size: int = 200) -> int:
        """
        Insert scraped weather data into the database while preventing duplicates.

        Parameters
        ----------
        weather_dict : dict
            Dictionary of dictionaries containing weather data in the format
            { 'YYYY-MM-DD': {'Min': float, 'Max': float, 'Mean': float}, }
        chunk_size : int, optional
            Number of rows to insert per batch. Defaults to 200.

        Returns
        -------
        int
            Total number of newly inserted rows.
        """
        if not weather_dict:
            LOGGER.warning("save_data called with empty weather_dict.")
            return 0

        rows = []
        for date_str, temps in weather_dict.items():
            rows.append(
                (
                    date_str,
                    "Winnipeg, MB",
                    temps.get("Min"),
                    temps.get("Max"),
                    temps.get("Mean"),
                )
            )

        insert_sql = """
            INSERT OR IGNORE INTO weather (
                sample_date, location, min_temp, max_temp, avg_temp
            )
            VALUES (?, ?, ?, ?, ?);
        """

        total_inserted = 0
        total_rows = len(rows)

        try:
            with DBCM(self.db_path) as cur:
                for start in range(0, total_rows, chunk_size):
                    end = min(start + chunk_size, total_rows)
                    chunk = rows[start:end]

                    cur.executemany(insert_sql, chunk)
                    cur.execute("SELECT changes();")
                    inserted = cur.fetchone()[0]
                    total_inserted += inserted

                    print(f"Saved {end}/{total_rows} days...")

            LOGGER.info("Inserted %d new rows into the database.", total_inserted)
            return total_inserted

        except Exception as exc:
            LOGGER.exception("Error saving data to database: %s", exc)
            raise
    

    def fetch_data(self, start_date = None, end_date = None, location = None):
        """
        Retrieve weather data from the database that matches the parameters provided.

        Parameters
        ----------
        start_date : str
            Earliest date in YYYY-MM-DD format.
        end_date : str
            Latest date in YYYY-MM-DD format.
        location : str
            location filter.

        Returns
        -------
        tuple[tuple]
            Rows of data as tuples.
        """

        columns = ("sample_date", "min_temp", "max_temp", "avg_temp", "location")
        where = []
        params = []

        if start_date:
            where.append("sample_date >= ?")
            params.append(start_date)
        if end_date:
            where.append("sample_date <= ?")
            params.append(end_date)
        if location:
            where.append("location = ?")
            params.append(location)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        sql = f"SELECT {', '.join(columns)} FROM weather {where_sql} ORDER BY sample_date ASC;"

        try:
            with DBCM(self.db_path) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
            LOGGER.info("Fetched %d rows from database.", len(rows))
            return tuple(tuple(row[col] for col in columns) for row in rows)
        except Exception as exc:
            LOGGER.exception("Error fetching data from database: %s", exc)
            raise
    
    def purge_data(self):
        """
        Delete all weather records in the database, but does not remove the table itself.

        Returns
        -------
        int
            Number of rows deleted.
        """

        try:
            with DBCM(self.db_path) as cur:
                cur.execute("SELECT COUNT(*) FROM weather;")
                count_before = cur.fetchone()[0]
                cur.execute("DELETE FROM weather;")
            LOGGER.info("Purged %d rows from database.", count_before)
            return count_before
        except Exception as exc: 
            LOGGER.exception("Error purging data from database: %s", exc)
            raise
    

if __name__ == "__main__":
    pass
