# main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib.robotparser
import urllib.error
from urllib.parse import quote_plus
import logging
import os
import spacy
from datetime import datetime
import feedparser
import re
from geopy.geocoders import Nominatim

app = Flask(__name__)


def _cors_origins():
    """Default dev origins plus CRISIS_COMPASS_CORS_ORIGINS (comma-separated) for production."""
    base = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    extra = os.environ.get("CRISIS_COMPASS_CORS_ORIGINS", "").strip()
    if not extra:
        return base
    seen = set()
    out = []
    for o in base + [s.strip() for s in extra.split(",") if s.strip()]:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


# Dev: Vite on localhost; production: set CRISIS_COMPASS_CORS_ORIGINS to your site origin(s)
CORS(app, origins=_cors_origins())


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
    "missing": 1,
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

# Set CRISIS_COMPASS_DEV_SAMPLES=1 to inject placeholder incidents when RSS returns nothing
_DEV_SAMPLE_INCIDENTS = os.environ.get(
    "CRISIS_COMPASS_DEV_SAMPLES", ""
).lower() in ("1", "true", "yes")


def _match_entails_negation(text_lower, match_start):
    window = text_lower[max(0, match_start - 50) : match_start]
    return bool(
        re.search(
            r"\b(?:no|not|without|never|isn't|aren't|wasn't|weren't)\b(?:\s+\w+){0,6}\s*$",
            window,
        )
    )


def _keyword_has_valid_match(text_lower, keyword):
    if not text_lower or not keyword:
        return False
    kw = keyword.strip()
    if " " in kw:
        pos = text_lower.find(kw.lower())
        if pos == -1:
            return False
        return not _match_entails_negation(text_lower, pos)
    for m in re.finditer(r"\b" + re.escape(kw) + r"\b", text_lower):
        if not _match_entails_negation(text_lower, m.start()):
            return True
    return False


def _collect_keyword_points(headline_lower, body_lower, keyword_dict, body_weight=0.55):
    points = 0
    found = []
    for kw, pts in keyword_dict.items():
        in_head = bool(headline_lower and _keyword_has_valid_match(headline_lower, kw))
        in_body = _keyword_has_valid_match(body_lower, kw)
        if in_head:
            points += pts
            found.append(kw)
        elif in_body:
            points += max(1, int(pts * body_weight))
            found.append(kw)
    return points, found


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


def extract_emergency_info(text, headline=None):
    """
    Extracts emergency-related keywords and calculates severity and trust scores.
    Uses word-boundary matching for single-token keywords, light negation handling,
    and stronger weight for headline matches than body-only matches.
    """
    text = text or ""
    headline = headline or ""
    body_lower = text.lower()
    headline_lower = headline.lower()
    combined_for_nlp = f"{headline} {text}".strip() or text
    doc = nlp(combined_for_nlp.lower())

    severity_points, emergency_keywords_found = _collect_keyword_points(
        headline_lower, body_lower, EMERGENCY_KEYWORDS, body_weight=0.55
    )
    severity = get_severity_level(severity_points)

    trust_raw, trust_keywords_found = _collect_keyword_points(
        headline_lower, body_lower, TRUST_KEYWORDS, body_weight=0.65
    )
    trust_score = get_trust_score(trust_raw)

    locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
    location = locations[0] if locations else "Unknown Location"

    all_keywords = emergency_keywords_found + trust_keywords_found

    return {
        "keywords": all_keywords,
        "points": severity_points,
        "severity": severity,
        "location": location,
        "trustScore": trust_score,
    }


# In-memory storage for incidents (For demonstration purposes)
incidents_db = []
_incident_key_to_row = {}

# Filled by scrape_local_news for /debug/logs and empty-state hints in the UI
LAST_LOCAL_SCRAPE_REPORT = {}


def _stable_incident_key(inc):
    url = (inc.get("url") or "").strip()
    if url:
        return ("url", url.split("?")[0].strip().lower())
    title = (inc.get("title") or "").strip().lower()[:120]
    loc = (inc.get("location") or "").strip().lower()[:80]
    return ("hash", f"{title}|{loc}")


def _next_incident_id():
    return max((i.get("id", 0) for i in incidents_db), default=0) + 1


