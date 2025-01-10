import pandas as pd
from scraper import *
from datakit import *
from datetime import datetime
from ydata_profiling import ProfileReport

def daily_data_run(
    main_path: str = 'data_processed/main.csv',
    new_announcements_url: str = 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?limit=36&daysSinceCreated=7&by=DEFAULT&direction=DESC&viewType=listing&page=2',
    sleep_length: int = 2,
    search_for_inactive_destination_path: str = 'data_raw/search_for_inactive',
    get_links_destination_path: str = 'data_raw/available_ads',
    scrape_otodom_destination_path: str = 'data_raw/otodom_scraped_data',
    report_destination_path: str = 'data_raw/data_reports'):

    # Read main
    main = pd.read_csv(main_path)

    ### TODO Add rent price updates
    # Search for inactive
    inactive = search_for_inactive(
        list(main[main.expired.eq(0)].link),
        csv_destination_path = search_for_inactive_destination_path,
        sleep_length = sleep_length/2)
    inactive = inactive[inactive.expired.eq(1)]

    # Update main with inactive
    main.update(main[['link']].merge(inactive, on='link', how='left'), overwrite=True)

    # Search for new announcement links
    new_announcements = get_links_titles(
        new_announcements_url,
        sleep_length = sleep_length/2,
        csv_destination_path = get_links_destination_path)

    # Scrape new announcements
    driver = initialize_otodom_scraper(2)
    links = list(set(new_announcements.link)-set(main.link))

    new_records = scrape_otodom_announcements(
        driver = driver,
        announcements_links = links,
        sleep_length = sleep_length,
        csv_destination_path = scrape_otodom_destination_path)

    driver.close()

    # Process scrabed announcements
    new_records = process_data(new_records)
    new_records = new_records[~new_records.link.isin(main.link)]

    # Concat main and newly scraped announcements
    main = pd.concat([main, new_records], ignore_index=True)

    # Save main
    main.to_csv(main_path,
            encoding='utf-8',
            index=False)

    # Create profile report for newly scraped announcements
    current_date = datetime.now().strftime('%Y_%m_%d')
    profile = ProfileReport(new_records, title='Data Profiling Report')
    profile.to_file(f'{report_destination_path}/scraped_announcements_{current_date}.html')

    return None