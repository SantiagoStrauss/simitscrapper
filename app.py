from flask import Flask, request, jsonify
from cemail import CompromisedEmailScraper, CompromisedData

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    scraper = CompromisedEmailScraper(headless=True)
    target_url = "https://whatismyipaddress.com/breach-check"
    scraped_data = scraper.scrape(target_url, email)

    return jsonify([data.__dict__ for data in scraped_data])

if __name__ == '__main__':
    app.run(debug=True)