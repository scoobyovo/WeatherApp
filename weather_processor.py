# from scrape_weather import WeatherScraper
# from db_operations import DBOperations
# import re
# import logging
# """
# Katie Sanders and Param Kotak.
# Processes user input and diplays weather data based on input
# 2025-11-19

# This module defines the WeatherProcessor class, which handles user interaction
# in the console. It allows the user to initialize the database and then enter
# date ranges that will later be used for displaying or plotting weather data.
# """

# LOGGER = logging.getLogger(__name__)

# def configure_logging():
#     logging.basicConfig(
#         filename="weatherapp.log",
#         level=logging.INFO,
#         format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
#     )
#     LOGGER.info("Logging configured for weather_processor.")

# #adding a comment to commit
# class WeatherProcessor:
    
#     def __init__(self):
#         self.starting_date = None
#         self.end_date = None
#         self.user_input = input("Welcome to Weather Processor!\n---" \
#         "Would you like to download all data including latest?\ny/n: ")
#         if self.user_input == "y":
#             db = DBOperations()
#             db.initialize_db()
#         self.program()

#     def program(self):
#         while(self.user_input != 'q'):
#             if self.starting_date == None:
#                 self.enter_date()
#             self.user_input = input("Enter q to quit or d to update the date: ")
#             if self.user_input == 'd':
#                 self.enter_date()

#         print("Quitting...")
#         self.end_date = None
#         self.starting_date = None
#         self.user_input = None

#     def enter_date(self):
#         while(True):
#             self.user_input = input("Enter year date ranges for a box plot (ex: 2020-2025, yyyy-yyyy)]\nor enter a year and month" \
#                     "for a line plot (ex: 2024-11, yyyy-mm): ")

#             year_range_pattern = r"^\d{4}-\d{4}$"
#             year_month_pattern = r"^\d{4}-\d{2}$"

#             if re.match(year_range_pattern, self.user_input):
#                 self.user_input = self.user_input.split("-")
#                 self.starting_date = self.user_input[0]
#                 self.end_date = self.user_input[1]
#                 #year box plot
#                 break
#             elif re.match(year_month_pattern, self.user_input):
#                 #month line plot!
#                 break
#             else:
#                 print(f"{self.user_input} is not one of the valid date options. Please try again.")

            
# if __name__ == "__main__":
#     wp = WeatherProcessor()

"""
weather_processor
=================

Entry point / controller for the WeatherApp.

This module defines the WeatherProcessor class, which handles user interaction
in the console. It allows the user to initialize the database and then enter
date ranges that will later be used for displaying or plotting weather data.
"""

import logging
import re

from db_operations import DBOperations
from plot_operations import PlotOperations

LOGGER = logging.getLogger(__name__)


