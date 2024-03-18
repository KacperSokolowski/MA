import pandas as pd
import numpy as np
import haversine as hs

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
    for station, coords in locations.items():
        loc1 = (coords['Latitude'], coords['Longitude'])
        loc2 = (lat, lon)
        dist_lst.append(hs.haversine(loc1, loc2))
    
    return round(min(dist_lst), 3)

def scrub_scraped_data(
        df : pd.DataFrame,
        subway_locations : dict = {}) -> pd.DataFrame:

    # Copy df
    df = df.copy()

    # Step 1 apply apply get_numbers function to specific columns
    columns_to_convert = ['rent_price', 'additional_fees', 'area']
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
    
    # Step 4 Create binary columns from building_type
    df['bt_apartment'] = df['building_type'].str.contains('apartment')
    df['bt_tenement'] = df['building_type'].str.contains('kamienica')
    df['bt_block'] = df['building_type'].str.contains('blok')
    df['bt_other'] = ~(df['bt_apartment'] | df['bt_tenement'] | df['bt_block'])
    df.drop(['building_type'], axis=1, inplace=True)

    # Step 5 Create binary columns from furnishings
    df['dishwasher'] = df['furnishings'].str.contains('zmywarka')
    

    # Step 6 Create binary columns from building_type

    return df