def merge_incident_into_store(inc):
    """Dedupe by URL or title+location; reuse existing row and id when seen."""
    k = _stable_incident_key(inc)
    if k in _incident_key_to_row:
        return _incident_key_to_row[k]
    row = dict(inc)
    row["id"] = _next_incident_id()
    row.setdefault("url", "")
    _incident_key_to_row[k] = row
    incidents_db.append(row)
    return row


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
        title = (
            soup.title.get_text(strip=True)
            if soup.title
            else "Unknown Title"
        )

        # Process the content
        emergency_info = extract_emergency_info(content, headline=title)

        incident = {
            "type": emergency_info["keywords"][0]
            if emergency_info["keywords"]
            else "general",
            "title": title[:100],
            "location": emergency_info["location"],
            "severity": emergency_info["severity"],
            "points": emergency_info["points"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "description": content[:200] + "...",
            "trustScore": emergency_info["trustScore"],
            "keywords": emergency_info["keywords"],
            "source": "Manual scrape",
            "url": url,
        }

        stored = merge_incident_into_store(incident)
        return jsonify(stored)

    except requests.exceptions.RequestException as e:
        logger.error("Error scraping URL: %s", str(e))
        return jsonify({'error': str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Liveness probe for load balancers and deploy scripts."""
    return jsonify({"status": "ok", "service": "crisis-compass-api"}), 200


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
        'server_status': 'running',
        'last_scrape': LAST_LOCAL_SCRAPE_REPORT,
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
        
        address = location.raw.get("address", {}) if location and getattr(location, "raw", None) else {}
        # Extract city/region name for news search
        city_name = extract_city_name(location_name, address)
        region = (
            address.get("state")
            or address.get("province")
            or address.get("region")
            or ""
        )
        country_code = (address.get("country_code") or "ca").upper()
        logger.info(f"Extracted city name: {city_name}, region: {region}, country: {country_code}")

        # Scrape local news
        logger.info(f"Starting news scraping for city: {city_name}")
        local_incidents = scrape_local_news(
            city_name, latitude, longitude, region=region, country_code=country_code
        )
        logger.info(f"Found {len(local_incidents)} incidents")

        merged = [merge_incident_into_store(dict(i)) for i in local_incidents]

        logger.info("=== REQUEST COMPLETE ===")
        return jsonify(merged)
        
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


def _parse_iso_date_prefix(raw):
    if not raw:
        return None
    s = raw.strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d")
        except ValueError:
            return None
    return None


def is_recent_web_article(article, title):
    """
    Prefer structured dates from the article DOM; no hard-coded year allow/block lists.
    If no date is found, include the article (same tradeoff as unknown RSS dates).
    """
    try:
        if article is not None:
            t_el = article.select_one("time[datetime]")
            if t_el and t_el.get("datetime"):
                article_date = _parse_iso_date_prefix(t_el["datetime"])
                if article_date:
                    return (datetime.now() - article_date).days <= 30
            meta = article.select_one('meta[property="article:published_time"]')
            if meta and meta.get("content"):
                article_date = _parse_iso_date_prefix(meta["content"])
                if article_date:
                    return (datetime.now() - article_date).days <= 30
        return True
    except Exception as e:
        logger.warning("Error checking web article recency: %s", e)
        return True


def extract_city_name(location_string, address=None):
    """
    Extract city name from Nominatim address dict or full location string.
    """
    if address:
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("hamlet")
        )
        if city:
            return city.strip()

    if not location_string:
        return "Unknown"

    parts = [p.strip() for p in location_string.split(",")]
    city = parts[0] if parts else "Unknown"

    if any(keyword in city.lower() for keyword in ["campus", "university", "college", "school"]):
        for part in parts:
            if any(
                indicator in part.lower()
                for indicator in [
                    "waterloo",
                    "toronto",
                    "ottawa",
                    "vancouver",
                    "montreal",
                    "calgary",
                    "edmonton",
                ]
            ):
                return part
        provinces = ["ontario", "quebec", "british columbia", "alberta"]
        for i, part in enumerate(parts):
            if any(province in part.lower() for province in provinces):
                if i > 0:
                    return parts[i - 1].strip()

    return city


def _google_news_rss_url(query, country_code="CA"):
    """Build a Google News RSS URL with proper encoding and region."""
    cc = (country_code or "CA").upper()
    if cc == "US":
        hl, gl, ceid = "en", "US", "US:en"
    elif cc == "GB":
        hl, gl, ceid = "en", "GB", "GB:en"
    else:
        hl, gl, ceid = "en", "CA", "CA:en"
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"


def get_news_sources(city_name, region_hint=None, country_code="CA"):
    """
    Get comprehensive list of news sources for a given city.
    Queries are URL-encoded; region uses the user's province/state when available.
    """
    region_hint = (region_hint or "").strip()
    cc = (country_code or "CA").upper()

    sources = [
        {
            "name": f"Google News - {city_name} Local",
            "url": _google_news_rss_url(f"{city_name} local news", cc),
            "type": "rss",
            "category": "local",
        },
        {
            "name": f"Google News - {city_name} Emergency",
            "url": _google_news_rss_url(
                f"{city_name} emergency OR disaster OR incident", cc
            ),
            "type": "rss",
            "category": "local",
        },
        {
            "name": f"Google News - {city_name} Breaking",
            "url": _google_news_rss_url(f"{city_name} breaking news", cc),
            "type": "rss",
            "category": "local",
        },
        {
            "name": f"Google News - {city_name} Fire Police",
            "url": _google_news_rss_url(
                f"{city_name} fire OR police OR ambulance OR 911", cc
            ),
            "type": "rss",
            "category": "local",
        },
    ]

    if region_hint:
        sources.append(
            {
                "name": f"Google News - {city_name} {region_hint}",
                "url": _google_news_rss_url(
                    f"{city_name} {region_hint} emergency OR accident", cc
                ),
                "type": "rss",
                "category": "regional",
            }
        )
        sources.append(
            {
                "name": f"Google News - {region_hint} Regional",
                "url": _google_news_rss_url(
                    f"{region_hint} emergency OR disaster OR severe weather", cc
                ),
                "type": "rss",
                "category": "regional",
            }
        )

    if cc == "CA":
        sources.extend(
            [
                {
                    "name": "CBC News Top Stories",
                    "url": "https://www.cbc.ca/cmlink/rss-topstories",
                    "type": "rss",
                    "category": "national",
                },
                {
                    "name": "Global News Canada",
                    "url": "https://globalnews.ca/feed/",
                    "type": "rss",
                    "category": "national",
                },
            ]
        )
    elif cc == "US":
        sources.append(
            {
                "name": "NPR News",
                "url": "https://feeds.npr.org/1001/rss.xml",
                "type": "rss",
                "category": "national",
            }
        )

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
                emergency_info = extract_emergency_info(full_content, headline=title)
                logger.info(f"Article analysis: '{title[:50]}...' -> points={emergency_info['points']}, keywords={emergency_info['keywords']}")
                
                # Only include if it has emergency keywords
                if emergency_info['points'] > 0:
                    incident = {
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


def _strip_html(text):
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)


def _local_relevance_boost(text, city_name, region):
    """Boost score when headline/body clearly mentions the user's city or region."""
    if not text:
        return 0
    t = text.lower()
    boost = 0
    city = (city_name or "").strip()
    if len(city) >= 3 and city.lower() in t:
        boost += 20
    elif city:
        for token in re.split(r"[\s,]+", city):
            tok = token.strip().lower()
            if len(tok) > 2 and tok in t:
                boost += 12
    reg = (region or "").strip()
    if len(reg) >= 3 and reg.lower() in t:
        boost += 10
    return min(boost, 40)


def _rss_item_relevant_to_area(category, emergency_points, local_boost, content, city_name):
    """National feeds: keep stories that are local or clearly incident-related."""
    c = (content or "").lower()
    city = (city_name or "").strip().lower()
    if category in ("local", "regional"):
        return True
    if emergency_points > 0:
        return True
    if local_boost >= 10:
        return True
    if city and len(city) >= 3 and city in c:
        return True
    return False


def _fetch_rss_feed(url):
    """Fetch RSS with a browser User-Agent so feeds (e.g. Google News) return entries."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=25)
    response.raise_for_status()
    return feedparser.parse(response.content)


def _dedupe_key(entry):
    link = getattr(entry, "link", "") or ""
    title = getattr(entry, "title", "") or ""
    if link:
        return ("url", link.split("?")[0].strip().lower())
    return ("title", title.strip().lower()[:120])


def scrape_local_news(city_name, latitude, longitude, region=None, country_code="CA"):
    """
    Scrape local news sources for incidents in the specified area.
    Ranks items by emergency NLP score plus local relevance (city/region in text).
    """
    global LAST_LOCAL_SCRAPE_REPORT

    incidents = []
    seen = set()
    region = region or ""
    cc = (country_code or "CA").upper()
    logger.info(f"Scraping local news for city: {city_name} (region={region}, cc={cc})")

    diag = {
        "city": city_name,
        "feeds_attempted": 0,
        "feeds_failed": 0,
        "feeds_with_entries": 0,
        "entries_considered": 0,
    }

    news_sources = get_news_sources(city_name, region_hint=region, country_code=cc)

    for source in news_sources:
        diag["feeds_attempted"] += 1
        try:
            logger.info("Checking news source: %s - %s", source["name"], source["url"])

            if source["type"] == "rss":
                feed = _fetch_rss_feed(source["url"])
                logger.info(
                    "Found %s entries from %s (bozo=%s)",
                    len(feed.entries),
                    source["name"],
                    getattr(feed, "bozo", False),
                )

                if len(feed.entries) > 0:
                    diag["feeds_with_entries"] += 1

                for entry in feed.entries[:12]:
                    diag["entries_considered"] += 1
                    if not is_recent_article(entry):
                        continue

                    title = (getattr(entry, "title", None) or "Untitled")[:200]
                    summary_raw = ""
                    if hasattr(entry, "summary"):
                        summary_raw = entry.summary
                    elif hasattr(entry, "description"):
                        summary_raw = entry.description
                    summary_plain = _strip_html(summary_raw)
                    content = f"{title} {summary_plain}".strip()
                    if not content:
                        continue

                    dk = _dedupe_key(entry)
                    if dk in seen:
                        continue
                    seen.add(dk)

                    emergency_info = extract_emergency_info(content, headline=title)
                    local_boost = _local_relevance_boost(content, city_name, region)
                    category = source.get("category", "local")
                    points = emergency_info["points"] + local_boost
                    if points < 3:
                        points = 3

                    if not _rss_item_relevant_to_area(
                        category,
                        emergency_info["points"],
                        local_boost,
                        content,
                        city_name,
                    ):
                        continue

                    keywords = list(
                        dict.fromkeys(
                            emergency_info["keywords"] + ["local"]
                        )
                    )
                    inc_type = (
                        emergency_info["keywords"][0]
                        if emergency_info["keywords"]
                        else "local_news"
                    )
                    severity = get_severity_level(points)
                    loc = city_name
                    if (
                        emergency_info.get("location")
                        and emergency_info["location"] != "Unknown Location"
                    ):
                        loc = emergency_info["location"]

                    incident = {
                        "type": inc_type,
                        "title": title[:100],
                        "location": loc,
                        "severity": severity,
                        "points": points,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                        "description": (content[:200] + "...")
                        if len(content) > 200
                        else content,
                        "trustScore": emergency_info["trustScore"],
                        "keywords": keywords,
                        "source": source["name"],
                        "url": entry.link if hasattr(entry, "link") else "",
                    }
                    incidents.append(incident)
                    logger.info(
                        "Added: %s | points=%s (nlp=%s local_boost=%s)",
                        title[:60],
                        points,
                        emergency_info["points"],
                        local_boost,
                    )

            elif source["type"] == "web_scrape":
                incidents_from_scraping = scrape_news_website(source, city_name)
                incidents.extend(incidents_from_scraping)

        except Exception as e:
            diag["feeds_failed"] += 1
            logger.warning("Error scraping news source %s: %s", source["name"], str(e))
            continue

    real_count = len(incidents)
    hint = ""
    if real_count == 0:
        if diag["feeds_attempted"] > 0 and diag["feeds_failed"] >= diag["feeds_attempted"]:
            hint = (
                "Every RSS feed request failed (timeout, HTTP error, or block). "
                "Google News often rejects scripted requests—check the API terminal for warnings."
            )
        elif diag["feeds_with_entries"] == 0:
            hint = (
                "No RSS entries were returned (empty feeds, blocked responses, or parse errors). "
                "Try again later or inspect API logs."
            )
        elif diag["entries_considered"] > 0:
            hint = (
                "Feeds returned headlines, but nothing was kept: items may be too old, "
                "duplicates, or filtered (national stories need emergency keywords or your city in the text)."
            )
        else:
            hint = "No feed entries were scanned."

    LAST_LOCAL_SCRAPE_REPORT = {
        **diag,
        "incidents_before_samples": real_count,
        "hint": hint,
        "dev_samples_available": _DEV_SAMPLE_INCIDENTS,
    }

    if len(incidents) == 0 and _DEV_SAMPLE_INCIDENTS:
        logger.info(
            "No RSS incidents; adding dev sample rows (CRISIS_COMPASS_DEV_SAMPLES=1)"
        )
        sample_incidents = [
            {
                "type": "fire",
                "title": f"[DEV SAMPLE] Fire drill scenario in {city_name}",
                "location": city_name,
                "severity": "medium",
                "points": 25,
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "description": (
                    f"Placeholder incident for UI testing only — not from live news "
                    f"({city_name})."
                ),
                "trustScore": 75,
                "keywords": ["fire", "emergency"],
                "source": "Dev sample (not real news)",
                "url": "",
                "is_sample": True,
            },
            {
                "type": "medical",
                "title": f"[DEV SAMPLE] Medical scenario in {city_name}",
                "location": city_name,
                "severity": "high",
                "points": 35,
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "description": (
                    "Placeholder medical scenario for UI testing only — not from live news."
                ),
                "trustScore": 80,
                "keywords": ["medical", "emergency", "casualty"],
                "source": "Dev sample (not real news)",
                "url": "",
                "is_sample": True,
            },
        ]
        incidents.extend(sample_incidents)
    elif len(incidents) == 0:
        logger.info("No incidents from feeds (samples disabled; set CRISIS_COMPASS_DEV_SAMPLES=1 for placeholders)")
    
    # Sort incidents by severity points (highest first)
    incidents.sort(key=lambda x: x['points'], reverse=True)
    
    return incidents


if __name__ == '__main__':
    app.run(debug=True, port=5000)
