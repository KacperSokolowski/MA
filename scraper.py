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


def get_text_from_aria_label(
    driver : selenium.webdriver.chrome.webdriver.WebDriver,
    label_name : str,
    tag_name : str = 'div') -> str:

    """
    Retrieves the text content of an element identified by an aria label and tag name.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The Selenium WebDriver instance used to interact with the web page.
    - label_name (str): The value of the `aria-label` attribute of the target element.
    - tag_name (str, optional): The tag name of the target element. Defaults to 'div'.

    Returns:
    - str or None: The text content of the found element, or `None` if the element is not found.
    """

    try:
        text = driver.find_element(
            By.XPATH, f'//{tag_name}[@aria-label="{label_name}"]').text
    except NoSuchElementException:
        text = None

    return text


def get_text_from_data_testid(
    driver : selenium.webdriver.chrome.webdriver.WebDriver,
    label_name : str,
    tag_name : str = 'div') -> str:
    """
    Retrieves the text content of an element identified by data-testid element and tag name.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The Selenium WebDriver instance used to interact with the web page.
    - label_name (str): The value of the `aria-label` attribute of the target element.
    - tag_name (str, optional): The tag name of the target element. Defaults to 'div'.

    Returns:
    - str or None: The text content of the found element, or `None` if the element is not found.
    """

    try:
        text = driver.find_element(
            By.XPATH, f'//{tag_name}[@data-testid="table-value-{label_name}"]').text
    except NoSuchElementException:
        text = None
    
    return text


# def scrape_announcement(
#     driver : selenium.webdriver.chrome.webdriver.WebDriver,
#     announcements_link : str,
#     sleep_length : float = 0.5):

#     # Containers
#     herf = []
#     rent_price = []
#     additional_fees = []

#     location = []
#     area = []
#     room_num = []
#     floor  = []
#     building_type = []
#     extra_space = []
#     flat_condition = []

#     advertiser_type = []
#     students_allowed = []
#     furnishings  = []
#     utilities = []
#     elevator = []
#     parking_space = []
#     year_of_construction = []
#     additional_information = []

#     latitude = []
#     longitude = []
#     adv_description = []
