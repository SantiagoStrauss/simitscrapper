from flask import Flask, request, jsonify, Response
from simit import simitScraper, RegistraduriaData
import json

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    nuip = data.get('nuip')
    if not nuip:
        return jsonify({'error': 'NUIP is required'}), 400

    scraper = simitScraper(headless=True)
    scraped_data = scraper.scrape(nuip)

    if not scraped_data:
        return jsonify({'error': 'No data found for the provided NUIP'}), 404

    # Convert the dataclass to a dictionary for JSON serialization
    response_data = scraped_data.__dict__
    return Response(json.dumps(response_data, ensure_ascii=False), mimetype='application/json'), 200

if __name__ == '__main__':
    app.run(debug=True)