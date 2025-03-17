from datakit import *

# Read and transform data
path = f'data_processed/main_new.csv'
df = pd.read_csv(path)

df = deduplicate_main(df)
df = transform_data(
    main = df,
    only_expired = True,
    duration_start = 1,
    duration_end = 28,
    utilize_morf = False
)

# District Keywords
district_keywords_mapping = {
    'Srodmiescie': ['Śródmieście', 'Śródmieściu', 'Śródmieścia', 'Śródmieściem'],
    'Wola': ['Wola', 'Woli'],
    'Mokotow': ['Mokotów', 'Mokotowa', 'Mokotowem', 'Mokotowie'],
    'Praga_Poludnie': ['Praga', 'Pragi', 'Pradze', 'Pragę', 'Pragą'],
    'Praga_Polnoc': ['Praga', 'Pragi', 'Pradze', 'Pragę', 'Pragą'],
    'Ochota': ['Ochota', 'Ochocie', 'Ochoty'],
    'Ursynow': ['Ursynów', 'Ursynowie', 'Ursynowa'],
    'Wawer': ['Wawer', 'Wawrze'],
    'Bielany': ['Bielany', 'Bielan', 'Bielanami', 'Bielanach'],
    'Wlochy': ['Włochy', 'Włoszech', 'Włochach'],
    'Bemowo': ['Bemowo', 'Bemowa', 'Bemowem', 'Bemowie'],
    'Rembertow': ['Rembertów', 'Rembertowa', 'Rembertowem', 'Rembertowie'],
    'Targowek': ['Targówek', 'Targówka', 'Targówkiem', 'Targówku'],
    'Wesola': ['Wesoła', 'Wesołej'],
    'Zoliborz': ['Żoliborz', 'Żoliborza', 'Żoliborzem', 'Żoliborzu'],
    'Bialoleka': ['Białołęka', 'Białołęce', 'Białołęki', 'Białołęką'],
    'Ursus': ['Ursus', 'Ursusa', 'Ursusie'],
    'Wilanow': ['Wilanów', 'Wilanowa', 'Wilanowem', 'Wilanowie']
}

# Find announcments to be checked for misleading locations
district_keywords = [d.lower() for sublist in district_keywords_mapping.values() for d in sublist]
df_check = df.copy()

def check_advert(row):
    found_districts = []
    
    # Combine description and title and convert the text to lowercase
    text = (str(row['adv_description']) + " " + str(row['title'])).lower()
    
    # Check if any district is mentioned in the text
    for district in district_keywords:
        if district in text:
            found_districts.append(district)
            
    # Compere with provided district
    row_district = str(row['district'])
    row_district_keywords = [d.lower() for d in district_keywords_mapping[row_district]]
    if any([i in row_district_keywords for i in found_districts]):
        return None
            
    return ", ".join(found_districts) if found_districts else None

# Apply the function to each row and create the 'found_district' column
df_check['found_district'] = df_check.apply(check_advert, axis=1)

# Save results
df_check['misleading_location'] = ''
df_check['real_address'] = ''
df_check['real_district'] = ''
df_check['maps_herf'] = ''

columns_to_save = [
    'added_dt', 'link', 'district',
    'found_district', 'title', 'adv_description',
    'misleading_location', 'real_address', 'real_district', 'maps_herf']

path = 'data_raw/manual_input/location_to_be_checked.csv'
df_check[df_check.found_district.notnull()][columns_to_save].to_csv(path)