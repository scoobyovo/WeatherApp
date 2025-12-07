"""
Katie Sanders and Param Kotak.
Processes user input and displays weather data based on input.
2025-11-19

This module defines the WeatherProcessor class, which serves as the main
controller for the WeatherApp. It provides a command-line interface for the 
user to download weather data, generate plots, and exit the program.
"""


from scrape_weather import WeatherScraper
from db_operations import DBOperations
from plot_operations import PlotOperations
import logging
import re


LOGGER = logging.getLogger(__name__)


def configure_logging() -> None:
    """    
    Configure application-wide logging for WeatherApp.

    Logging output is written to 'weatherapp.log' in the working directory.
    This function sets formatting, log levels, and registers a module logger.
    """
    logging.basicConfig(
        filename="weatherapp.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    LOGGER.info("Logging configured for weather processor.")


class WeatherProcessor:
    """
    Main menu controller for the WeatherApp.

    This class presents the user with a text-based menu and allows them to:
    - initialize the database and download weather data
    - generate monthly line plots
    - generate yearly box plots
    - quit the application

    All menu actions are logged to weatherapp.log for debugging and grading.
    """

    def __init__(self):
        """
        Initialize the WeatherProcessor application.

        This constructor sets up:
        - the PlotOperations instance used for generating plots,
        - default values for date fields,
        - the DBOperations instance for database interactions,
        - the command-menu mapping for user actions.

        After initializing internal state, it immediately launches the
        main program loop by calling self.program().
        """
        self.plot_op = PlotOperations()
        self.starting_date = None
        self.end_date = None
        self.db = DBOperations()
        self.options = {
            "1": self.download_all_data,
            "2": self.generate_line,
            "3": self.generate_box,
            "4": None,
        }

        LOGGER.info("Weather Processor initialized.")
        self.program()

    def program(self):
        """
        Run the main command-line menu loop.

        This method repeatedly displays a menu of options:
        1. Initialize database and download latest weather data.
        2. Generate a month-based line plot.
        3. Generate a year-based box plot.
        4. Quit the program.

        The user's selection is validated and dispatched to the corresponding
        handler function stored within `self.options`. Any unexpected errors are 
        logged to weatherapp.log.
        """
        LOGGER.info("Program loop started.")

        while True:
            print(
                "\nWelcome to Weather Processor!\n"
                "--- cmds ---\n"
                "1 - Download all latest weather data.\n"
                "2 - Generate a line plot (month)\n"
                "3 - Generate a box plot (year)\n"
                "4 - Quit"
            )

            try:
                user_input = input("Enter your choice (1-4): ").strip()
            except (EOFError, KeyboardInterrupt):
                LOGGER.info("User aborted from the program.")
                break

            if user_input == "4":
                LOGGER.info("User chose to quit from main menu.")
                break

            action = self.options.get(user_input)
            if action is None:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
                LOGGER.warning("Invalid menu choice: %s", user_input)
                continue

            try:
                action()
            except Exception as exc:
                LOGGER.exception("Error running menu option %s: %s", user_input, exc)
                print("An error occurred. See weatherapp.log for details.")


        print("Quitting...")
        self.end_date = None
        self.starting_date = None

    def download_all_data(self):
        """
        Initialize the database (if needed), scrape all available weather data,
        and save new records into the database.

        Existing rows are not duplicated because DBOperations.save_data()
        uses INSERT OR IGNORE. The number of newly inserted rows is printed
        to the console and logged to weatherapp.log.
        """
        LOGGER.info("Download of all latest weather data requested.")
        print("[DEBUG] entered download_all_data")


        try:
            print("[DEBUG] initializing DB")
            print("Initializing database (if needed)...")
            self.db.initialize_db()
            print("Database ready. Scraping data from Environment Canada...")
            LOGGER.info("Database initialized in option 1.")
        except Exception as exc:
            LOGGER.exception("Error initializing database in option 1: %s", exc)
            print("Error initializing the database. See weatherapp.log for details.")
            print("[DEBUG] leaving download_all_data early (DB error)")
            return


        try:
            print("[DEBUG] about to call scrape_data()")
            scraper = WeatherScraper()
            weather_dict = scraper.scrape_data()
            print(f"[DEBUG] scrape_data() returned {len(weather_dict)} days")
            LOGGER.info("Scraping finished. %d days scraped.", len(weather_dict))
        except Exception as exc:
            LOGGER.exception("Error scraping weather data in option 1: %s", exc)
            print("Error scraping weather data. See weatherapp.log for details.")
            print("[DEBUG] leaving download_all_data early (scrape error)")
            return


        try:
            print("[DEBUG] about to call save_data()")
            inserted = self.db.save_data(weather_dict)
            print(f"Download complete. {inserted} new rows added to the database.")
            LOGGER.info("Download complete. %d new rows inserted.", inserted)
            print("[DEBUG] save_data() finished")
        except Exception as exc:
            LOGGER.exception("Error saving scraped data in option 1: %s", exc)
            print("Error saving data to the database. See weatherapp.log for details.")
            print("[DEBUG] leaving download_all_data early (save error)")
            return

        print("[DEBUG] leaving download_all_data normally, returning to menu")


    def generate_box(self):
        """
        Prompt the user for a year range and generate a yearly box plot.

        Expected input format:
        'YYYY-YYYY'  (e.g., '2020-2025')

        The method validates the input using a regular expression, parses the start
        and end year, and calls PlotOperations.plot_boxplot(). If the user enters
        an invalid format or aborts the input, the function logs the event and 
        terminates gracefully.
        """
        LOGGER.info("Box-plot generation requested.")
        year_range_pattern = r"^\d{4}-\d{4}$"

        try:
            user_input = input(
                "Enter year date ranges for a box plot "
                "(ex: 2020-2025, yyyy-yyyy): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            LOGGER.info("User aborted year-range input for box plot.")
            return

        if re.match(year_range_pattern, user_input):
            start_str, end_str = user_input.split("-")
            self.starting_date = start_str
            self.end_date = end_str

            try:
                start_year = int(start_str)
                end_year = int(end_str)
                self.plot_op.plot_boxplot(start_year, end_year)
                LOGGER.info("Box plot generated for %s–%s.", start_year, end_year)
            except Exception as exc:
                LOGGER.exception("Error generating box plot: %s", exc)
                print("Error generating box plot. See weatherapp.log for details.")
        else:
            print(f"{user_input} was not formatted correctly. Please try again.")
            LOGGER.warning("Invalid year range format: %s", user_input)


    def generate_line(self):
        """
        Prompt the user for a year-month pair and generate a line plot.

        Expected input format:
            'YYYY-MM'  (e.g., '2024-11')

        he method validates the input using a regular expression, extracts the
        year and month, and calls PlotOperations.plot_month_line(). Invalid input
        or interrupted input is logged and handled cleanly.
        """
        LOGGER.info("Line-plot generation requested.")
        year_month_pattern = r"^\d{4}-\d{2}$"

        try:
            user_input = input(
                "Enter year and month for a line plot "
                "(ex: 2024-11, yyyy-mm): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            LOGGER.info("User aborted program while entering year-month.")
            return

        if re.match(year_month_pattern, user_input):
            year_str, month_str = user_input.split("-")
            self.starting_date = user_input
            self.end_date = None

            try:
                year = int(year_str)
                month = int(month_str)
                self.plot_op.plot_month_line(year, month)
                LOGGER.info("Line plot generated for %s-%02d.", year, month)
            except Exception as exc:
                LOGGER.exception("Error generating line plot: %s", exc)
                print("Error generating line plot. See weatherapp.log for details.")
        else:
            print(f"{user_input} was not formatted correctly. Please try again.")
            LOGGER.warning("Invalid year-month format: %s", user_input)




if __name__ == "__main__":

    configure_logging()
    WeatherProcessor()