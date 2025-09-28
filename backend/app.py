# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib.robotparser
import logging
import spacy
from datetime import datetime
import feedparser
import re
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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


@app.route('/debug/logs', methods=['GET'])
def get_debug_logs():
    """
    Debug endpoint to see recent activity.
    """
    return jsonify({
        'total_incidents': len(incidents_db),
        'recent_incidents': incidents_db[-5:] if incidents_db else [],
        'server_status': 'running'
    })


@app.route('/get-local-incidents', methods=['POST'])
def get_local_incidents():
    """
    Endpoint to scrape and analyze local news for incidents based on user location.
    """
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    logger.info(f"=== NEW REQUEST ===")
    logger.info(f"Received coordinates: lat={latitude}, lng={longitude}")
    
    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        # Get location name from coordinates
        logger.info(f"Looking up location for coordinates: {latitude}, {longitude}")
        geolocator = Nominatim(user_agent="crisis-compass")
        location = geolocator.reverse(f"{latitude}, {longitude}", language='en')
        location_name = location.address if location else "Unknown Location"
        
        logger.info(f"Detected location: {location_name}")
        
        # Extract city/region name for news search
        city_name = extract_city_name(location_name)
        logger.info(f"Extracted city name: {city_name}")
        
        # Scrape local news
        logger.info(f"Starting news scraping for city: {city_name}")
        local_incidents = scrape_local_news(city_name, latitude, longitude)
        logger.info(f"Found {len(local_incidents)} incidents")
        
        # Add to incidents database
        for incident in local_incidents:
            incidents_db.append(incident)
        
        logger.info(f"=== REQUEST COMPLETE ===")
        return jsonify(local_incidents)
        
    except Exception as e:
        logger.error("Error getting local incidents: %s", str(e))
        return jsonify({'error': str(e)}), 500


def is_recent_article(entry):
    """
    Check if an article is within the last week.
    """
    try:
        # Get the article's published date
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            article_date = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            article_date = datetime(*entry.updated_parsed[:6])
        else:
            # If no date available, assume it's recent
            return True
        
        # Calculate the difference
        now = datetime.now()
        time_diff = now - article_date
        
        # Check if it's within the last 30 days (more reasonable for emergency news)
        is_recent = time_diff.days <= 30
        
        if not is_recent:
            logger.info(f"Article too old: {article_date.strftime('%Y-%m-%d')} ({(now - article_date).days} days ago)")
        
        return is_recent
        
    except Exception as e:
        logger.warning(f"Error checking article date: {str(e)}")
        # If we can't parse the date, assume it's recent
        return True


def is_recent_web_article(article, title):
    """
    Basic check for recent web articles (less reliable than RSS dates).
    """
    try:
        # Look for date indicators in the title or content
        title_lower = title.lower()
        
        # Skip articles with obvious old date indicators
        old_indicators = [
            '2022', '2021', '2020', '2019', '2018', '2017', '2016',
            'two years ago', 'last year', 'months ago', 'weeks ago',
            'may 2023', 'april 2023', 'march 2023', 'february 2023', 'january 2023'
        ]
        
        for indicator in old_indicators:
            if indicator in title_lower:
                return False
        
        # Look for recent indicators
        recent_indicators = [
            'today', 'yesterday', 'this week', 'this month',
            '2024', '2025', 'recent', 'latest', 'breaking'
        ]
        
        for indicator in recent_indicators:
            if indicator in title_lower:
                return True
        
        # If no clear indicators, assume it's recent (better to include than exclude)
        return True
        
    except Exception as e:
        logger.warning(f"Error checking web article recency: {str(e)}")
        return True


def extract_city_name(location_string):
    """
    Extract city name from full location string.
    """
    if not location_string:
        return "Unknown"
    
    # Split by comma and take the first part (usually city)
    parts = location_string.split(',')
    city = parts[0].strip()
    
    # If we get a very specific location like "South Campus", try to get a broader area
    if any(keyword in city.lower() for keyword in ['campus', 'university', 'college', 'school']):
        # Look for the actual city name in the address
        for part in parts:
            part = part.strip()
            # Look for common city indicators
            if any(indicator in part.lower() for indicator in ['waterloo', 'toronto', 'ottawa', 'vancouver', 'montreal', 'calgary', 'edmonton']):
                return part
            # Look for state/province names that might indicate the city
            if any(province in part.lower() for province in ['ontario', 'quebec', 'british columbia', 'alberta']):
                # Try to find the city name before the province
                for i, p in enumerate(parts):
                    if province in p.lower() and i > 0:
                        return parts[i-1].strip()
    
    return city