def configure_logging():
    """
    Configure application-wide logging.

    Logging output is written to the file 'weatherapp.log' in the current
    working directory.

    Returns
    -------
    None
    """
    logging.basicConfig(
        filename="weatherapp.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    LOGGER.info("Logging configured for weather_processor.")


class WeatherProcessor:
    """
    Manage user interaction for the WeatherApp.

    The WeatherProcessor class prompts the user to optionally initialize the
    database, and then repeatedly asks for date input until the user decides
    to quit the application.
    """

    def __init__(self, db_path="weather.sqlite"):
        """
        Initialize a new WeatherProcessor instance.

        Parameters
        ----------
        db_path : str, optional
            Path to the SQLite database file. Defaults to 'weather.sqlite'.
        """
        self.db_path = db_path
        self.starting_date = None
        self.end_date = None
        self._running = True

    # --------------------------------------------------------------------- #

    def run(self):
        """
        Run the main interactive loop of the program.

        The user is first asked whether they would like to initialize the
        database (for example, before downloading or processing weather data).
        After that, the program repeatedly prompts the user to enter date
        ranges until the user chooses to quit.

        Returns
        -------
        None
        """
        LOGGER.info("WeatherProcessor started.")
        self._initial_prompt()

        while self._running:
            if self.starting_date is None and self.end_date is None:
                self.enter_date()

            try:
                user_input = input(
                    "Enter 'q' to quit or 'd' to update the date: "
                ).strip().lower()
            except (EOFError, KeyboardInterrupt):
                LOGGER.info("User aborted from main loop.")
                break

            if user_input == "q":
                LOGGER.info("User chose to quit.")
                self._running = False
            elif user_input == "d":
                self.enter_date()
            else:
                print("Unknown option. Please enter 'q' or 'd'.")
                LOGGER.warning("Invalid main-loop option entered: %s", user_input)

        print("Quitting...")
        LOGGER.info("WeatherProcessor finished. start=%s end=%s",
                    self.starting_date, self.end_date)

        # Reset internal state (not strictly necessary but keeps state clean)
        self.starting_date = None
        self.end_date = None

    # --------------------------------------------------------------------- #

    def _initial_prompt(self):
        """
        Ask the user if the database should be initialized.

        If the user enters 'y', the database is initialized using DBOperations.
        Any database errors are logged and surfaced to the user.

        Returns
        -------
        None
        """
        try:
            user_input = input(
                "Welcome to Weather Processor!\n"
                "--- Would you like to initialize the database "
                "and download all data including the latest? (y/n): "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            LOGGER.info("User aborted at initial prompt.")
            self._running = False
            return

        if user_input == "y":
            LOGGER.info("User chose to initialize the database.")
            try:
                db = DBOperations(self.db_path)
                db.initialize_db()
                print("Database initialized.")
            except Exception as exc:  # pylint: disable=broad-except
                LOGGER.exception("Error initializing database: %s", exc)
                print("Error initializing the database. See weatherapp.log for details.")
                # You may choose to stop the program entirely if this fails.
        elif user_input == "n":
            LOGGER.info("User skipped database initialization.")
        else:
            LOGGER.warning("Invalid initial choice: %s", user_input)
            print("Invalid choice. Skipping database initialization.")

    # --------------------------------------------------------------------- #

    def enter_date(self):
        """
        Prompt the user to enter date information.

        The user may enter:
        - a year range for a box plot (e.g., '2020-2025'), OR
        - a specific year and month for a line plot (e.g., '2024-11').

        Valid input examples
        --------------------
        2020-2025   -> sets starting_date='2020', end_date='2025'
        2024-11     -> sets starting_date='2024-11', end_date=None

        Returns
        -------
        None
        """
        year_range_pattern = r"^\d{4}-\d{4}$"
        year_month_pattern = r"^\d{4}-\d{2}$"

        plotter = PlotOperations(self.db_path)

        while True:
            try:
                user_input = input(
                    "Enter year date ranges for a box plot "
                    "(e.g., 2020-2025, yyyy-yyyy)\n"
                    "OR enter a year and month for a line plot "
                    "(e.g., 2024-11, yyyy-mm): "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                LOGGER.info("User aborted while entering date.")
                self._running = False
                return

            if re.match(year_range_pattern, user_input):
                start_year_str, end_year_str = user_input.split("-")
                start_year = int(start_year_str)
                end_year = int(end_year_str)

                self.starting_date = start_year
                self.end_date = end_year

                LOGGER.info("Year range selected: %s to %s",
                            self.starting_date, self.end_date)
                print(f"Year range selected: {self.starting_date}–{self.end_date}")

                try:
                    plotter.plot_boxplot(start_year, end_year)
                except Exception as exc:  # pylint: disable=broad-except
                    LOGGER.exception("Error generating boxplot: %s", exc)
                    print("Error generating boxplot. See weatherapp.log for details")
                break

            if re.match(year_month_pattern, user_input):
                year_str, month_str = user_input.split("-")
                year = int(year_str)
                month = int(month_str)

                self.starting_date = user_input
                self.end_date = None

                LOGGER.info("Year-month selected: %s", self.starting_date)
                print(f"Year and month selected: {year}-{month:02d}")

                try:
                    plotter.plot_month_line(year, month)
                except Exception as exc:
                    LOGGER.exception("Error generating line plot: %s", exc)
                    print("Error generating line plot. See weatherapp.log for details.")

                break

            print(
                f"'{user_input}' is not a valid date option. "
                "Please try again using 'yyyy-yyyy' or 'yyyy-mm'."
            )
            LOGGER.warning("Invalid date format entered: %s", user_input)


def main():
    """
    Configure logging and start the WeatherProcessor interactive loop.

    Returns
    -------
    None
    """
    configure_logging()
    processor = WeatherProcessor()
    processor.run()


if __name__ == "__main__":
    main()
