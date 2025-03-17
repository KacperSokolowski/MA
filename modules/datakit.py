import pandas as pd
import numpy as np
import os
import re
import haversine as hs
import spacy
import morfeusz2
from sklearn.neighbors import BallTree
import pandas.api.types as pdt
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep

def find_warsaw_district(input_string) -> str:
    """
    Identifies and returns a Warsaw district name from a given input string.

    The function splits the input string by commas and checks each part against a list of Warsaw district names. 
    If one of the parts matches a district name, that district name is returned. If there are no matches, 
    the function returns None.

    Parameters:
    - input_string (str): The string to be analyzed, which can contain multiple comma-separated values.

    Returns:
    - str or None: The name of a Warsaw district if found; otherwise, None.
    """
    # List of Warsaw districts
    warsaw_districts = [
        "Bemowo", "Białołęka", "Bielany", "Mokotów", "Ochota",
        "Praga-Południe", "Praga-Północ", "Rembertów", "Śródmieście",
        "Targówek", "Ursus", "Ursynów", "Wawer", "Wesoła",
        "Wilanów", "Włochy", "Wola", "Żoliborz"
    ]

    # Split the input string by commas
    parts = input_string.split(',')

    # Check each part for a match with Warsaw districts
    for part in parts:
        if part.strip() in warsaw_districts:
            return part.strip()  # Return the matching district name

    return None

def extract_last_update_date(ad_info):
    
    update_date_part = [line for line in ad_info.split('\\n') if 'Aktualizacja:' in line]
    return update_date_part[0].replace("('Aktualizacja: ", '').strip() if update_date_part else None

def extract_added_date(ad_info):
    
    added_date_part = [line for line in ad_info.split('\\n') if 'Dodano:' in line]
    return added_date_part[0].replace('Dodano: ', '').strip() if added_date_part else None

def prepare_for_append(data_draw):
    """
    Processes raw advertisement data to before appending to main dataset.

    This function takes a DataFrame containing advertisement data and performs several transformations:
    - Identifies and extracts the district name from the 'location' column using the `find_warsaw_district` function.
    - Removes rows where the district name could not be identified.
    - Extracts the last update date and added date from the 'announcement_date' column using the `extract_ad_dates` function.
    - Drops the 'announcement_date' column as it is no longer needed.
    - Reorders the columns to place 'added_dt', 'last_update', and 'link' at the beginning.

    Parameters:
    - data_draw (pd.DataFrame): A DataFrame containing raw advertisement data with at least 
      'location', 'announcement_date', and 'link' columns.

    Returns:
    - pd.DataFrame: A cleaned and organized DataFrame with extracted and reordered information.
    """

    df = data_draw.copy()
    
    # Extract district names from the 'location' column and create a new 'district' column
    df['district'] = df['location'].apply(lambda x: find_warsaw_district(str(x)))
    
    # Remove rows where the district name could not be identified
    df = df[~df.district.isna()]
    
    # Extract 'last_update' and 'added_dt' dates using the `extract_ad_dates` function
    df['last_update'] = df['announcement_date'].apply(lambda x: extract_last_update_date(str(x)))
    df['added_dt'] = df['announcement_date'].apply(lambda x: extract_added_date(str(x)))
    df.drop(['announcement_date'], axis=1, inplace=True)
    
    # Add columns
    df['expired'] = 0
    df['expired_date'] = None

    # Reorder columns
    to_order = ['added_dt', 'last_update', 'link', 'expired', 'expired_date']
    columns_order = to_order + [col for col in df.columns if col not in to_order]
    df = df[columns_order]
    
    return df

def convert_date(date_str):
    try:
        if '.' in date_str:  # Format 1: 'DD.MM.YYYY'
            return pd.to_datetime(date_str, format='%d.%m.%Y')
        elif '_' in date_str:  # Format 2: 'YYYY_MM_DD'
            return pd.to_datetime(date_str, format='%Y_%m_%d')
    except Exception:
        return None
    
def extract_rent_info(text):
    # Extract rent
    rent_match = re.search(r'(\d[\d\s]*)\s*([A-Za-zł]+)', text)
    rent = int(rent_match.group(1).replace(" ", "")) if rent_match else None
    rent_currency = rent_match.group(2) if rent_match else None

    # Extract additional fees
    fees_match = re.search(r'\+ Czynsz (\d[\d\s]*)\s*([A-Za-zł]+)', text)
    additional_fees = int(fees_match.group(1).replace(" ", "")) if fees_match else 0
    additional_fees_currency = fees_match.group(2) if fees_match else None

    # Extract payment frequency
    freq_match = re.search(r'/(\w+)', text)
    payment_frequency = freq_match.group(1) if freq_match else None

    return pd.Series([rent, rent_currency, additional_fees, additional_fees_currency, payment_frequency])

