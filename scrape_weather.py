from html.parser import HTMLParser
from urllib.request import urlopen
from html.entities import name2codepoint
from datetime import datetime, date
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

"""
    Katie Sanders & Param Kotak
    Scrapes weather data
    2025-11-16
"""

class WeatherScraper(HTMLParser):   
    """Represents a weather scraper using HTMLParser"""

    def __init__(self):
        """
        Initializes an instance of the weather scraper
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
        return self._full_url
    
    @full_url.setter
    def full_url(self, new_url):
        if str(new_url) == "":
            raise Exception("url can not be null")
        self._full_url = new_url

    def scrape_data(self):
        """
        Handles url updating and scraping for each page
        """
        while True:
            self.reset()
            self.in_tr = False
            self.in_tbody = False
            self.data_found = False
            
            print(self.format_url())
            try:
                response = urlopen(self.format_url())
                html = response.read().decode("utf-8")
                self.feed(html)
            except Exception as e:
                print(f"Exception - {e}")
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
        """Formats the url with updated year and month"""
        return f"{self.base_url}Year={self.curr_year}&Month={self.curr_month}#"

    def handle_starttag(self, tag, attrs):
        """Handles all start tags for scraping"""
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
            Handles end tag and extracts the data from each row into weather dictionary
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
                    print(f"{self.current_date}: Max = {max_temp}, Min = {min_temp}, Mean = {mean_temp}")
                    self.data_found = True
                except Exception as e:
                    print(f"Exception occurred: {e}")
                self.in_tr = False

    def handle_data(self, data):
        """Handles website data"""
        if self.in_tr and self.in_tbody:
            line = data.strip()
            if self.current_tag == "td" and line:
                self.current_row_data.append(line)
            elif line and self.current_tag == "span":
                self.current_row_data.append("M")
            

if __name__ == "__main__":
    scraper = WeatherScraper()
    scraper.scrape_data()