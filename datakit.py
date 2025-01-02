import pandas as pd

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

def extract_ad_dates(row):
    """
    Extracts and returns the last update date and added date from an advertisement's metadata.

    The function processes a given row from a DataFrame, which contains an 'announcement_date' field
    with metadata formatted as strings separated by newline characters. It identifies and extracts 
    lines containing 'Aktualizacja:' (last update) and 'Dodano:' (added date). If either date is not found, 
    the corresponding return value is None.

    Parameters:
    - row (pd.Series): A row from a DataFrame containing an 'announcement_date' field.

    Returns:
    - pd.Series: A series containing two elements:
        - The last update date as a string (or None if not available).
        - The added date as a string (or None if not available).
    """
    # Extract the 'announcement_date' field from the row
    ad_info = row['announcement_date']
    
    # Extract the last update date if the line contains 'Aktualizacja:'
    update_date_part = [line for line in ad_info.split('\\n') if 'Aktualizacja:' in line]
    last_update = update_date_part[0].replace("('Aktualizacja: ", '').strip() if update_date_part else None
    
    # Extract the added date if the line contains 'Dodano:'
    added_date_part = [line for line in ad_info.split('\\n') if 'Dodano:' in line]
    ad_added = added_date_part[0].replace('Dodano: ', '').strip() if added_date_part else None
    
    # Return the extracted dates as a pandas Series
    return pd.Series([last_update, ad_added])

def process_data(data_draw):
    """
    Processes raw advertisement data to extract and organize relevant information.

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
    df[['last_update', 'added_dt']] = df.apply(extract_ad_dates, axis=1)
    
    # Drop the 'announcement_date' column as it is no longer needed
    df.drop(['announcement_date'], axis=1, inplace=True)
    
    # Reorder columns to place 'added_dt', 'last_update', and 'link' at the beginning
    columns_order = ['added_dt', 'last_update', 'link'] + \
                    [col for col in df.columns if col not in ['added_dt', 'last_update', 'link']]
    df = df[columns_order]
    
    return df