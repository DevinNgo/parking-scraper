from flask import Flask, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import threading
import time
import os

from scraper import scrape_parking_data
from model import prediction_model

app = Flask(__name__)
CORS(app)

# Cache for scraped data
cached_data = []
last_updated = None

cached_predictions = {}
last_predicted = None

try:
    cached_predictions = prediction_model()
    last_predicted = time.strftime('%Y-%m-%d %H:%M:%S')
except Exception as e:
    app.logger.error(f"Initial prediction_model() failed: {e}")

def prediction_loop():
    global cached_predictions, last_predicted
    while True:
        try:
            preds = prediction_model()
            cached_predictions = preds
            last_predicted = time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            app.logger.error(f"prediction_loop error: {e}")
        time.sleep(12 * 3600)
        

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
    return jsonify({'lastPredicted': last_predicted, 'predictions': cached_predictions})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)