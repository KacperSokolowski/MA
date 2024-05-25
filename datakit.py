import pandas as pd
import numpy as np
import os
import re
import haversine as hs
import spacy
import morfeusz2
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep

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

def nearest_distance(lat: float, lon: float,
                     locations : dict) -> float:
    """
    Calculates and returns the minimum distance from a given latitude and longitude to a set of predefined locations.

    This function iterates through a dictionary of locations, each defined by its name and a dictionary containing its latitude and longitude, 
    and calculates the distance from the provided latitude and longitude to each location using the Haversine formula. 
    It returns the shortest distance found.

    Parameters:
    - lat (float): The latitude of the point from which the distance is to be calculated.
    - lon (float): The longitude of the point from which the distance is to be calculated.
    - locations (dict): A dictionary where keys are points names and values are dictionaries with keys 'Latitude' and 'Longitude' representing each point's location.

    Returns:
    - int: The shortest distance to the nearest location, rounded to to 3 decimal points.

    Requires:
    - An external Haversine formula implementation (hs.haversine) to calculate the distance between two latitude/longitude points.
    """

    if not locations:
        return np.nan
    
    dist_lst = []
    for coords in locations.values():
        loc1 = (coords['Latitude'], coords['Longitude'])
        loc2 = (lat, lon)
        dist_lst.append(hs.haversine(loc1, loc2))
    
    return round(min(dist_lst), 3)

def contains_keywords_nlp(description: str, keywords: list,
                          negations: list = ['nie', 'brak'],
                          negation_distance: int = 2) -> bool:
    """
    Determines whether a textual description contains any specified keywords and considers the influence of nearby negation words.

    This function processes a text description using a natural language processing model to break the text into sentences and tokenize them.
    For each sentence, it checks if any of the provided keywords are present and then examines if any negation words are
    close enough to potentially negate the meaning of the keyword. The function returns True if a keyword is found without
    a nearby negation that affects its context, and it stops further analysis once a valid keyword is detected.

    Parameters:
    - description (str): The text description to analyze for the presence of keywords.
    - keywords (list): A list of keywords to search for in the description.
    - negations (list): A list of negation words (default includes 'nie', 'brak') that can alter the context of the keywords.
    - negation_distance (int): The maximum allowable distance (in terms of token indices) between a keyword and a negation word to consider the keyword negated.

    Returns:
    - bool: True if at least one keyword is found in the description without being negated, False otherwise.

    Requires:
    - A loaded natural language processing model (nlp) to tokenize the text and extract sentences and tokens.
    """
    try:
        doc = nlp(description.lower())
    except AttributeError:
        return False
    
    contains_keywords = False
    for sentence in doc.sents:
        keywords_presence = [token for token in sentence if token.lemma_ in keywords]
        negation_presence = [token for token in sentence if token.lemma_ in negations]
        
        # Check if any negation is close to a furniture keyword
        if keywords_presence:
            contains_keywords = not any(negation.i < keyword_token.i + negation_distance and negation.i > keyword_token.i - negation_distance
                                 for negation in negation_presence
                                 for keyword_token in keywords_presence)
            if contains_keywords:
                break

    return contains_keywords

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

def remove_duplicates(
    df: pd.DataFrame,
    column_name: str = 'link'):
    """
    Removes duplicates from the DataFrame based on the specified column name.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.
    - column_name (str): The name of the column to check for duplicates.

    Returns:
    - pd.DataFrame: The DataFrame with duplicates removed.
    """
    df = df.copy()
    df = df.drop_duplicates(subset=column_name)

    return df

