import sqlite3
import pandas as pd
#from typing import Dict, Iterable, List, Optional, Tuple
from dbcm import DBCM
from scrape_weather import WeatherScraper

"""
11/16/25 
Param Kotak & Katie Sanders

Database Operations Files
"""

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

class DBOPerations():

    """
    Handles database operations
    """

    def __init__(self, db_path: str = "weather.sqlite"):

        """
        Initialize a new DBOperations object.

        Parameters
        ----------
        db_path 
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

        with DBCM(self.db_path) as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(CREATE_INDEX_SQL)

    def save_data(self, weather_dict):

        """
        Insert scraped weather data into the database while preventing duplicates.
        """
        #weather_dict = WeatherScraper.scrape_data()
        if not weather_dict:
            return 0
        
        rows = []
        for date_str, temps in weather_dict.items():
            rows.append((
                date_str,
                "Winnipeg, MB",
                temps.get("Min"),
                temps.get("Max"),
                temps.get("Mean"),
            ))

        insert_sql = """
            INSERT OR IGNORE INTO weather (sample_date, location, min_temp, max_temp, avg_temp)
            VALUES (?, ?, ?, ?, ?)
        """

        with DBCM(self.db_path) as cur:
            cur.executemany(insert_sql, rows)
            cur.execute("SELECT changes();")
            inserted = cur.fetchone()[0]

        return inserted
    
    def fetch_data(self, start_date = None, end_date = None, location = None):

        """
        Retrieve weather data from the database that matches the parameters provided.
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

        with DBCM(self.db_path) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return tuple(tuple(row[col] for col in columns) for row in rows)
    
    def purge_data(self):

        """
        Delete all weather records in the database, but does not remove the table itself.
        """

        with DBCM(self.db_path) as cur:
            cur.execute("SELECT COUNT(*) FROM weather;")
            count_before = cur.fetchone()[0]
            cur.execute("DELETE FROM weather;")
        return count_before

    # def create_csv(self, csv_path: str = "weather_export.csv"):
    #     conn = sqlite3.connect(self.db_path)

    #     query = """
    #         SELECT id, sample_date, location, min_temp, max_temp, avg_temp
    #         FROM weather
    #         ORDER BY sample_date ASC
    #     """

    #     df = pd.read_sql_query(query, conn)
    #     df.to_csv(csv_path, index=False)

    #     conn.close()
    #     return csv_path
    

if __name__ == "__main__":

    scraper = WeatherScraper()
    weather_dict = scraper.scrape_data()

    print(f"Scraped {len(weather_dict)} days of data")

    db = DBOPerations()
    db.initialize_db()

    inserted = db.save_data(weather_dict)

    print(f"Inserted {inserted} new rows into the database.")

    csv_path = db.create_csv()
    print(f"CSV exported to {csv_path}")

    #print("Database created at:", db.db_path)
    