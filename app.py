from flask import Flask, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import threading
import time
import os

app = Flask(__name__)
CORS(app)

cached_data = []
last_updated = None

def scraper_loop():
    global cached_data, last_updated
    while True:
        new_data = scrape_parking_data()
        if new_data:
            cached_data = new_data
            last_updated = time.strftime('%Y-%m-%d %H:%M:%S')
        time.sleep(60)

threading.Thread(target=scraper_loop, daemon=True).start()

@app.route('/api/parking')
def get_parking():
    return jsonify({'lastUpdated': last_updated, 'data': cached_data})

@app.route('/api/predict')
def predict():
    return jsonify(prediction_model())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
