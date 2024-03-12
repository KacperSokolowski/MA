import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import re

def initialize_otodom_scraper(sleep_length : float = 0.5) -> selenium.webdriver.chrome.webdriver.WebDriver:
    """
    Initializes and returns a Chrome WebDriver with the Otodom.pl homepage loaded, 
    and cookies accepted. 
    
    Parameters:
    - sleep_length (float): Time in seconds to pause after actions, defaulting to 0.5.
    
    Returns:
    - A Chrome WebDriver ready for web scraping tasks on Otodom.pl.
    """

    # Initialize chrome driver; get otodom website
    driver = webdriver.Chrome()
    driver.get('https://www.otodom.pl')
    sleep(sleep_length)

    # Accept cookies on the site
    driver.find_element(By.XPATH, '//button[text()="Akceptuję"]').click()
    sleep(sleep_length)

    return driver
    
def get_announcements_links(
    driver : selenium.webdriver.chrome.webdriver.WebDriver,
    first_page_url : str,
    sleep_length : float = 0.5) -> list:
    """
    Navigates through a apartments for rent website's paginated listings starting from a given URL, 
    collecting and returning the unique links to all listed property announcements.

    Args:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): A Selenium WebDriver instance for Chrome.
    - first_page_url (str): The URL of the first page of listings.
    - sleep_length (float, optional): The duration in seconds to wait for dynamic content to load 
      upon navigating to a new page and after scrolling to the bottom of the page. Defaults to 0.5.

    Returns:
    - List[str]: A list of unique URLs linking to individual rent announcements found across 
      the paginated search results.
    """

    # Container
    announcements_links = []

    # Loop through otodom using link with prefilled search
    i=1
    while True:
        site = re.sub('&page=[^&]*', f'&page={i}', first_page_url)
        driver.get(site)

        # Iter until page without new result appears
        try:
            driver.find_element(By.XPATH, '//div[@data-cy="no-search-results"]')
            break
        except NoSuchElementException:
            i+=1
        
        # Go to the down of the page to load all announcements
        sleep(sleep_length)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(sleep_length)
        
        # Get announcements links
        ts=driver.find_elements(By.XPATH, '//a[@data-cy="listing-item-link"]')
        for t in ts:
            announcements_links.append(t.get_attribute('href'))

    # Remove duplicates; return result
    announcements_links = list(dict.fromkeys(announcements_links))
    return announcements_links

