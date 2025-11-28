import matplotlib.pyplot as plt
import sqlite3
import pandas as pd

class PlotOperations():
    def __init__(self, db_path: str = "weather.sqlite"):
        self.db_path = db_path

    def _load_data(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("""
            SELECT sample_date, avg_temp
            FROM weather
            WHERE avg_temp IS NOT NULL                   
        """, conn)
        conn.close()

        df["avg_temp"] = pd.to_numeric(df["avg_temp"], errors="coerce")

        df["sample_date"] = pd.to_datetime(df["sample_date"])
        df["year"] = df["sample_date"].dt.year
        df["month"] = df["sample_date"].dt.month
        df["day"] = df["sample_date"].dt.day

        return df
    
    def plot_boxplot(self, start_year, end_year):
        df = self._load_data()

        df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]

        if df.empty:
            print(f"No data found from {start_year} to {end_year}.")
            return
        
        weather_data = {
            month: df[df["month"] == month]["avg_temp"].dropna().tolist()
            for month in range(1, 13)
        }

        data_in_order = []
        labels = []
        for month in range(1, 13):
            vals = weather_data[month]
            if vals:
                data_in_order.append(vals)
                labels.append(month)

        if not data_in_order:
            print(f"No useable avg_temp values between {start_year} and {end_year}.")
            return
        
        plt.figure(figsize=(10, 6))
        plt.boxplot(data_in_order, tick_labels=labels)

        plt.title(f"Monthly temperature Distribution for: {start_year} to {end_year}")
        plt.xlabel("Month")
        plt.ylabel("Mean Temperature (Celsius)")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_month_line(self, year: int, month: int):
        df = self._load_data()

        subset = df[(df["year"] == year) & (df["month"] == month)]

        if subset.empty:
            print(f"No data found for {year}-{month:02d}.")
            return

        plt.figure(figsize=(10, 5))
        plt.plot(subset["day"], subset["avg_temp"], marker='o')

        plt.title(f"Mean Daily Temperature Distribution for: {year}-{month:02d}")
        plt.xlabel("Day of Month")
        plt.ylabel("Mean Temperature (Celsius)")
        plt.grid(True)
        plt.tight_layout()
        plt.show()




if __name__ == "__main__":
    plotter = PlotOperations()

    plotter.plot_boxplot(2020, 2025)
    plotter.plot_month_line(2025, 11)

