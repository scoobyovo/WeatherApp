"""
scrape_weather
==============

Katie Sanders & Param Kotak
Scrapes weather data from Environment Canada using HTMLParser.
2025-11-16

This module defines the WeatherScraper class, which scrapes historical
weather data from Environment Canada's climate website using Python's
built-in HTMLParser.

The scraper navigates month-by-month backwards in time, extracts
maximum, minimum, and mean temperatures for each day, and stores the
results in a dictionary keyed by date.
"""


from html.parser import HTMLParser
from urllib.request import urlopen
from datetime import datetime, date
import ssl
import logging


ssl._create_default_https_context = ssl._create_unverified_context
LOGGER = logging.getLogger(__name__)


class WeatherScraper(HTMLParser):   
    """
    Scrape daily weather data from Environment Canada's climate website.

    This class uses HTMLParser to navigate the site's table structure
    and extract daily temperature values, which are stored in a nested
    dictionary.

    Attributes
    ----------
    weather : dict
        Stores all scraped weather data.
    in_tr : bool
        Indicates whether the parser is currently inside a <tr> row.
    in_tbody : bool
        Indicates whether the parser is inside the main weather-data table body.
    current_date : str or None
        Holds the date for the current row being processed.
    current_row_data : list
        Accumulates column values (Max, Min, Mean, etc.) for the current row.
    current_tag : str or None
        Tracks the current HTML tag being processed.
    curr_year : int
        The current year being scraped (moves backwards in time).
    curr_month : int
        The current month being scraped.
    base_url : str
        Partial URL used to construct full request URLs.
    data_found : bool
        Indicates whether valid weather data was found for the current month.
    last_year : int
        The earliest year to scrape before stopping.
    """


    def __init__(self):
        """
        Initialize a new WeatherScraper instance.

        Sets initial parser state, defines date traversal logic, and
        prepares the scraper to extract weather data month-by-month.
        """
        super().__init__()
        self.weather = {}
        self.in_tr = False
        self.in_tbody = False
        self.current_date = None
        self.current_row_data = []
        self.current_tag = None
        self.in_href = False

        date_ref = date.today()
        self.curr_year = date_ref.year
        self.curr_month = date_ref.month
        self.base_url = "https://climate.weather.gc.ca/climate_data/daily_data_e.html?StationID=27174&timeframe=2&StartYear=1900&EndYear=2018&Day=1&"
        self.data_found = False
        self.last_year = 2020
            

    @property
    def full_url(self):
        """Return the current full URL being used for scraping."""
        return self._full_url
    

    @full_url.setter
    def full_url(self, new_url):
        """
        Set the full URL for scraping.

        Parameters
        ----------
        new_url : str
            A non-empty URL string.

        Raises
        ------
        Exception
            If the URL is empty.
        """
        if str(new_url) == "":
            raise Exception("url can not be null")
        self._full_url = new_url


    def scrape_data(self):
        """
        Scrape all available data by iterating month-by-month backwards.

        The method repeatedly:
        - Builds a monthly URL
        - Downloads the HTML
        - Parses table rows
        - Extracts Max/Min/Mean temperatures
        - Moves back one month until no more data exists

        Returns
        -------
        dict
            A dictionary containing all scraped weather records.
        """
        while True:
            self.reset()
            self.in_tr = False
            self.in_tbody = False
            self.data_found = False
            
            try:
                response = urlopen(self.format_url())
                html = response.read().decode("utf-8")
                self.feed(html)
            except Exception as exc:
                LOGGER.exception("Exception while fetching URL %s: %s", self.format_url(), exc)
                print(f"Exception - {exc}")
                break

            if not self.data_found:
                print(f"No data found for {self.curr_year}-{self.curr_month:02d}. Stopping.")
                return self.weather

            if self.curr_year != self.last_year or self.curr_year == self.curr_year and self.curr_month > 1:
                if self.curr_month == 1:
                    self.curr_month = 12
                    self.curr_year -= 1
                else:
                    self.curr_month -= 1
            else:
                print(f"Scraping finished for {date.today().year}-{self.curr_year:02d}. Stopping.")
                return self.weather


    def format_url(self):
        """
        Construct the full scraping URL for the current year and month.

        Returns
        -------
        str
            A complete URL ready for use.
        """
        return f"{self.base_url}Year={self.curr_year}&Month={self.curr_month}#"


    def handle_starttag(self, tag, attrs):
        """
        Process HTML start tags and detect relevant data sections.

        Parameters
        ----------
        tag : str
            The name of the HTML tag encountered.
        attrs : list
            The list of (attribute, value) pairs for the tag.
        """
        attrs = dict(attrs)
        self.current_tag = tag

        if tag == "tbody":
            self.in_tbody = True

        '''Reset values if inside a new tr'''
        if self.in_tbody and tag == "tr":
            self.in_tr = True
            self.current_row_data = []
            self.current_date = None
        
        if self.in_tbody and tag == "abbr":
            date = attrs.get("title")
            try:
                self.current_date = datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")
            except Exception:
                self.current_date = None


    def handle_endtag(self, tag):    
        """
        Handle closing tags and finalize row processing.

        Parameters
        ----------
        tag : str
            The HTML end tag encountered.

        Notes
        -----
        When a </tr> tag closes, if at least three temperature values were
        captured, the row is stored in the weather dictionary.
        """
        if tag == "tbody":
            self.in_tbody = False

        if tag == "tr" and self.in_tr:
            if self.current_date and len(self.current_row_data) >= 3:
                try:
                    max_temp = self.current_row_data[0] if len(self.current_row_data) > 0 else None
                    min_temp = self.current_row_data[1] if len(self.current_row_data) > 1 else None
                    mean_temp = self.current_row_data[2] if len(self.current_row_data) > 2 else None
                            
                    self.weather[self.current_date] = {
                        "Max": max_temp,
                        "Min": min_temp,
                        "Mean": mean_temp
                    }
                    self.data_found = True
                except Exception as exc:
                    LOGGER.exception("Exception while processing row for %s: %s", 
                                     self.current_date, exc)
                    print(f"Exception occurred: {exc}")
                self.in_tr = False


    def handle_data(self, data):
        """
        Process text content inside relevant HTML tags.

        Parameters
        ----------
        data : str
            The inner text of the current HTML element.

        Notes
        -----
        Temperature readings appear within <td> or <span> tags.
        Missing data is represented as 'M'.
        """
        if self.in_tr and self.in_tbody:
            line = data.strip()
            if self.current_tag == "td" and line:
                self.current_row_data.append(line)
            elif line and self.current_tag == "span":
                self.current_row_data.append("M")




if __name__ == "__main__":
    scraper = WeatherScraper()
    scraper.scrape_data()
