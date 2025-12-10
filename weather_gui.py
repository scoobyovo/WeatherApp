"""
weather_gui.py
--------------

Provides the graphical user interface (GUI) for the WeatherApp project.
This module uses Tkinter to allow users to:

- Download and update historical weather data from Environment Canada.
- Generate monthly line plots using matplotlib.
- Generate year-range box plots using matplotlib.
- View status updates and error messages in a responsive interface.

The GUI performs long-running tasks (scraping and saving) in background
threads so that the window remains responsive. All actions are logged
to weatherapp.log.

Authors:
    Param Kotak
    Katie Sanders
Date:
    2025-12-07
"""

import logging
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from scrape_weather import WeatherScraper
from db_operations import DBOperations
from plot_operations import PlotOperations


logging.basicConfig(
    filename="weatherapp.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

LOGGER = logging.getLogger(__name__)


class WeatherAppGUI(tk.Tk):
    """Main Tkinter window for the WeatherApp."""

    YEAR_MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")
    YEAR_RANGE_PATTERN = re.compile(r"^\d{4}-\d{4}$")

    def __init__(self) -> None:
        """
        Initialize the WeatherApp GUI window.

        This constructor:
        - Creates the Tkinter root window.
        - Initializes database and plotting helper classes.
        - Sets up StringVar fields for user input (month and year range).
        - Builds all UI widgets and configures resizing.
        - Prepares threading state for background downloads.
        """
        super().__init__()

        self.title("WeatherApp – Winnipeg Historical Weather")
        self.minsize(600, 300)

        self.db = DBOperations()
        self.plot_ops = PlotOperations()

        self._download_thread: threading.Thread | None = None

        self.year_month_var = tk.StringVar(value="2025-12")
        self.year_range_var = tk.StringVar(value="2020-2025")
        self.status_var = tk.StringVar(value="Ready.")

        self._build_layout()
        self._configure_resizing()

        LOGGER.info("WeatherApp GUI initialized.")


    def _build_layout(self) -> None:
        """Create and place all widgets in the main window."""
        main_frame = ttk.Frame(self, padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")

        actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding=12)
        actions_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        plot_frame = ttk.LabelFrame(main_frame, text="Plot Options", padding=12)
        plot_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        status_bar = ttk.Label(
            self, textvariable=self.status_var, relief="sunken", anchor="w", padding=(8, 2)
        )
        status_bar.grid(row=1, column=0, sticky="ew")

        download_btn = ttk.Button(
            actions_frame,
            text="Download / Update Weather Data",
            command=self.on_download_click,
        )
        download_btn.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        instructions = (
            "Tips:\n"
            "- Use 'Download / Update' first to make sure your data is up to date.\n"
            "- Then use the plot options on the right to visualize the data."
        )
        instr_label = ttk.Label(actions_frame, text=instructions, justify="left")
        instr_label.grid(row=1, column=0, sticky="nsew")

        line_label = ttk.Label(plot_frame, text="Monthly Line Plot (YYYY-MM):")
        line_label.grid(row=0, column=0, sticky="w")

        line_entry = ttk.Entry(plot_frame, textvariable=self.year_month_var, width=12)
        line_entry.grid(row=1, column=0, sticky="w")

        line_btn = ttk.Button(
            plot_frame,
            text="Generate Line Plot",
            command=self.on_line_plot_click,
        )
        line_btn.grid(row=1, column=1, sticky="w", padx=(8, 0))

        ttk.Separator(plot_frame, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=8
        )

        box_label = ttk.Label(plot_frame, text="Year Range Box Plot (YYYY-YYYY):")
        box_label.grid(row=3, column=0, sticky="w")

        box_entry = ttk.Entry(plot_frame, textvariable=self.year_range_var, width=12)
        box_entry.grid(row=4, column=0, sticky="w")

        box_btn = ttk.Button(
            plot_frame,
            text="Generate Box Plot",
            command=self.on_box_plot_click,
        )
        box_btn.grid(row=4, column=1, sticky="w", padx=(8, 0))


    def _configure_resizing(self) -> None:
        """Configure grid weights so widgets scale properly when resized."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main = self.children[list(self.children.keys())[0]]
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)


    def _set_status(self, text: str) -> None:
        """
        Thread-safe helper to update the status bar text.

        Parameters
        ----------
        text : str
            Status message to display at the bottom of the window.
        """
        def _update():
            self.status_var.set(text)

        self.after(0, _update)


    def _show_error(self, title: str, message: str) -> None:
        """
        Thread-safe helper to show an error dialog.

        Parameters
        ----------
        title : str
            Title of the error dialog.
        message : str
            Error message to display.
        """
        def _popup():
            messagebox.showerror(title, message)

        self.after(0, _popup)


    def on_download_click(self) -> None:
        """
        Handler for the 'Download / Update Weather Data' button.

        Starts a background thread that:
        - initializes the database,
        - scrapes weather data,
        - saves new rows into the SQLite database.

        If a download is already in progress, the user is informed and no
        new thread is started.
        """
        try:
            if self._download_thread and self._download_thread.is_alive():
                messagebox.showinfo(
                    "WeatherApp",
                    "A download is already in progress. Please wait for it to finish.",
                )
                return

            self._set_status("Starting download…")
            self._download_thread = threading.Thread(
                target=self._download_worker, daemon=True
            )
            self._download_thread.start()

        except Exception as exc:
            LOGGER.exception("Unexpected error in on_download_click: %s", exc)
            self._set_status("An unexpected error occurred.")
            self._show_error("Download Error", f"Unexpected error: {exc}")


    def _download_worker(self) -> None:
        """
        Background worker function that performs the full download.

        This method runs in a separate thread and:
        - initializes the database (if needed),
        - scrapes data from Environment Canada,
        - saves the data to SQLite using DBOperations.

        Status updates are shown in the GUI, and failures are logged and
        displayed as error dialogs.
        """
        LOGGER.info("GUI download initiated.")
        try:
            self._set_status("Initializing database (if needed)…")
            self.db.initialize_db()

            self._set_status("Scraping data from Environment Canada…")
            scraper = WeatherScraper()
            weather_dict = scraper.scrape_data()
            days = len(weather_dict)
            LOGGER.info("GUI scraping finished: %d days scraped.", days)

            self._set_status(f"Saving {days} days into the database…")
            inserted = self.db.save_data(weather_dict, progress_callback=self._set_status)
            LOGGER.info("GUI save complete: %d new rows inserted.", inserted)

            self._set_status(
                f"Download complete. {inserted} new rows added. Ready."
            )
        except Exception as exc:
            LOGGER.exception("Error in GUI download worker: %s", exc)
            self._set_status("An error occurred during download.")
            self._show_error("Download Error", str(exc))


    def on_line_plot_click(self) -> None:
        """Handler for 'Generate Line Plot' button."""
        text = self.year_month_var.get().strip()
        if not self.YEAR_MONTH_PATTERN.match(text):
            messagebox.showwarning(
                "Invalid Input",
                "Please enter a month in the format YYYY-MM (e.g., 2025-12).",
            )
            return

        year_str, month_str = text.split("-")
        year = int(year_str)
        month = int(month_str)

        LOGGER.info("GUI requested line plot for %d-%02d.", year, month)
        self._set_status(f"Generating line plot for {year}-{month:02d}…")

        try:
            self.plot_ops.plot_month_line(year, month)
            self._set_status("Line plot generated. Ready.")
        except Exception as exc:
            LOGGER.exception("Error generating line plot from GUI: %s", exc)
            self._set_status("Error generating line plot.")
            self._show_error("Plot Error", str(exc))


    def on_box_plot_click(self) -> None:
        """Handler for 'Generate Box Plot' button."""
        text = self.year_range_var.get().strip()
        if not self.YEAR_RANGE_PATTERN.match(text):
            messagebox.showwarning(
                "Invalid Input",
                "Please enter a year range in the format YYYY-YYYY (e.g., 2020-2025).",
            )
            return

        start_str, end_str = text.split("-")
        start_year = int(start_str)
        end_year = int(end_str)

        LOGGER.info("GUI requested box plot for %d–%d.", start_year, end_year)
        self._set_status(f"Generating box plot for {start_year}–{end_year}…")

        try:
            self.plot_ops.plot_boxplot(start_year, end_year)
            self._set_status("Box plot generated. Ready.")
        except Exception as exc:
            LOGGER.exception("Error generating box plot from GUI: %s", exc)
            self._set_status("Error generating box plot.")
            self._show_error("Plot Error", str(exc))


def main() -> None:
    """Entry point for running the GUI."""
    app = WeatherAppGUI()
    app.mainloop()




if __name__ == "__main__":
    main()