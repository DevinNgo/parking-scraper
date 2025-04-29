# scraper.py

from bs4 import BeautifulSoup
import requests
import time

def scrape_parking_data():
    # Scrapes the CSUF parking website and returns a list of parking data.
    try:
        url = 'https://parking.fullerton.edu/parkinglotcounts/mobile.aspx'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('table#GridView_All tr')
        results = []

        for row in rows:
            location_tag = row.select_one('.LocationName a') or row.select_one('.LocationName span')
            location = location_tag.text.strip() if location_tag else None

            total = row.find('span', id=lambda x: x and 'GridView_All_Label_Avail_' in x)
            available = row.find('span', id=lambda x: x and 'GridView_All_Label_AllSpots_' in x)
            updated = row.find('span', id=lambda x: x and 'GridView_All_Label_LastUpdated_' in x)

            if location:
                results.append({
                    'structure': location,
                    'totalSpots': total['aria-label'] if total else None,
                    'availableSpots': available.text.strip() if available else None,
                    'lastUpdated': updated['aria-label'] if updated else None
                })

        return results

    except Exception as e:
        print("Error scraping:", e)
        return []
