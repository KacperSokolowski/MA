"""
This module provides tools for scraping apartment rental announcements from the Otodom website.
It includes functionality to initialize a web scraper using Selenium WebDriver,
collect links to announcements from a given URL, extract information from individual announcements,
and compile the data into a Pandas DataFrame. Additionally, it can filter announcements based on user-defined criteria,
save the extracted data as a CSV file, and handle dynamic content loading on web pages. The module is designed to be flexible,
allowing for customizable scraping configurations such as specifying sleep intervals to mimic human browsing behavior,
choosing whether to save the data as a CSV file, and including additional filtered links to refine the data collection process.

Dependencies:
- selenium: For automating web browser interaction to scrape data.
- pandas: For organizing scraped data into structured formats.
- re: For regex operations to parse URLs and extract relevant information.
- collections.defaultdict: For efficiently collecting and organizing scraped data.
- datetime: For timestamping saved data files.
- time.sleep: For pacing requests to simulate human browsing patterns and manage dynamic content loading.

Features:
- Initialize Selenium WebDriver with options tailored for Otodom scraping.
- Navigate through paginated listing URLs to collect announcement links.
- Extract detailed information from individual announcement pages.
- Compile and optionally filter announcement data based on additional criteria.
- Save the compiled data as a CSV file for further analysis or use.
"""

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
import re
import pandas as pd
from collections import defaultdict
from datetime import datetime


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

def get_location_from_map(
    driver : selenium.webdriver.chrome.webdriver.WebDriver) -> dict:
    """
    Retrieves geographical coordinates from a Google Maps link element on a webpage.
    If the exact location is not available, the function checks for a specific text indicating
    that the location is approximate. This is determined based on the presence of a div element
    with a specific message. If this message is present, the function marks the location as approximate.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The web driver instance from Selenium.

    Returns:
    - dict: A dictionary containing the geographical coordinates:
        - 'latitude' (str or None): The latitude as a string if available; otherwise, None.
        - 'longitude' (str or None): The longitude as a string if available; otherwise, None.
        - 'approximate' (bool): True if the location is approximate (exact address not specified),
          False if the location is based on the map link, or None if no location information is found.
    """

    # Returns structure
    geo_location = {'latitude' : None, 'longitude' : None, 'approximate': None}

    # Check if exact address is provided
    not_available_indicator = None
    not_available_text = 'Nieruchomość znajduje się w zaznaczonym obszarze mapy. Niestety ogłoszeniodawca nie wskazał dokładnego adresu.'
    try:
        not_available_indicator = driver.find_element(By.XPATH, f"//div[contains(text(), '{not_available_text}')]")
    except NoSuchElementException:
        pass
    
    if not_available_indicator is None:
        geo_location['approximate'] = False
    else:
        geo_location['approximate'] = True

    # Get coordinates from a Google Maps link
    try:
        map_link_elem = driver.find_elements(By.XPATH, "//a[@title='Pokaż ten obszar w Mapach Google (otwiera się w nowym oknie)']")
    except NoSuchElementException:
        return geo_location
    
    map_link = [elem.get_attribute('href') for elem in map_link_elem]
    if map_link:
        geo_location['latitude'] = re.search('ll=(.*),',str(map_link[0])).group(1)
        geo_location['longitude'] = re.search(',(.*)&z',str(map_link[0])).group(1)

    return geo_location

def get_adv_description(
    driver : selenium.webdriver.chrome.webdriver.WebDriver) -> str:
    """
    Retrieves the full advertisement description from a web page by clicking a button to expand the text if necessary.

    Args:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): A Selenium WebDriver instance for Chrome, used to control 
    the browser.

    Returns:
    - str: The full text of the advertisement description,
    or `None` if the element is not found.
    """

    # Find the button to load full description
    button = None
    try:
        button = driver.find_element(By.XPATH, f"//button[.//span[contains(text(), 'Pokaż więcej')]]")

    except NoSuchElementException:
        pass

    if button is not None:
        desc_location = driver.find_element(By.XPATH, f"//h4[contains(text(), 'Opis')]")
        desc_location.location_once_scrolled_into_view
        button.click()

    # Get description
    try:
        adv_description = driver.find_element(By.XPATH, f'//div[@data-cy="adPageAdDescription"]').text
    except NoSuchElementException:
        return None
    
    return adv_description