def extract_area(text):
    match = re.search(r'(\d+(?:\.\d+)?)m²', text)
    return float(match.group(1)) if match else None

def extract_rooms(text):
    match = re.search(r'(\d+)\s*pok', text)
    return int(match.group(1)) if match else None

def parse_floor_values(row: str) -> tuple:
    """
    Parses a string containing floor information to extract the specific floor and the total number of floors in the building.

    Parameters:
    - row (str): The string from which to parse floor information. Can be NaN, a single number, a range in 'X/Y' format, 
                 or special formats like 'parter' or '>X'.

    Returns:
    - tuple: A tuple containing two elements:
        1. floor (int or None): The specific floor number, or None if not determinable.
        2. building_height (int or None): The total number of floors in the building, or None if not applicable.
    """
    
    if pd.isna(row):
        return None, None
    if '/' in row:
        parts = row.split('/')
        floor_part = parts[0].strip()
        if floor_part.isdigit():
            floor = int(floor_part)
        elif floor_part == 'parter':
            floor = 1
        elif floor_part.startswith('>'):
            floor = int(floor_part[1:].strip())
        else:
            floor = None

        height_part = parts[1].strip()
        if height_part.isdigit():
            building_height = int(height_part)
        else:
            building_height = None
    else:
        floor = int(row) if row.isdigit() else None
        building_height = None
    
    return floor, building_height

def initialize_nlp() -> None:
    """
    Initializes a global NLP model using the spaCy library with the Polish small model.
    This allows the `nlp` model to be used elsewhere in the code after initialization.

    Returns:
    - None
    """
    global nlp
    nlp = spacy.load("pl_core_news_sm")

    return None

def initialize_morf() -> None:
    """
    Initializes a global morphological analyzer using the Morfeusz2 library.
    This prepares `morf` for use throughout the codebase for morphological analysis tasks.

    Returns:
    - None
    """
    global morf
    morf = morfeusz2.Morfeusz()

    return None

def contains_keywords_morf(description: str, keywords: list):
    """
    Determines whether a given text description contains any of a list of keywords based on morphological analysis.

    This function processes the input text using a natural language processing model to tokenize the text.
    For each token, it performs a morphological analysis to identify the base form of the word.
    The function then checks if this base form matches any of the keywords provided in the list.
    It returns True as soon as a keyword match is found and stops further analysis.

    Parameters:
    - description (str): The text description to analyze for the presence of keywords.
    - keywords (list): A list of keyword strings to search for in the text, based on their morphological base forms.

    Returns:
    - bool: True if at least one of the keywords is found in the text, False otherwise.

    Requires:
    - A loaded natural language processing model (nlp) to tokenize the text.
    - A morphological analysis tool morfeusz2 (morf) that provides the base form of each token.
    """

    try:
        doc = nlp(description.lower())
    except AttributeError:
        return False
    
    contains_keywords = False
    for token in doc:
        analysis = morf.analyse(token.text)
        try:
            contains_keywords = True if analysis[0][2][1] in keywords else contains_keywords
        except IndexError:
            continue

        if contains_keywords:
            break
            
    return contains_keywords

def replace_characters(input_string : str) -> str:
    """
    Replaces specific Polish characters and hyphens in a given string with their ASCII equivalents or alternatives.

    This function maps Polish diacritic characters to their non-diacritic counterparts and replaces hyphens with underscores.
    It iterates over a predefined set of character replacements and applies these transformations to the input string.

    Parameters:
    - input_string (str): The string to be transformed.

    Returns:
    - str: The transformed string with specified characters replaced.
    """
    
    replacements = {
        'ł': 'l', 'Ł': 'L', 'ą': 'a', 'Ą': 'A', 'ć': 'c', 'Ć': 'C', 'ę': 'e', 'Ę': 'E',
        'ń': 'n', 'Ń': 'N', 'ó': 'o', 'Ó': 'O', 'ś': 's', 'Ś': 'S', 'ż': 'z', 'Ż': 'Z',
        'ź': 'z', 'Ź': 'Z', '-': '_'
    }
    for search, replace in replacements.items():
        input_string = input_string.replace(search, replace)
    return input_string