def scrub_data(
    df : pd.DataFrame,
    subway_locations : dict = {}) -> pd.DataFrame:

    # Copy df
    df = df.copy()

    # Step 1 apply get_numbers function to specific columns
    columns_to_convert = ['rent_price', 'additional_fees', 'area', 'room_num']
    for column in columns_to_convert:
        df[column] = df[column].apply(lambda x: get_numbers(str(x)))

    # Step 2 get district name from location, drop location,
    # Remove observations outside of Warsaw,
    # Remove Polish characters from district names
    df['district'] = df['location'].apply(lambda x: find_warsaw_district(str(x)))
    df.drop(['location'], axis=1, inplace=True)
    df = df[~df.district.isna()]
    df['district'] = df['district'].apply(lambda x: replace_characters(str(x)))

    # Step 3 calcuate distance to nearest subway and to city center
    if subway_locations:
        df['subway_distance'] = df.apply(lambda row: nearest_distance(row['latitude'], row['longitude'], subway_locations), axis=1)

    df['center_distance'] = df.apply(lambda row: round(hs.haversine(
        (row['latitude'], row['longitude']), (52.2297, 21.0122)),3), axis=1)

    # Step 4 Determine whether apartment is furnished - create binary column
    initialize_nlp()

    furnishing_keywords = [
    'umeblowany', 'umeblowana', 'umeblowane',
    'wyposażony', 'wyposażona', 'wyposażone',
    'meble', 'meblami'
    'łóżko', 'łóżkiem', 'łóżkami'
    'sofa', 'sofą', 'sofami'
    'szafa', 'szafą', 'szafami'
    'pralka', 'pralką']

    df['is_furnished'] = df.apply(
        lambda row: not pd.isna(row['furnishings']) or contains_keywords_nlp(row['adv_description'], furnishing_keywords),
        axis=1)

    # Step 5 Determine whether apartment has a dishwasher - create binary column
    # Drop furnishings column
    initialize_morf()

    dishwasher_keywords = ['zmywarka']

    df['dishwasher'] = df.apply(
        lambda row: (not pd.isna(row['furnishings']) and 'zmywarka' in row['furnishings']) or\
            contains_keywords_morf(row['adv_description'], dishwasher_keywords),
        axis=1)
    df.drop(['furnishings'], axis=1, inplace=True)
    
    # Step 6 Determine whether the apartment has air conditioning - create binary column
    # Drop adv_description column
    air_conditioning_keywords = ['klimatyzacja', 'klimatyzator']

    df['air_conditioning'] = df.apply(
        lambda row: (not pd.isna(row['additional_information']) and 'klimatyzacja' in row['additional_information']) or\
            contains_keywords_morf(row['adv_description'], air_conditioning_keywords),
        axis=1)
    df.drop(['adv_description'], axis=1, inplace=True)

    # Step 7 Determine whether the apartment have to be renovated
    # Drop flat_condition column
    df['for_renovation'] = df['flat_condition'].apply(
        lambda x: False if pd.isna(x) or x == 'do zamieszkania' else True)
    df.drop(['flat_condition'], axis=1, inplace=True)

    # Step 8 Adjust students_allowed column to binary form
    df['students_allowed'] = df['students_allowed'].apply(lambda x: x == 'tak')

    # Step 9 Adjust elevator column to binary form
    df['elevator'] = df['elevator'].apply(lambda x: x == 'tak')

    # Step 10 Adjust parking_space column to binary form
    df['parking_space'] = ~df.parking_space.isna()

    # Step 11 Adjust floor column; create column building_height
    df[['floor', 'building_height']] = df['floor'].apply(lambda x: pd.Series(parse_floor_values(x)))

    # Step 12 Adjust room_num to int data type
    df['room_num'] = df['room_num'].astype(int)

    # Step 13 Sum up additional_fees to rent_price
    # Drop rent_price column
    df['rent_price'] = df.apply(
    lambda row: row['rent_price'] + row['additional_fees'] if not pd.isna(row['additional_fees']) else row['rent_price'], 
    axis=1)

    df.drop(['additional_fees'], axis=1, inplace=True)

    # Step 14 Change all columns with a Boolean dtype to an int dtype
    df = df.apply(lambda x: x.astype(int) if x.dtype == 'bool' else x)

    # Step 15 Drop link column
    df.drop(['link'], axis=1, inplace=True)
    
    return df

