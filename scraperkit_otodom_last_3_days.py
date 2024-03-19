from scraper import *

first_page_url = 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?distanceRadius=0&limit=36&daysSinceCreated=3&by=DEFAULT&direction=DESC&viewType=listing&page=1'

run_otodom_scraper(
    first_page_url = first_page_url,
    add_filtered_links = False, 
    filtered_links_dict = {},
    return_df = False,
    sleep_length = 1,
    save_as_csv = True,
    csv_file_name_prefix = 'otodom_last3',
    csv_destination_path = 'data_raw',
)