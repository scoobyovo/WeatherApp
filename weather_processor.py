from scrape_weather import WeatherScraper
from db_operations import DBOPerations
import re
"""
Katie Sanders and Param Kotak.
Processes user input and diplays weather data based on input
2025-11-19
"""
#adding a comment to commit
class WeatherProcessor:
    
    def __init__(self):
        self.starting_date = None
        self.end_date = None
        self.user_input = input("Welcome to Weather Processor!\n---" \
        "Would you like to download all data including latest?\ny/n: ")
        if self.user_input == "y":
            DBOPerations.initialize_db(self)
        self.program()

    def program(self):
        while(self.user_input != 'q'):
            if self.starting_date == None:
                self.enter_date()
            self.user_input = input("Enter q to quit or d to update the date: ")
            if self.user_input == 'd':
                self.enter_date()

        print("Quitting...")
        self.end_date = None
        self.starting_date = None
        self.user_input = None

    def enter_date(self):
        while(True):
            self.user_input = input("Enter year date ranges for a box plot (ex: 2020-2025, yyyy-yyyy)]\nor enter a year and month" \
                    "for a line plot (ex: 2024-11, yyyy-mm): ")

            year_range_pattern = r"^\d{4}-\d{4}$"
            year_month_pattern = r"^\d{4}-\d{2}$"

            if re.match(year_range_pattern, self.user_input):
                self.user_input = self.user_input.split("-")
                self.starting_date = self.user_input[0]
                self.end_date = self.end_date[1]
                #year box plot
                break
            elif re.match(year_month_pattern, self.user_input):
                #month line plot!
                break
            else:
                print(f"{self.user_input} is not one of the valid date options. Please try again.")

            
if __name__ == "__main__":
    wp = WeatherProcessor()