def get_text_from_class(driver, element, class_name):
    """
    Retrieves the text content of an element identified by its class name.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The Selenium WebDriver instance used to interact with the 
    web page.
    - element (str): The name of searched element.
    - class_name (str): The class name of the target element.

    Returns:
    - str or None: The text content of the found element, or `None` if the element is not found.
    """

    try:
        text = driver.find_element(By.XPATH, f"//{element}[@class='{class_name}']").text
    except NoSuchElementException:
        text = None
    return text

def get_text_from_main_table(driver, label_name):
    """
    Retrieves the text content of a specific element within the main table based on a label name.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The Selenium WebDriver instance used to interact with the 
    web page.
    - label_name (str): The text contained within a `p` element used to identify the target element.

    Returns:
    - str or None: The text content of the found element, or `None` if the element is not found 
      or if the content is equal to 'brak informacji'.
    """

    try:
        xpath = (
            "//div[h4[contains(text(), 'Mieszkanie na wynajem')]]"
            f"/div/div[p[contains(text(), '{label_name}')]]/p[2]"
        )
        value_element = driver.find_element(By.XPATH, xpath)
        text = value_element.text
    except NoSuchElementException:
        text = None
    return text if text != 'brak informacji' else None

def get_text_from_supp_table(driver, table_name, label_name):
    """
    Retrieves the text content of a specific element within a supplementary table based on the table name and label name.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The Selenium WebDriver instance used to interact
    with the web page.
    - table_name (str): The text contained within the `header/p` element used to identify the supplementary table.
    - label_name (str): The text contained within a `p` element used to locate the target element within the table.

    Returns:
    - str or None: The text content of the found element, or `None` if the element is not found 
      or if the content is equal to 'brak informacji'.
    """

    try:
        xpath = (
            f"//div[header/p[contains(text(), '{table_name}')]]"
            f"/div/div/div[p[contains(text(), '{label_name}')]]/p[2]"
        )
        value_element = driver.find_element(By.XPATH, xpath)
        text = value_element.text
    except NoSuchElementException:
        text = None
    return text if text != 'brak informacji' else None

def scrape_single_announcement(
    driver : selenium.webdriver.chrome.webdriver.WebDriver,
    announcements_link : str,
    sleep_length : float = 1) -> dict:
    """
    Scrapes data from a single apartment for rent announcement on a webpage using a given web driver.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): The Selenium WebDriver instance to interact with the webpage.
    - announcements_link (list): URL to individual announcements to be scraped.
    - sleep_length (float, optional): Time in seconds to pause between actions to simulate human behavior and ensure
    page content is loaded. Defaults to 1.

    Returns:
    dict: A dictionary containing scraped data of various attributes of the rent announcement.
    """
    
    driver.get(announcements_link)
    sleep(sleep_length)
    
    try:
        expired = driver.find_element(By.XPATH, "//div[@data-cy='expired-ad-alert']")
        return None
    except NoSuchElementException:
        pass
    
    scrape_dict = {
        'title': get_text_from_class(driver, 'h1', 'css-wqvm7k ef3kcx01').strip(),
        'rent_price' : get_text_from_class(driver, 'div', 'css-1ifvn3m ef3kcx02'),
        'area_room_num' : get_text_from_class(driver, 'div', 'css-58w8b7 eezlw8k0'),
        'floor': get_text_from_main_table(driver, 'Piętro'),
        'ogrzewanie':get_text_from_main_table(driver, 'Ogrzewanie'),
        'flat_condition': get_text_from_main_table(driver, 'Stan wykończenia'),
        'available_from': get_text_from_main_table(driver, 'Dostępne od'),
        'deposit': get_text_from_main_table(driver, 'Kaucja'),
        'advertiser_type': get_text_from_main_table(driver, 'Typ ogłoszeniodawcy'),
        'additional_information': get_text_from_main_table(driver, 'Informacje dodatkowe'),
        'location': get_text_from_class(driver, 'div', 'css-70qvj9 e42rcgs0')
    }
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(sleep_length/2)
    try:
        map_element = driver.find_element(By.ID, 'map')
    except NoSuchElementException:
        pass
    map_element.location_once_scrolled_into_view
    sleep(sleep_length)
    geo_location = get_location_from_map(driver)
    scrape_dict['latitude'] = geo_location['latitude']
    scrape_dict['longitude'] = geo_location['longitude']
    scrape_dict['approximate_coordinates'] = geo_location['approximate']
    
    try:
        driver.find_element(By.XPATH, "//header[@role='button']//p[text()='Budynek i materiały']").click()
    except NoSuchElementException:
        pass
    sleep(sleep_length/2)
    scrape_dict['year_of_construction'] = get_text_from_supp_table(driver, 'Budynek i materiały', 'Rok budowy')
    scrape_dict['elevator'] = get_text_from_supp_table(driver, 'Budynek i materiały', 'Winda')
    scrape_dict['building_type'] = get_text_from_supp_table(driver, 'Budynek i materiały', 'Rodzaj zabudowy')
    scrape_dict['security'] = get_text_from_supp_table(driver, 'Budynek i materiały', 'Bezpieczeństwo')
    
    try:
        driver.find_element(By.XPATH, "//header[@role='button']//p[text()='Wyposażenie']").click()   
    except NoSuchElementException:
        pass
    sleep(sleep_length/2)
    scrape_dict['equipment'] = get_text_from_supp_table(driver, 'Wyposażenie', 'Wyposażenie')
    scrape_dict['utilities'] = get_text_from_supp_table(driver, 'Wyposażenie', 'Media')
    scrape_dict['safeguards'] = get_text_from_supp_table(driver, 'Wyposażenie', 'Zabezpieczenia')
    
    scrape_dict['announcement_date'] = get_text_from_class(driver, 'div', 'css-gg4vpm e2md81j0'),
    scrape_dict['adv_description'] = get_adv_description(driver)
    
    return scrape_dict

