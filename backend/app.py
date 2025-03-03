# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib.robotparser
import logging
import spacy
from datetime import datetime

app = Flask(__name__)


# Allow requests from http://localhost:5173
CORS(app, origins=["http://localhost:5173"])


# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error(
        "spaCy model not found. Run: python -m spacy download en_core_web_sm")
    raise

# Emergency keywords and severity points
EMERGENCY_KEYWORDS = {
    "hurricane": 5,
    "accident": 2,
    "injury": 2,
    "emergency": 7,
    "rescue": 1,
    "evacuation": 4,
    "chemical spill": 7,
    "flood": 2,
    "fire": 5,
    "medical": 4,
    "storm": 2,
    "casualty": 6,
    "disaster": 7,
    "critical": 6,
    "danger": 4,
    "lost": 1,
    "Missing": 1,
    "flame": 5,
    "acid rain": 6
}

# Trust-related keywords and trust points
TRUST_KEYWORDS = {
    "confirmed": 10,
    "verified": 10,
    "official": 8,
    "reported": 5,
    "estimated": 3,
    "testified": 4,
    "accounted": 2,
}


def get_severity_level(points):
    if points >= 35:
        return "high"
    elif points >= 20:
        return "medium"
    else:
        return "low"


def get_trust_score(trust_points, base_score=50):
    """
    Calculate the trust score based on trust-related keywords.

    Parameters:
        trust_points (int): Total points from trust-related keywords.
        base_score (int): The base trust score before adjustments.

    Returns:
        int: Adjusted trust score, capped between 0 and 100.
    """
    trust_score = base_score + trust_points
    # Ensure trust score is between 0 and 100
    trust_score = max(min(trust_score, 100), 0)
    return trust_score


def can_fetch(url, user_agent='*'):
    """
    Check if the scraper is allowed to fetch the given URL based on the site's robots.txt.

    Parameters:
        url (str): The URL to check.
        user_agent (str): The user agent to use for checking permissions.

    Returns:
        bool: True if fetching is allowed, False otherwise.
    """
    parsed_url = requests.utils.urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        logger.warning("Could not read robots.txt for %s: %s", url, e)
        return False


def extract_emergency_info(text):
    """
    Extracts emergency-related keywords and calculates severity and trust scores.

    Parameters:
        text (str): The text to analyze.

    Returns:
        dict: Contains keywords, points, severity, location, and trustScore.
    """
    doc = nlp(text.lower())

    # Extract emergency-related keywords and calculate severity points
    severity_points = 0
    emergency_keywords_found = []

    for keyword, points in EMERGENCY_KEYWORDS.items():
        if keyword in text.lower():
            severity_points += points
            emergency_keywords_found.append(keyword)

    severity = get_severity_level(severity_points)

    # Extract trust-related keywords and calculate trust points
    trust_points = 0
    trust_keywords_found = []

    for keyword, points in TRUST_KEYWORDS.items():
        if keyword in text.lower():
            trust_points += points
            trust_keywords_found.append(keyword)

    trust_score = get_trust_score(trust_points)

    # Extract location entities using spaCy
    locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
    location = locations[0] if locations else "Unknown Location"

    # Combine all keywords
    all_keywords = emergency_keywords_found + trust_keywords_found

    return {
        'keywords': all_keywords,
        'points': severity_points,
        'severity': severity,
        'location': location,
        'trustScore': trust_score
    }


# In-memory storage for incidents (For demonstration purposes)
incidents_db = []


@app.route('/scrape', methods=['POST'])
def scrape_url():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    if not can_fetch(url):
        return jsonify({'error': 'Scraping not allowed for this URL'}), 403

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract main content
        content = ' '.join([p.get_text() for p in soup.find_all('p')])
        title = soup.title.string if soup.title else "Unknown Title"

        # Process the content
        emergency_info = extract_emergency_info(content)

        # Create incident data
        incident = {
            'id': len(incidents_db) + 1,  # Incremental ID
            'type': emergency_info['keywords'][0] if emergency_info['keywords'] else 'general',
            'title': title[:100],
            'location': emergency_info['location'],
            'severity': emergency_info['severity'],
            'points': emergency_info['points'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M %p'),
            'description': content[:200] + "...",
            'trustScore': emergency_info['trustScore'],
            'keywords': emergency_info['keywords']
        }

        # Add to the in-memory database
        incidents_db.append(incident)

        return jsonify(incident)

    except requests.exceptions.RequestException as e:
        logger.error("Error scraping URL: %s", str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/get-incidents', methods=['GET'])
def get_incidents():
    """
    Endpoint to retrieve all incidents.
    """
    return jsonify(incidents_db)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
