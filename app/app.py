from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# Replace with your actual Adzuna API credentials
ADZUNA_APP_ID = '82916c82'
ADZUNA_APP_KEY = '1bbbd36d21b6b11e346a89f3a609ecd7'

# Country code mapping
COUNTRY_CODES = {
    "india": "in",
    "united states": "us",
    "united kingdom": "gb",
    "australia": "au",
    "canada": "ca",    # Added Canada
    "germany": "de"    # Added Germany
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_jobs', methods=['POST'])
def get_jobs():
    data = request.get_json()
    role = data.get('role', '')
    location = data.get('location', '')
    results_per_page = int(data.get('results_per_page', 10))

    # Get the country code based on the selected location
    country_code = COUNTRY_CODES.get(location.lower(), 'in')  # Default to 'in' (India)

    # Adjusted URL to work dynamically with the country code
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"

    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'what': role,
        'where': location,
        'results_per_page': results_per_page,
        'content-type': 'application/json'
    }

    try:
        # Make the request to the Adzuna API
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        jobs = response.json().get('results', [])
        return jsonify(jobs)  # Return jobs as JSON response
    except requests.exceptions.RequestException as e:
        print("API Error:", e)
        return jsonify({'error': 'Failed to fetch jobs from API'}), 500

if __name__ == '__main__':
    app.run(debug=True)