def get_news_sources(city_name):
    """
    Get comprehensive list of news sources for a given city.
    """
    # Location-specific news sources (prioritize local over global)
    sources = [
        # Local news sources first - using RSS feeds instead of web scraping for better reliability
        {
            'name': f'Google News - {city_name} Local',
            'url': f'https://news.google.com/rss/search?q={city_name}+local+news&hl=en&gl=CA&ceid=CA:en',
            'type': 'rss',
            'category': 'local'
        },
        {
            'name': f'Google News - {city_name} Emergency',
            'url': f'https://news.google.com/rss/search?q={city_name}+emergency+disaster+incident&hl=en&gl=CA&ceid=CA:en',
            'type': 'rss',
            'category': 'local'
        },
        {
            'name': f'Google News - {city_name} Breaking',
            'url': f'https://news.google.com/rss/search?q={city_name}+breaking+news&hl=en&gl=CA&ceid=CA:en',
            'type': 'rss',
            'category': 'local'
        },
        {
            'name': f'Google News - {city_name} Fire Police',
            'url': f'https://news.google.com/rss/search?q={city_name}+fire+police+emergency&hl=en&gl=CA&ceid=CA:en',
            'type': 'rss',
            'category': 'local'
        },
        # Add broader regional searches
        {
            'name': f'Google News - Waterloo Ontario',
            'url': f'https://news.google.com/rss/search?q=waterloo+ontario+emergency&hl=en&gl=CA&ceid=CA:en',
            'type': 'rss',
            'category': 'regional'
        },
        {
            'name': f'Google News - Ontario Emergency',
            'url': f'https://news.google.com/rss/search?q=ontario+emergency+disaster&hl=en&gl=CA&ceid=CA:en',
            'type': 'rss',
            'category': 'regional'
        },
        # Canadian news sources
        {
            'name': 'CBC News Ontario',
            'url': 'https://www.cbc.ca/cmlink/rss-topstories',
            'type': 'rss',
            'category': 'national'
        },
        {
            'name': 'CTV News',
            'url': 'https://www.ctvnews.ca/rss/ctvnews-ca-topstories-public-rss-1.822289',
            'type': 'rss',
            'category': 'national'
        },
        # Removed BBC World News fallback to avoid international news
    ]
    
    return sources


def get_regional_news_sources(city_name):
    """
    Get regional news sources based on city name.
    """
    regional_sources = []
    
    # US-specific sources
    if any(state in city_name.lower() for state in ['new york', 'ny', 'california', 'ca', 'texas', 'tx']):
        regional_sources.extend([
            {
                'name': 'CNN Breaking News',
                'url': 'http://rss.cnn.com/rss/edition.rss',
                'type': 'rss',
                'category': 'national'
            },
            {
                'name': 'NPR News',
                'url': 'https://feeds.npr.org/1001/rss.xml',
                'type': 'rss',
                'category': 'national'
            }
        ])
    
    # Add more regional sources as needed
    return regional_sources


