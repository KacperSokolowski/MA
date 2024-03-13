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
    
    return text if test != 'brak informacji' else None

def get_location_from_map(
    driver : selenium.webdriver.chrome.webdriver.WebDriver) -> dict:
    """
    Retrieves geographical coordinates from a Google Maps link element on a webpage.

    Parameters:
    driver (selenium.webdriver.chrome.webdriver.WebDriver): The web driver instance from Selenium.

    Returns:
    dict: A dictionary containing the 'latitude' and 'longitude' as strings extracted from the link.
    """

    map_link_elem = driver.find_elements(By.XPATH, '//a[@title="Pokaż ten obszar w Mapach Google (otwiera się w nowym oknie)"]')
    map_link = [elem.get_attribute('href') for elem in map_link_elem]
    geo_location = {
        'latitude' : re.search('ll=(.*),',str(map_link[0])).group(1),
        'longitude' : re.search(',(.*)&z',str(map_link[0])).group(1)}

    return geo_location

def get_adv_description(
    driver : selenium.webdriver.chrome.webdriver.WebDriver,
    button_xpath : str = 
    button_text : str = 'Pokaż więcej') -> dict:
    """
    Retrieves the full advertisement description from a web page by clicking a button to expand the text if necessary.

    Args:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): A Selenium WebDriver instance for Chrome, used to control the browser.
    - button_text (str, optional): The text displayed on the button that expands the advertisement description. Defaults to 'Pokaż więcej'.

    Returns:
    - str: The full text of the advertisement description.
    """

    # Find the button to load full description
    try:
        button = driver.find_element(By.XPATH, f"//button[.//span[contains(text(), '{button_text}')]]")
        button.click()
    except NoSuchElementException:
        pass

    # Get description
    adv_description = driver.find_element(By.XPATH, f'//div[@data-cy="adPageAdDescription"]').text

    return adv_description

# def scrape_announcement(
#     driver : selenium.webdriver.chrome.webdriver.WebDriver,
#     announcements_link : str,
#     sleep_length : float = 0.5):

#     geo_location = get_location_from_map(driver)

#     scrape_dict = {
#         "herf" = announcements_link
#         # Explained variables
#         "rent_price" = get_text_from_aria_label(driver, 'Cena', 'strong')
#         "additional_fees" = get_text_from_data_testid(driver, 'rent')
#         # Explanatory variables
#         "location" = get_text_from_aria_label(driver, 'Adres', 'a')
#         "area" = get_text_from_data_testid(driver, 'area')
#         "room_num" = get_text_from_data_testid(driver, 'rooms_num')
#         "floor" = get_text_from_data_testid(driver, 'floor')
#         "building_type" = get_text_from_data_testid(driver, 'building_type')
#         "extra_space" = get_text_from_data_testid(driver, 'outdoor')
#         "flat_condition" = get_text_from_data_testid(driver, 'construction_status')
#         "advertiser_type" = get_text_from_data_testid(driver, 'advertiser_type')
#         "students_allowed" = get_text_from_data_testid(driver, 'rent_to_students')
#         "furnishings" = get_text_from_data_testid(driver, 'equipment_types')
#         "elevator" = get_text_from_data_testid(driver, 'lift')
#         "parking_space" = get_text_from_data_testid(driver, 'car')
#         "year_of_construction" = get_text_from_data_testid(driver, 'build_year')
#         "additional_information" = get_text_from_data_testid(driver, 'extras_types')
#         "latitude" = geo_location['latitude']
#         "longitude" = geo_location['longitude']
#         "adv_description" = get_adv_description(driver)
#     }
