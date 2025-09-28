# Crisis Compass - Real-time Event Monitoring System

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import feedparser
import logging
import spacy
import nltk
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import re
from geopy.geocoders import Nominatim
from collections import defaultdict, Counter
import json
import time
from threading import Thread
import asyncio

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize NLP tools
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error(
        "spaCy model not found. Run: python -m spacy download en_core_web_sm")
    raise

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Initialize geocoder
geolocator = Nominatim(user_agent="crisis_compass")

# Crisis-related keywords with severity weights
CRISIS_KEYWORDS = {
    'natural_disasters': {
        'earthquake': 9, 'hurricane': 9, 'tornado': 8, 'flood': 7, 'wildfire': 8,
        'tsunami': 9, 'blizzard': 6, 'avalanche': 7, 'landslide': 7, 'drought': 5
    },
    'human_emergencies': {
        'accident': 6, 'crash': 7, 'explosion': 8, 'fire': 7, 'shooting': 9,
        'attack': 9, 'terrorism': 9, 'emergency': 6, 'evacuation': 8, 'rescue': 7
    },
    'infrastructure': {
        'blackout': 6, 'outage': 5, 'bridge collapse': 9, 'derailment': 8,
        'gas leak': 8, 'chemical spill': 8, 'water contamination': 7
    },
    'health_crises': {
        'outbreak': 8, 'pandemic': 9, 'epidemic': 8, 'contamination': 7,
        'hospital': 5, 'medical emergency': 6, 'quarantine': 7
    }
}

# Flatten keywords for easy lookup
ALL_CRISIS_KEYWORDS = {}
for category, keywords in CRISIS_KEYWORDS.items():
    ALL_CRISIS_KEYWORDS.update(keywords)

# News sources for scraping
NEWS_SOURCES = {
    'cbc_toronto': {
        'url': 'https://www.cbc.ca/news/canada/toronto',
        'rss': 'https://www.cbc.ca/cmlink/rss-topstories',
        'selector': 'article'
    },
    'cp24': {
        'url': 'https://www.cp24.com',
        'rss': 'https://www.cp24.com/feeds/all-news-1.822958?format=rss',
        'selector': '.story-item'
    },
    'global_news_toronto': {
        'url': 'https://globalnews.ca/toronto/',
        'rss': 'https://globalnews.ca/toronto/feed/',
        'selector': '.c-posts__item'
    },
    'reddit_toronto': {
        'url': 'https://www.reddit.com/r/toronto/hot/.json',
        'type': 'reddit_api',
        'selector': None
    },
    'reddit_emergency': {
        'url': 'https://www.reddit.com/r/emergencyservices/hot/.json',
        'type': 'reddit_api',
        'selector': None
    }
}

# Global storage for events
events_storage = []
last_update = None