def transform_data(main, only_expired, duration_start, duration_end, utilize_morf): 

    df = main.copy()
    del main

    # Keep only expired announcements
    # Convert dates, calculate duration between announcement appearance and expiration
    # Filter duration time
    if only_expired:
        df = df[df.expired.eq(1)]

        df['expired_date'] = df['expired_date'].apply(convert_date)
        df['days_difference'] = (df['expired_date'] - df['added_dt']).dt.days

        df = df[df.days_difference.ge(duration_start)&\
                df.days_difference.le(duration_end)].copy()
        
    # Transform rent_price
    # Create: rent, rent_currency, additional_fees, additional_fees_currency, payment_frequency
    # Exclude prices not in PLN
    rental_columns = ['rent', 'rent_currency', 'additional_fees', 'additional_fees_currency', 'payment_frequency']
    df[rental_columns] = df['rent_price'].apply(extract_rent_info)

    df = df[df.rent_currency.eq('zł')&\
            (df.additional_fees_currency.eq('zł')|df.additional_fees_currency.isna())].copy()
    
    # Transform area_room_num
    # Create: area, room_number
    df['area'] = df['area_room_num'].apply(extract_area)
    df['room_number'] = df['area_room_num'].apply(extract_rooms)

    # Transform floor
    df[['floor', 'building_height']] = df['floor'].apply(lambda x: pd.Series(parse_floor_values(x)))

    # Transform flat_condition
    df['for_renovation'] = df['flat_condition'].apply(
        lambda x: 0 if pd.isna(x) or x == 'do zamieszkania' else 1)
    
    # Transform heating
    df.rename(columns={'ogrzewanie': 'heating'}, inplace=True)
    df['heating'] = df['heating'].replace({
        'elektryczne': 'electric',
        'gazowe': 'gas',
        'inne': 'other',
        'kotłownia': 'boiler room',
        'miejskie': 'district'
    })

    # Transform additional_information
    # Create: balcony / terrace / garden / parking_space / separate_kitchen / utility_room / basement
    df['balcony'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'balkon' in x else 0)
    df['terrace'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'taras' in x else 0)
    df['garden'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'ogródek' in x else 0)
    df['parking_space'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'garaż/miejsce parkingowe' in x else 0)
    df['separate_kitchen'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'oddzielna kuchnia' in x else 0)
    df['utility_room'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'pom. użytkowe' in x else 0)
    df['basement'] = df['additional_information'].apply(
        lambda x: 1 if type(x)==str and 'piwnica' in x else 0)

    # Transform elevator
    df['elevator'] = df['elevator'].apply(lambda x: x == 'tak').astype(int)

    # Transform building_type
    df['building_type'] = df['building_type'].replace({
        'apartamentowiec': 'apartment',
        'kamienica': 'tenement',
        'blok': 'block_of_flats'
    })
    df.loc[~df['building_type'].fillna('').isin(['apartment', 'tenement', 'block_of_flats']), 'building_type'] = 'other'

    # Transform security
    # Create: gated_community, security_monitoring
    df['gated_community'] = df['security'].apply(
        lambda x: 1 if type(x)==str and 'teren zamknięty' in x else 0)
    df['security_monitoring'] = df['security'].apply(
        lambda x: 1 if type(x)==str and 'onitoring / ochrona' in x else 0)
    
    # Transform safeguards
    df['safeguards'] = df['safeguards'].apply(
        lambda x:1 if type(x)==str and\
        ('system alarmowy' in x or 'antywłamaniowe' in x) else 0)
    
    # Transform year_of_construction
    # Create: building_age
    df.loc[(df['year_of_construction'] < 1600) | (df['year_of_construction'] > 2025), 'year_of_construction'] = np.nan
    df['building_age'] = 2025 - df['year_of_construction']

    # Transform utilities
    df['cable_tv'] = df['utilities'].apply(
        lambda x: 1 if type(x)==str and 'telewizja kablowa' in x else 0)
    df['internet'] = df['utilities'].apply(
        lambda x: 1 if type(x)==str and 'internet' in x else 0)
    
    # Transform equipment / adv_description
    # Create: dishwasher, air_conditioning
    if utilize_morf:
        initialize_nlp()
        initialize_morf()

    df['dishwasher'] = df.apply(
        lambda row: (not pd.isna(row['equipment']) and 'zmywarka' in row['equipment']) or\
            (utilize_morf and contains_keywords_morf(row['adv_description'], ['zmywarka'])),
        axis=1).astype(int)
    df['air_conditioning'] = df.apply(
        lambda row: (not pd.isna(row['equipment']) and 'klimatyzacja' in row['equipment']) or\
            (utilize_morf and contains_keywords_morf(row['adv_description'], ['klimatyzacja', 'klimatyzator'])),
        axis=1).astype(int)
    
    # Transform district
    df['district'] = df['district'].apply(lambda x: replace_characters(str(x)))

    # Drop columns
    columns_to_drop = [
    'expired', 'expired_date',
    'rent_price', 'area_room_num', 'flat_condition',
    'available_from', 'deposit', 'additional_information',
    'year_of_construction', 'security', 'equipment',
    'utilities', 'days_difference',
    'rent_currency', 'additional_fees_currency', 'payment_frequency',
    'advertiser_type', 'approximate_coordinates']
    df = df.drop(columns=columns_to_drop)

    return df

