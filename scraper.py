import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep

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
    

