from modules.scraper import *

first_page_url = 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?ownerTypeSingleSelect=ALL&viewType=listing'

run_otodom_scraper(
    first_page_url = first_page_url,
    add_filtered_links = False, 
    filtered_links_dict = {},
    return_df = False,
    sleep_length = 1,
    save_as_csv = True,
    csv_file_name_prefix = 'otodom',
    csv_destination_path = 'data_raw/otodom_scraped_data',
)