def combine_rows(group):    
    # Get the index of the row with the latest added_dt
    idx_latest = group['added_dt'].idxmax()
    latest_row = group.loc[idx_latest].copy()
    
    # Replace the added_dt with the oldest added_dt in the group
    latest_row['added_dt'] = group['added_dt'].min()
    
    return latest_row

def deduplicate_main(main):
    
    df = main.copy()
    del main
    
    # Convert dates
    df['added_dt'] = df['added_dt'].apply(convert_date)
    df['last_update'] = df['last_update'].apply(convert_date)
    
    # If the added_dt < Dec 2024 replace it with last update date
    df.loc[df.added_dt.lt('2024-12-01')&(~df.last_update.isna()), 'added_dt'] = df['last_update']
    df = df[df.added_dt.ge('2024-12-01')].copy()
    
    # Dedup
    df = df.groupby('title', as_index=False).apply(combine_rows).reset_index(drop=True)
    df = df.sort_values(['added_dt', 'link']).reset_index(drop=True)
    
    return df

def distance_to_nearest_stop(df, stops_df):
    
    EARTH_RADIUS = 6371.0
    
    points_rad = np.deg2rad(df[['latitude', 'longitude']].values)
    stops_rad = np.deg2rad(stops_df[['stop_lat', 'stop_lon']].values)

    # Build a BallTree for the stops
    tree = BallTree(stops_rad, metric='haversine')

    # Find the nearest stop
    distances, indices = tree.query(points_rad, k=1)

    return distances.flatten() * EARTH_RADIUS

def distance_to_center(df):
    
    distance_series = df.apply(
        lambda row: round(hs.haversine(
            (row['latitude'], row['longitude']),
            (52.2297, 21.0122)),3), axis=1)
    
    return distance_series

def fill_column_with_stat(df: pd.DataFrame, column: str, method: str) -> None:
    """
    Fills missing values in the specified column of the DataFrame with a statistical measure
    (mode, median, or mean) based on the 'method' parameter.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing the data.
    - column (str): The name of the column to fill the missing values in.
    - method (str): The statistical method to use for filling ('mode', 'median', 'mean').

    Returns:
    - None: Modifies the DataFrame in place.
    """
    if method not in ['mode', 'median', 'mean']:
        raise ValueError("Method must be 'mode', 'median', or 'mean'")

    if method == 'mode':
        # Mode can return multiple values, we take the first one
        fill_value = df[column].mode().iloc[0]
    elif method == 'median':
        fill_value = df[column].median()
    elif method == 'mean':
        fill_value = df[column].mean()

    df[column].fillna(fill_value, inplace=True)

def input_missing_values(df: pd.DataFrame) -> None:
    columns_with_nans = df.columns[df.isna().any()].tolist()
    
    for col in columns_with_nans:
        if pdt.is_numeric_dtype(df[col].dtype):
            fill_column_with_stat(df, col, 'median')
        if pdt.is_string_dtype(df[col].dtype):
            fill_column_with_stat(df, col, 'mode')

def initialize_driver() -> selenium.webdriver.chrome.webdriver.WebDriver:  
    """
    Initializes and returns a Chrome WebDriver instance that navigates to Google Maps and handles an initial cookie acceptance popup.

    This function creates a new instance of the Chrome WebDriver, navigates to the Google Maps URL, and waits briefly to ensure the page loads correctly. It then finds and clicks the 'Accept All' button for cookies using an XPATH selector to handle site permissions before the actual automation tasks can be performed.

    Returns:
    - selenium.webdriver.chrome.webdriver.WebDriver: A WebDriver instance with the Google Maps page loaded and initial dialogs handled.
    """
    
    driver = webdriver.Chrome()
    driver.get('https://www.google.com/maps')

    sleep(0.5)
    driver.find_element(By.XPATH, '//button/span[text()="Zaakceptuj wszystko"]').click()
    sleep(0.5)
    
    return driver

