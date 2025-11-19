# import sqlite3

# conn = sqlite3.connect("weather.sqlite")
# cur = conn.cursor()

# cur.execute("SELECT COUNT(*) FROM weather;")
# print("Row count:", cur.fetchone()[0])

# cur.execute("SELECT * FROM weather LIMIT 5;")
# for row in cur.fetchall():
#     print(row)

# conn.close()

import sqlite3

conn = sqlite3.connect("weather.sqlite")
cur = conn.cursor()

cur.execute("""
    SELECT 
        substr(sample_date, 1, 4) AS year,
        substr(sample_date, 6, 2) AS month,
        COUNT(*)
    FROM weather
    WHERE CAST(substr(sample_date, 1, 4) AS INTEGER) BETWEEN 2020 AND 2025
    GROUP BY year, month
    ORDER BY year, month;
""")

for row in cur.fetchall():
    print(row)

conn.close()