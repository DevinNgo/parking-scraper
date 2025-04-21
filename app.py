from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
import threading
import time

app = Flask(__name__)
cached_data = []
last_updated = None

def scrape_data():
    global cached_data, last_updated
    while True:
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

            cached_data = results
            last_updated = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{last_updated}] Scraped successfully.")
        except Exception as e:
            print("Error scraping:", e)
        
        time.sleep(60)  # run every minute

threading.Thread(target=scrape_data, daemon=True).start()

@app.route('/api/parking')
def get_parking():
    return jsonify({
        'lastUpdated': last_updated,
        'data': cached_data
    })

if __name__ == '__main__':
    app.run(debug=True)