def get_location(
    driver: selenium.webdriver.chrome.webdriver.WebDriver,
    address: str) -> list:
    """
    Retrieves the geographic coordinates of an address by inputting it into Google Maps and extracting the coordinates from the resulting URL.

    Parameters:
    - driver (selenium.webdriver.chrome.webdriver.WebDriver): An instance of a Selenium WebDriver, specifically configured for Chrome.
    - address (str): The address for which geographic coordinates are to be retrieved.

    Returns:
    - list: A list containing the latitude and longitude as strings.
    """
    
    sleep(2)
    input_box = driver.find_element(By.XPATH, '//input[@id="searchboxinput"]')
    input_box.clear()
    sleep(2)
    input_box.send_keys(address)
    driver.find_element(By.XPATH, '//button[@id="searchbox-searchbutton"]').click()
    sleep(4)
    current_url = driver.current_url
    
    geo_location = re.search('@(.*),',str(current_url)).group(1).split(',')
    
    return geo_location

def add_geo_location(df: pd.DataFrame) -> pd.DataFrame:
    """
    Updates a pandas DataFrame with latitude and longitude coordinates for each row by querying Google Maps.

    Parameters:
    - df (pd.DataFrame): The DataFrame that contains at least a 'location' column and columns for 'latitude' and 'longitude' which may have missing values.

    Returns:
    - pd.DataFrame: The original DataFrame updated with latitude and longitude coordinates where they were missing.
    """
    
    if not df[['latitude', 'longitude']].isnull().values.any():
        return df
    
    driver = initialize_driver()
    sleep(1)
    for index, row in df.iterrows():
        if pd.isna(row['latitude']) and pd.isna(row['longitude']):
            geo_location = get_location(driver, row['location'])
            df.at[index, 'latitude'] = float(geo_location[0])
            df.at[index, 'longitude'] = float(geo_location[1])
            
    return df

def concat_csv_files(
    folder_path: str = 'data_raw',
    regex_pattern: str = r'^.*otodom_last7.*\.csv$') -> pd.DataFrame:
    """
    Reads all CSV files in a specified folder, filters them by a regex pattern, and concatenates them into a single DataFrame.

    Parameters:
    - folder_path (str): The path to the folder containing CSV files.
    - regex_pattern (str): The regex pattern to filter file names.

    Returns:
    - pd.DataFrame: A concatenated DataFrame containing data from all filtered CSV files.
    """

    dfs = []

    for filename in os.listdir(folder_path):
        if re.match(regex_pattern, filename):
            file_path = os.path.join(folder_path, filename)
            dfs.append(pd.read_csv(file_path))
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()
    
def get_numbers(input_string : str) -> float:
    """
    Extracts numbers from a given string and returns them as a float.

    This function iterates through each character in the input string, extracting digits and commas.
    Commas are then replaced with dots to conform to the float format. The result is converted to a float.

    Parameters:
    - input_string (str): The string from which numbers are to be extracted.

    Returns:
    - float: The extracted number in float format, with commas replaced by dots.

    Note:
    The function assumes there's only one numeric value in the input string and that commas are used as decimal separators.
    """

    extract = ""
    for s in input_string:
        if (s.isdigit() or s == ",") and s!= '²':
            extract = extract + s
    try:
        extract = float(extract.replace(',', '.'))
    except ValueError:
        extract = np.nan
    
    return(extract)

def compute_average(indices, legacy_data):
    """
    Calculate the average 'log_price_per_square' for the given indices in legacy_data.
    If no indices are provided, return 0.
    """
    if len(indices) > 0:
        return legacy_data.iloc[indices]['price_per_square'].mean()
    else:
        return 0
    
def average_price_within_radius(df, legacy_data, radius_km=0.5):
    """
    For each point in df, compute the average log_price_per_square from legacy_data 
    for points that lie within a given radius (default 0.5 km).
    Returns the updated dataframe with a new column 'avg_log_price'.
    """

    EARTH_RADIUS = 6371.0
    radius_rad = radius_km / EARTH_RADIUS

    legacy_coords_rad = np.deg2rad(legacy_data[['latitude', 'longitude']].values)
    tree = BallTree(legacy_coords_rad, metric='haversine')
    df_coords_rad = np.deg2rad(df[['latitude', 'longitude']].values)
    neighbors_indices = tree.query_radius(df_coords_rad, r=radius_rad)

    return [compute_average(indices, legacy_data) for indices in neighbors_indices]