def scrape_otodom_announcements(
    driver : selenium.webdriver.chrome.webdriver.WebDriver,
    announcements_links : list,
    sleep_length : float = 1,
    save_as_csv : bool = True,
    csv_file_name_prefix : str = 'otodom',
    csv_destination_path : str = 'data_raw') -> pd.DataFrame:
    """
    Scrapes apartment for rent announcements from provided links on the Otodom website, compiles the data into a DataFrame, 
    and optionally saves it as a CSV file.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): Selenium WebDriver for web page interaction.
    - announcements_links (list): List of URLs to individual announcements to be scraped.
    - sleep_length (float, optional): Time in seconds to pause between actions to simulate human behavior and ensure
      page content is loaded. Defaults to 0.5.
    - save_as_csv (bool, optional): If True, saves the compiled DataFrame as a CSV file. Defaults to True.
    - csv_file_name_prefix (str, optional): Prefix for the CSV file name. Defaults to 'otodom'.
    - csv_destination_path (str, optional): Directory path where the CSV file will be saved. Defaults to 'data_raw'.

    Returns:
    - pd.DataFrame: DataFrame containing scraped data from each announcement link.
    """
    # Container
    scraped_dicts = []

    # Loop through scraped announcements links
    for i in announcements_links:
        single_announcement = scrape_single_announcement(driver, i, sleep_length)
        #### TO DO
        if single_announcement is not None:
            single_announcement['link'] = i
            scraped_dicts.append(single_announcement)

    # Concatenate dictionaries
    concat_dict = defaultdict(list)
    for dictionary in scraped_dicts:
        for key, value in dictionary.items():
            concat_dict[key].append(value)

    # Converting defaultdict to pd.DataFrame
    df = pd.DataFrame(dict(concat_dict))

    # Save df as csv file with current date suffix
    if save_as_csv:
        current_date = datetime.now().strftime("%Y_%m_%d")
        file_name = f"{csv_file_name_prefix}_{current_date}.csv"
        path = f'{csv_destination_path}/{file_name}'
        df.to_csv(path,
                  encoding='utf-8',
                  index=False)
    return df

