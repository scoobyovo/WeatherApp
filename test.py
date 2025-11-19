import sqlite3

conn = sqlite3.connect("weather.sqlite")
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM weather;")
print("Row count:", cur.fetchone()[0])

cur.execute("SELECT * FROM weather LIMIT 5;")
for row in cur.fetchall():
    print(row)

conn.close()