def scrape_news_website(source, city_name):
    """
    Scrape news website using BeautifulSoup.
    """
    incidents = []
    
    try:
        logger.info(f"Scraping website: {source['name']}")
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Make request with timeout
        response = requests.get(source['url'], headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find articles using the configured selectors
        articles = soup.select(source['selectors']['articles'])
        logger.info(f"Found {len(articles)} articles from {source['name']}")
        
        for article in articles[:15]:  # Limit to 15 articles
            try:
                # Extract title
                title_elem = article.select_one(source['selectors']['title'])
                title = title_elem.get_text().strip() if title_elem else "No title"
                
                # Extract content/description
                content_elem = article.select_one(source['selectors']['content'])
                content = content_elem.get_text().strip() if content_elem else ""
                
                # Extract link
                link_elem = article.select_one(source['selectors']['link'])
                link = link_elem.get('href') if link_elem else ""
                
                # Make link absolute if it's relative
                if link and not link.startswith('http'):
                    if link.startswith('/'):
                        from urllib.parse import urljoin
                        link = urljoin(source['url'], link)
                
                # Check if article appears recent (basic check for web scraping)
                if not is_recent_web_article(article, title):
                    logger.info(f"Skipping potentially old web article: {title[:50]}...")
                    continue
                
                # Combine title and content for analysis
                full_content = f"{title} {content}"
                
                # Analyze for emergency keywords
                emergency_info = extract_emergency_info(full_content)
                logger.info(f"Article analysis: '{title[:50]}...' -> points={emergency_info['points']}, keywords={emergency_info['keywords']}")
                
                # Only include if it has emergency keywords
                if emergency_info['points'] > 0:
                    incident = {
                        'id': len(incidents_db) + len(incidents) + 1,
                        'type': emergency_info['keywords'][0] if emergency_info['keywords'] else 'general',
                        'title': title[:100],
                        'location': emergency_info['location'] if emergency_info['location'] != 'Unknown Location' else city_name,
                        'severity': emergency_info['severity'],
                        'points': emergency_info['points'],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M %p'),
                        'description': full_content[:200] + "...",
                        'trustScore': emergency_info['trustScore'],
                        'keywords': emergency_info['keywords'],
                        'source': source['name'],
                        'url': link
                    }
                    incidents.append(incident)
                    logger.info(f"Added incident from {source['name']}: {incident['title']}")
                
            except Exception as e:
                logger.warning(f"Error processing article from {source['name']}: {str(e)}")
                continue
                
    except Exception as e:
        logger.warning(f"Error scraping {source['name']}: {str(e)}")
    
    return incidents


def scrape_local_news(city_name, latitude, longitude):
    """
    Scrape local news sources for incidents in the specified area.
    """
    incidents = []
    logger.info(f"Scraping local news for city: {city_name}")
    
    # Multi-source news aggregation
    news_sources = get_news_sources(city_name)
    
    for source in news_sources:
        try:
            logger.info(f"Checking news source: {source['name']} - {source['url']}")
            
            if source['type'] == 'rss':
                # Parse RSS feed
                feed = feedparser.parse(source['url'])
                logger.info(f"Found {len(feed.entries)} entries from {source['name']}")
                
                for entry in feed.entries[:10]:  # Limit to 10 most recent
                    # Check if article is within the last week
                    if not is_recent_article(entry):
                        logger.info(f"Skipping old article: {entry.title[:50]}...")
                        continue
                    
                    # Extract content from the entry
                    content = f"{entry.title} {entry.summary if hasattr(entry, 'summary') else ''}"
                    logger.info(f"Processing local news: {content[:100]}...")
                    
                    # Add ALL local news from the last week, not just emergency-related
                    incident = {
                        'id': len(incidents_db) + len(incidents) + 1,
                        'type': 'local_news',
                        'title': entry.title[:100],
                        'location': city_name,
                        'severity': 'low',
                        'points': 5,  # Base points for local news
                        'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M %p'),
                        'description': content[:200] + "...",
                        'trustScore': 70,
                        'keywords': ['local', 'news'],
                        'source': source['name'],
                        'url': entry.link if hasattr(entry, 'link') else ''
                    }
                    incidents.append(incident)
                    logger.info(f"Added local news: {incident['title']}")
            
            elif source['type'] == 'web_scrape':
                # Use BeautifulSoup for web scraping
                incidents_from_scraping = scrape_news_website(source, city_name)
                incidents.extend(incidents_from_scraping)
            
        except Exception as e:
            logger.warning("Error scraping news source %s: %s", source['name'], str(e))
            continue
    
    
    # Removed broader search fallback to avoid international news
    
    # Add sample incidents only if still no real incidents found
    if len(incidents) == 0:
        logger.info("No incidents found from any sources, adding sample incidents for testing")
        sample_incidents = [
            {
                'id': len(incidents_db) + len(incidents) + 1,
                'type': 'fire',
                'title': f'Sample Fire Incident in {city_name}',
                'location': city_name,
                'severity': 'medium',
                'points': 25,
                'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M %p'),
                'description': f'Sample fire incident reported in {city_name} area. Emergency services responding.',
                'trustScore': 75,
                'keywords': ['fire', 'emergency'],
                'source': 'Sample Data',
                'url': ''
            },
            {
                'id': len(incidents_db) + len(incidents) + 2,
                'type': 'medical',
                'title': f'Sample Medical Emergency in {city_name}',
                'location': city_name,
                'severity': 'high',
                'points': 35,
                'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M %p'),
                'description': f'Sample medical emergency in {city_name}. Multiple casualties reported.',
                'trustScore': 80,
                'keywords': ['medical', 'emergency', 'casualty'],
                'source': 'Sample Data',
                'url': ''
            }
        ]
        incidents.extend(sample_incidents)
    
    # Sort incidents by severity points (highest first)
    incidents.sort(key=lambda x: x['points'], reverse=True)
    
    return incidents


if __name__ == '__main__':
    app.run(debug=True, port=5000)