class EventScraper:
    def __init__(self, location="Toronto, Ontario"):
        self.location = location
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_rss_feeds(self):
        """Scrape RSS feeds from news sources"""
        events = []

        for source_name, source_info in NEWS_SOURCES.items():
            if 'rss' not in source_info:
                continue

            try:
                logger.info(f"Scraping RSS from {source_name}")
                feed = feedparser.parse(source_info['rss'])

                for entry in feed.entries[:10]:  # Limit to recent entries
                    event_data = {
                        'source': source_name,
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'content': entry.get('content', [{}])[0].get('value', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published_parsed'),
                        'timestamp': datetime.now()
                    }
                    events.append(event_data)

            except Exception as e:
                logger.error(f"Error scraping RSS from {source_name}: {e}")

        return events

    def scrape_reddit_posts(self):
        """Scrape Reddit posts without using API keys"""
        events = []

        reddit_sources = ['reddit_toronto', 'reddit_emergency']

        for source_name in reddit_sources:
            source_info = NEWS_SOURCES[source_name]

            try:
                logger.info(f"Scraping Reddit from {source_name}")
                response = self.session.get(source_info['url'])

                if response.status_code == 200:
                    data = response.json()

                    for post in data['data']['children'][:15]:  # Limit posts
                        post_data = post['data']

                        event_data = {
                            'source': source_name,
                            'title': post_data.get('title', ''),
                            'description': post_data.get('selftext', ''),
                            'content': post_data.get('selftext', ''),
                            'link': f"https://reddit.com{post_data.get('permalink', '')}",
                            'score': post_data.get('score', 0),
                            'comments': post_data.get('num_comments', 0),
                            'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0))
                        }
                        events.append(event_data)

            except Exception as e:
                logger.error(f"Error scraping Reddit from {source_name}: {e}")

        return events

    def scrape_web_content(self):
        """Scrape web pages directly"""
        events = []

        web_sources = ['cbc_toronto', 'cp24', 'global_news_toronto']

        for source_name in web_sources:
            source_info = NEWS_SOURCES[source_name]

            try:
                logger.info(f"Scraping web content from {source_name}")
                response = self.session.get(source_info['url'], timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    articles = soup.select(source_info['selector'])[:10]

                    for article in articles:
                        title_elem = article.find(['h1', 'h2', 'h3', 'a'])
                        title = title_elem.get_text(
                            strip=True) if title_elem else ''

                        desc_elem = article.find(['p', 'div'])
                        description = desc_elem.get_text(
                            strip=True) if desc_elem else ''

                        link_elem = article.find('a')
                        link = link_elem.get('href', '') if link_elem else ''

                        if title and (title not in [e['title'] for e in events]):
                            event_data = {
                                'source': source_name,
                                'title': title,
                                'description': description[:300],
                                'content': description,
                                'link': link if link.startswith('http') else source_info['url'] + link,
                                'timestamp': datetime.now()
                            }
                            events.append(event_data)

            except Exception as e:
                logger.error(
                    f"Error scraping web content from {source_name}: {e}")

        return events

    def scrape_all_sources(self):
        """Scrape all configured sources"""
        all_events = []

        # Scrape RSS feeds
        rss_events = self.scrape_rss_feeds()
        all_events.extend(rss_events)

        # Scrape Reddit
        reddit_events = self.scrape_reddit_posts()
        all_events.extend(reddit_events)

        # Scrape web content
        web_events = self.scrape_web_content()
        all_events.extend(web_events)

        logger.info(f"Scraped {len(all_events)} total events")
        return all_events


class EventAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000, stop_words='english')

    def extract_crisis_score(self, text):
        """Calculate crisis severity score based on keywords"""
        if not text:
            return 0

        text_lower = text.lower()
        score = 0
        found_keywords = []

        for keyword, weight in ALL_CRISIS_KEYWORDS.items():
            if keyword in text_lower:
                score += weight
                found_keywords.append(keyword)

        return min(score, 10), found_keywords

    def extract_location(self, text):
        """Extract location entities from text"""
        if not text:
            return None

        doc = nlp(text)
        locations = [
            ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]

        # Prioritize Toronto/GTA locations
        toronto_keywords = ['toronto', 'gta', 'scarborough', 'etobicoke', 'north york',
                            'york region', 'mississauga', 'brampton', 'markham', 'richmond hill']

        for location in locations:
            if any(keyword in location.lower() for keyword in toronto_keywords):
                return location

        return locations[0] if locations else None

    def calculate_engagement_score(self, event_data):
        """Calculate engagement score based on available metrics"""
        score = 0

        # Reddit-specific metrics
        if 'score' in event_data:
            # Max 5 points for upvotes
            score += min(event_data['score'] / 100, 5)

        if 'comments' in event_data:
            # Max 3 points for comments
            score += min(event_data['comments'] / 50, 3)

        # Text-based engagement indicators
        text = f"{event_data.get('title', '')} {event_data.get('description', '')}"
        engagement_words = ['breaking', 'urgent',
                            'developing', 'live', 'update', 'alert']

        for word in engagement_words:
            if word in text.lower():
                score += 1

        return min(score, 10)

    def calculate_recency_score(self, timestamp):
        """Calculate recency score based on how recent the event is"""
        if not timestamp:
            return 0

        if isinstance(timestamp, tuple):  # RSS parsed time
            timestamp = datetime(*timestamp[:6])
        elif not isinstance(timestamp, datetime):
            return 0

        now = datetime.now()
        hours_diff = (now - timestamp).total_seconds() / 3600

        if hours_diff <= 1:
            return 10
        elif hours_diff <= 6:
            return 8
        elif hours_diff <= 24:
            return 6
        elif hours_diff <= 72:
            return 4
        else:
            return 2

    def analyze_events(self, events):
        """Analyze and score events"""
        analyzed_events = []

        for event in events:
            text_content = f"{event.get('title', '')} {event.get('description', '')}"

            # Extract crisis information
            crisis_score, crisis_keywords = self.extract_crisis_score(
                text_content)

            # Extract location
            location = self.extract_location(text_content)

            # Calculate scores
            engagement_score = self.calculate_engagement_score(event)
            recency_score = self.calculate_recency_score(
                event.get('timestamp'))

            # Calculate overall relevance score
            relevance_score = (crisis_score * 0.4 +
                               engagement_score * 0.3 + recency_score * 0.3)

            analyzed_event = {
                **event,
                'crisis_score': crisis_score,
                'crisis_keywords': crisis_keywords,
                'location': location,
                'engagement_score': engagement_score,
                'recency_score': recency_score,
                'relevance_score': round(relevance_score, 2),
                'timestamp_str': event.get('timestamp').strftime('%Y-%m-%d %I:%M %p') if event.get('timestamp') else ''
            }

            analyzed_events.append(analyzed_event)

        return analyzed_events

    def cluster_similar_events(self, events):
        """Cluster similar events together"""
        if len(events) < 2:
            return events

        texts = [
            f"{event.get('title', '')} {event.get('description', '')}" for event in events]

        try:
            # Vectorize texts
            tfidf_matrix = self.vectorizer.fit_transform(texts)

            # Perform clustering
            n_clusters = min(len(events) // 3, 10)  # Dynamic cluster count
            if n_clusters < 2:
                return events

            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(tfidf_matrix)

            # Group events by cluster
            clustered_events = defaultdict(list)
            for event, cluster in zip(events, clusters):
                clustered_events[cluster].append(event)

            # Select best event from each cluster
            representative_events = []
            for cluster_events in clustered_events.values():
                # Sort by relevance score and pick the best
                best_event = max(
                    cluster_events, key=lambda x: x.get('relevance_score', 0))

                # Add cluster information
                best_event['cluster_size'] = len(cluster_events)
                best_event['similar_events'] = [e['title']
                                                for e in cluster_events if e != best_event]

                representative_events.append(best_event)

            return representative_events

        except Exception as e:
            logger.error(f"Error clustering events: {e}")
            return events


# Global instances
scraper = EventScraper()
analyzer = EventAnalyzer()


def update_events_background():
    """Background task to update events periodically"""
    global events_storage, last_update

    try:
        logger.info("Starting background event update...")

        # Scrape all sources
        raw_events = scraper.scrape_all_sources()

        # Analyze events
        analyzed_events = analyzer.analyze_events(raw_events)

        # Filter for crisis-related events
        crisis_events = [
            e for e in analyzed_events if e['crisis_score'] > 0 or e['relevance_score'] > 3]

        # Cluster similar events
        clustered_events = analyzer.cluster_similar_events(crisis_events)

        # Sort by relevance score
        sorted_events = sorted(
            clustered_events, key=lambda x: x['relevance_score'], reverse=True)

        # Update global storage
        events_storage = sorted_events[:50]  # Keep top 50 events
        last_update = datetime.now()

        logger.info(f"Updated {len(events_storage)} events")

    except Exception as e:
        logger.error(f"Error in background update: {e}")


@app.route('/events', methods=['GET'])
def get_events():
    """Get ranked list of crisis events"""
    try:
        # Get query parameters
        location = request.args.get('location', 'Toronto, Ontario')
        limit = int(request.args.get('limit', 20))
        min_severity = int(request.args.get('min_severity', 0))

        # Filter events
        filtered_events = events_storage

        if location.lower() != 'all':
            filtered_events = [e for e in filtered_events
                               if e.get('location') and location.lower() in e['location'].lower()]

        if min_severity > 0:
            filtered_events = [e for e in filtered_events if e.get(
                'crisis_score', 0) >= min_severity]

        # Limit results
        result_events = filtered_events[:limit]

        return jsonify({
            'events': result_events,
            'total': len(filtered_events),
            'last_update': last_update.strftime('%Y-%m-%d %I:%M %p') if last_update else None,
            'location_filter': location
        })

    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/refresh', methods=['POST'])
def refresh_events():
    """Manually trigger event refresh"""
    try:
        # Run update in background thread
        thread = Thread(target=update_events_background)
        thread.start()

        return jsonify({'message': 'Event refresh started', 'status': 'success'})

    except Exception as e:
        logger.error(f"Error refreshing events: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'active',
        'events_count': len(events_storage),
        'last_update': last_update.strftime('%Y-%m-%d %I:%M %p') if last_update else None,
        'sources': list(NEWS_SOURCES.keys())
    })


if __name__ == '__main__':
    # Initial data load
    logger.info("Starting Crisis Compass Event Monitoring System...")

    # Start background update
    update_thread = Thread(target=update_events_background)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, port=5000)