def modeling_preprocessing(df : pd.DataFrame) -> pd.DataFrame:

    # Copy df
    df = df.copy()

    # Step 1 Create binary columns from building_type
    df['bt_apartment'] = df['building_type'].str.contains('apartment')
    df['bt_tenement'] = df['building_type'].str.contains('kamienica')
    df['bt_block'] = df['building_type'].str.contains('blok')
    df['bt_other'] = ~(df['bt_apartment'] | df['bt_tenement'] | df['bt_block'])
    df.drop(['building_type'], axis=1, inplace=True)

    # Step 2 Create binary columns from advertiser_type
    # Drop advertiser_type column
    df['at_private'] = df.advertiser_type.str.contains('prywatny')
    df['at_agency'] = df.advertiser_type.str.contains('biuro nieruchomości')
    df['at_developer'] = df.advertiser_type.str.contains('deweloper')
    df.drop(['advertiser_type'], axis=1, inplace=True)

    # Step 3 Create binary columns from extra_space
    # Drop extra_space column
    df['balcony'] = df['extra_space'].apply(lambda x: True if type(x)==str and 'balkon' in x else False)
    df['terrace'] = df['extra_space'].apply(lambda x: True if type(x)==str and 'taras' in x else False)
    df['garden'] = df['extra_space'].apply(lambda x: True if type(x)==str and 'ogródek' in x else False)
    df.drop(['extra_space'], axis=1, inplace=True)

    # Step 4 Create binary columns from year_of_construction
    # Drop year_of_construction column
    df['cy_old_building'] = np.where(df['year_of_construction'] <= 1950, True, False)
    df['cy_new_building'] = np.where(df['year_of_construction'] >= 2000, True, False)
    df['cy_other'] = np.where(~df['cy_old_building'] & ~df['cy_new_building'], True, False)
    df.drop(['year_of_construction'], axis=1, inplace=True)

    # Step 5 Create binary columns from district
    # Drop district column
    df = pd.get_dummies(df, columns=['district'])

    # Step 6 Change all columns with a Boolean dtype to an int dtype
    df = df.apply(lambda x: x.astype(int) if x.dtype == 'bool' else x)

    # Step 7 Drop latitude, longitude columns
    df.drop(['latitude', 'longitude'], axis=1, inplace=True)

    # Step 8 Fill missing values
    fill_column_with_stat(df, 'floor', 'mode')
    fill_column_with_stat(df, 'building_height', 'mode')

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
    
    input_box = driver.find_element(By.XPATH, '//input[@class="searchboxinput xiQnY"]')
    input_box.clear()
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
    
    driver = initialize_driver()
    for index, row in df.iterrows():
        if pd.isna(row['latitude']) and pd.isna(row['longitude']):
            geo_location = get_location(driver, row['location'])
            df.at[index, 'latitude'] = float(geo_location[0])
            df.at[index, 'longitude'] = float(geo_location[1])
            
    return df

def fix_missing_locations(
    folder_path: str = 'data_raw',
    regex_pattern: str = r'^.*otodom_last7.*\.csv$') -> None:
    
    """
    Processes each CSV file in a specified directory that matches a given regex pattern, 
    updating missing geographic coordinates in the 'latitude' and 'longitude' columns.

    Parameters:
    - folder_path (str): The directory path where CSV files are stored. Defaults to 'data_raw'.
    - regex_pattern (str): A regex pattern to match file names that should be processed. 
        Defaults to r'^.*otodom_last7.*\.csv$', which targets files typically named according to a convention 
        used for weekly data dumps from the website Otodom.

    Returns:
    - None: This function does not return a value but writes directly to the CSV files.
    """
    
    for filename in os.listdir(folder_path):
        if re.match(regex_pattern, filename):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            df = add_geo_location(df)
            df.to_csv(file_path, encoding='utf-8', index=False)
            
    return None