def run_otodom_scraper(
    first_page_url : str,
    add_filtered_links : bool = False,
    filtered_links_dict : dict = {},
    return_df : bool = True,
    sleep_length : float = 1,
    save_as_csv : bool = True,
    csv_file_name_prefix : str = 'otodom',
    csv_destination_path : str = 'data_raw') -> pd.DataFrame:
    """
    Executes the Otodom scraper to collect apartment for rent announcements from a given URL, optionally including data 
    from additional filtered links, and returns or saves the data as specified.

    Parameters:
    - first_page_url (str): URL to the first page of unfiltered announcements.
    - add_filtered_links (bool, optional): If True, additional information from filtered links is included. Defaults to False.
    - filtered_links_dict (dict): A dictionary where keys represent column names for the final DataFrame to indicate 
      if an announcement is within filtered announcements, and values are URLs to the first page of filtered announcements.
    - return_df (bool, optional): Determines whether to return a DataFrame. Defaults to True.
    - sleep_length (float, optional): Time in seconds to wait between actions to ensure page content loads. Defaults to 0.5.
    - save_as_csv (bool, optional): If True, saves the resulting DataFrame as a CSV file. Defaults to True.
    - csv_file_name_prefix (str, optional): Prefix for the generated CSV file name. Defaults to 'otodom'.
    - csv_destination_path (str, optional): Path to save the CSV file. Defaults to 'data_raw'.

    Returns:
    - pd.DataFrame or None: The DataFrame containing scraped data if return_df is True; otherwise, None.

    The function initializes the scraper, collects links to announcements, and optionally processes additional 
    filtered links as specified in `filtered_links_dict`. The collected data can be returned as a DataFrame, 
    saved as a CSV file, or both depending on the function parameters.
    """

    # Initialize driver
    driver = initialize_otodom_scraper(sleep_length)

    # Get announcements URLs
    announcements_links = get_announcements_links(driver, first_page_url, sleep_length)

    # Run scraper, save as csv and return df if additional info from other filtered pages is not required
    if not add_filtered_links:
        df = scrape_otodom_announcements(
            driver = driver,
            announcements_links = announcements_links,
            save_as_csv = save_as_csv,
            sleep_length = sleep_length,
            csv_file_name_prefix = csv_file_name_prefix,
            csv_destination_path = csv_destination_path)
        
        return df if return_df else None
    
    # Run scraper
    df = scrape_otodom_announcements(
        driver = driver,
        announcements_links = announcements_links,
        sleep_length = sleep_length,
        save_as_csv = False)
    
    # Get additnal info
    for column_name, ulr in filtered_links_dict.items():
        filtered_annoucments = get_announcements_links(driver, ulr)
        filtered_annoucments = list(dict.fromkeys(filtered_annoucments))
        df[column_name] = df['link'].isin(filtered_annoucments)

    # Save as csv
    if save_as_csv:
        current_date = datetime.now().strftime("%Y_%m_%d")
        file_name = f"{csv_file_name_prefix}_{current_date}.csv"
        path = f'{csv_destination_path}/{file_name}'
        df.to_csv(path,
                  encoding='utf-8',
                  index=False)
    
    return df if return_df else None

def get_links_titles(
    first_page_url : str,
    sleep_length : float = 1,
    return_df : bool = True,
    save_as_csv : bool = True,
    csv_file_name_prefix : str = 'available_ads',
    csv_destination_path : str = 'data_raw') -> pd.DataFrame:
    
    
    driver = initialize_otodom_scraper(sleep_length)
    
    # Container
    announcements = []

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
        
        # Get announcements links and titles
        links = driver.find_elements(By.XPATH, '//a[@data-cy="listing-item-link"]')
        titles = driver.find_elements(By.XPATH, '//p[@data-cy="listing-item-title"]')
        
        # Collect data
        for link, title in zip(links, titles):
            announcements.append({
                "link": link.get_attribute('href'),
                "title": title.text.strip()
            })

    # Remove duplicates; return result
    df = pd.DataFrame(announcements).drop_duplicates().reset_index(drop=True)
    current_date = datetime.now().strftime("%Y_%m_%d")
    df['date'] = current_date
    
    # Save as csv
    if save_as_csv:
        file_name = f"{csv_file_name_prefix}_{current_date}.csv"
        path = f'{csv_destination_path}/{file_name}'
        df.to_csv(path,
                  encoding='utf-8',
                  index=False)
        
    return df if return_df else None