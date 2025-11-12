from html.parser import HTMLParser
from urllib.request import urlopen
from html.entities import name2codepoint
"""
    Katie Sanders
    Scrapes weather data off _
"""

class WeatherScraper(HTMLParser):   

    def __init__(self, full_url):
        super().__init__()
        self._full_url = full_url
        self.weather = {}
        self.in_line = False

            
    @property
    def full_url(self):
        return self._full_url
    
    @full_url.setter
    def full_url(self, new_url):
        if str(new_url) == "":
            raise Exception("url can not be null")
        self._full_url = new_url

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if attrs.get("class") == "table table-striped table-hover align-cells-right data-table":
            self.in_line = True
            print(attrs)


    def handle_data(self, data):
        if self.in_line:
            line = data.strip()
            print(line)

    


def main():
    url = "https://climate.weather.gc.ca/climate_data/daily_data_e.html?StationID=27174&timeframe=2&StartYear=1840&EndYear=2018&Day=1&Year=2025&Month=11#"
    response = urlopen(url)
    html = response.read().decode("utf-8")

    scraper = WeatherScraper(url)
    scraper.feed(html)

main()