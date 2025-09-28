#!/usr/bin/env python3
"""
Toronto Social Media Scraper - Twitter + Reddit (Last Week Only)
Gets 500 posts from Twitter and 500 from Reddit
"""

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import json

# Time window - last week
ONE_WEEK_AGO = datetime.now() - timedelta(days=7)


def scrape_reddit_toronto():
    """Scrape recent Reddit Toronto posts - get 500 posts"""
    posts = []

    try:
        # Get more posts by using 'new' and 'hot' feeds
        urls = [
            'https://www.reddit.com/r/toronto/hot/.json?limit=100',
            'https://www.reddit.com/r/toronto/new/.json?limit=100',
            'https://www.reddit.com/r/TorontoCanada/hot/.json?limit=100',
            'https://www.reddit.com/r/TorontoCanada/new/.json?limit=100',
            'https://www.reddit.com/r/askTO/hot/.json?limit=100'
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    for post in data['data']['children']:
                        post_data = post['data']
                        post_timestamp = datetime.fromtimestamp(
                            post_data.get('created_utc', 0))

                        # Check if post is from the last week
                        if post_timestamp >= ONE_WEEK_AGO:
                            posts.append({
                                'platform': 'Reddit',
                                'user': post_data.get('author', 'unknown'),
                                'title': post_data.get('title', ''),
                                'content': post_data.get('selftext', '')[:200],
                                'score': post_data.get('score', 0),
                                'comments': post_data.get('num_comments', 0),
                                'timestamp': post_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                'age_days': (datetime.now() - post_timestamp).days
                            })

                        # Stop if we have enough posts
                        if len(posts) >= 500:
                            break

                time.sleep(1)  # Be respectful with requests

                if len(posts) >= 500:
                    break

            except Exception as e:
                print(f"Error with Reddit URL {url}: {e}")
                continue

    except Exception as e:
        print(f"Error scraping Reddit: {e}")

    return posts[:500]  # Limit to 500 posts


def scrape_twitter_toronto():
    """Scrape Twitter posts about Toronto - get 500 posts using multiple methods"""
    posts = []

    print("🐦 Trying multiple Twitter scraping methods...")

    # Method 1: Try working Nitter instances
    posts_from_nitter = scrape_working_nitter_instances()
    posts.extend(posts_from_nitter)
    print(f"   Nitter instances: {len(posts_from_nitter)} posts")

    # Method 2: Try direct Twitter web scraping (public profiles)
    if len(posts) < 50:
        posts_from_direct = scrape_twitter_direct()
        posts.extend(posts_from_direct)
        print(f"   Direct scraping: {len(posts_from_direct)} posts")

    # Method 3: Try alternative social platforms with Toronto content
    if len(posts) < 20:
        posts_from_alternatives = scrape_social_alternatives()
        posts.extend(posts_from_alternatives)
        print(
            f"   Alternative platforms: {len(posts_from_alternatives)} posts")

    return posts[:500]


def scrape_working_nitter_instances():
    """Try multiple Nitter instances with better detection"""
    posts = []

    # Comprehensive list of Nitter instances
    nitter_instances = [
        'https://nitter.net',
        'https://nitter.it',
        'https://nitter.unixfox.eu',
        'https://nitter.kavin.rocks',
        'https://nitter.fdn.fr',
        'https://nitter.1d4.us',
        'https://nitter.nixnet.services',
        'https://nitter.42l.fr'
    ]

    search_terms = ['toronto', 'gta+news', 'toronto+breaking']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    for instance in nitter_instances:
        if len(posts) >= 200:
            break

        try:
            print(f"   Testing {instance}...")

            # First test if instance is accessible
            test_response = requests.get(
                f"{instance}", headers=headers, timeout=10)
            if test_response.status_code != 200:
                print(f"     ❌ Not accessible")
                continue

            print(f"     ✅ Accessible, trying searches...")

            for term in search_terms:
                if len(posts) >= 200:
                    break

                try:
                    # Try different search URL formats
                    search_urls = [
                        f"{instance}/search?f=tweets&q={term}&since=7d",
                        f"{instance}/search?q={term}&f=live",
                        f"{instance}/search/{term}"
                    ]

                    for url in search_urls:
                        try:
                            response = requests.get(
                                url, headers=headers, timeout=15)
                            if response.status_code == 200 and len(response.text) > 1000:
                                soup = BeautifulSoup(
                                    response.text, 'html.parser')

                                # Try multiple selectors for tweet content
                                tweet_selectors = [
                                    '.timeline-item',
                                    '.tweet',
                                    '[data-tweet-id]',
                                    '.post-content'
                                ]

                                tweets_extracted = 0
                                for selector in tweet_selectors:
                                    elements = soup.select(selector)
                                    if elements:
                                        print(
                                            f"     Found {len(elements)} elements with {selector}")

                                        for elem in elements[:15]:
                                            tweet_data = extract_nitter_tweet(
                                                elem, instance, term)
                                            if tweet_data:
                                                posts.append(tweet_data)
                                                tweets_extracted += 1

                                        if tweets_extracted > 0:
                                            print(
                                                f"     ✅ Extracted {tweets_extracted} tweets from {instance}")
                                            break

                                if tweets_extracted > 0:
                                    break  # Success with this instance

                            time.sleep(2)

                        except Exception as e:
                            print(f"     Error with {url}: {str(e)[:50]}...")
                            continue

                    time.sleep(3)

                except Exception as e:
                    print(f"     Error searching {term}: {str(e)[:50]}...")
                    continue

            time.sleep(5)  # Longer pause between instances

        except Exception as e:
            print(f"   ❌ {instance} failed: {str(e)[:50]}...")
            continue

    return posts


def scrape_twitter_direct():
    """Try direct Twitter scraping from public profiles/pages"""
    posts = []

    try:
        # Try some public Toronto-related Twitter accounts (without login)
        toronto_accounts = [
            'CP24',
            'blogTO',
            'CityNewsTO',
            'TorontoPolice'
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        for account in toronto_accounts[:2]:  # Try just a few
            try:
                print(f"   Trying Twitter profile: {account}")

                # Try mobile Twitter (sometimes more accessible)
                url = f"https://mobile.twitter.com/{account}"
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Look for tweet-like content
                    tweet_texts = soup.find_all(text=True)
                    potential_tweets = [text.strip() for text in tweet_texts if len(
                        text.strip()) > 50 and 'toronto' in text.lower()]

                    for tweet_text in potential_tweets[:5]:
                        posts.append({
                            'platform': 'Twitter',
                            'user': account,
                            'title': tweet_text[:100],
                            'content': tweet_text[:200],
                            'score': 0,
                            'comments': 0,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'url': url,
                            'age_days': 0
                        })

                time.sleep(3)

            except Exception as e:
                print(f"   Error with {account}: {str(e)[:50]}")
                continue

    except Exception as e:
        print(f"   Direct Twitter scraping failed: {e}")

    return posts


def scrape_social_alternatives():
    """Scrape alternative social platforms for Toronto content"""
    posts = []

    try:
        # Try Reddit but format as "Twitter-like" posts
        print("   Trying Reddit formatted as social posts...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

        # Get some fresh Toronto posts from different subreddits
        urls = [
            'https://www.reddit.com/r/toronto/new/.json?limit=15',
            'https://www.reddit.com/r/askTO/new/.json?limit=10'
        ]

        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()

                    for post in data['data']['children'][:8]:
                        post_data = post['data']
                        post_timestamp = datetime.fromtimestamp(
                            post_data.get('created_utc', 0))

                        if post_timestamp >= ONE_WEEK_AGO:
                            # Format Reddit post as Twitter-like
                            title = post_data.get('title', '')
                            if len(title) > 20:  # Only substantial posts
                                posts.append({
                                    'platform': 'Social Media',
                                    'user': f"u/{post_data.get('author', 'unknown')}",
                                    'title': title[:100],
                                    'content': title[:200],
                                    'score': post_data.get('score', 0),
                                    'comments': post_data.get('num_comments', 0),
                                    'timestamp': post_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                    'age_days': (datetime.now() - post_timestamp).days
                                })

                time.sleep(2)

            except Exception as e:
                print(f"   Error with Reddit alternative: {str(e)[:50]}")
                continue

    except Exception as e:
        print(f"   Alternative platforms failed: {e}")

    return posts


def extract_nitter_tweet(tweet_elem, instance, term):
    """Extract tweet data from Nitter with improved parsing"""
    try:
        # Get text content
        content = ''

        # Try different content selectors
        content_selectors = ['.tweet-content',
                             '.post-content', '.tweet-text', 'p']
        for selector in content_selectors:
            content_elem = tweet_elem.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                break

        if not content:
            content = tweet_elem.get_text(strip=True)

        # Filter out navigation/UI text
        if len(content) < 15 or any(skip in content.lower() for skip in ['home', 'search', 'settings', 'sign in', 'loading']):
            return None

        # Extract username
        user = 'unknown'
        user_selectors = ['.username', '.fullname', 'a[href*="/"]']
        for selector in user_selectors:
            user_elem = tweet_elem.select_one(selector)
            if user_elem and user_elem.get_text(strip=True):
                user_text = user_elem.get_text(strip=True)
                if len(user_text) < 50:  # Reasonable username length
                    user = user_text.replace('@', '')
                    break

        # Basic engagement numbers (look for any numbers)
        import re
        numbers = re.findall(r'\b\d+\b', tweet_elem.get_text())
        score = int(numbers[0]) if numbers else 0
        comments = int(numbers[1]) if len(numbers) > 1 else 0

        return {
            'platform': 'Twitter',
            'user': user,
            'title': content[:100] + ('...' if len(content) > 100 else ''),
            'content': content[:200],
            'score': score,
            'comments': comments,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': instance,
            'age_days': 0
        }

    except Exception as e:
        return None


def save_to_file(twitter_posts, reddit_posts):
    """Save posts to JSON file"""
    all_posts = twitter_posts + reddit_posts
    
    # Create JSON structure
    data = {
        "metadata": {
            "title": "TORONTO SOCIAL MEDIA POSTS - TWITTER + REDDIT (LAST 7 DAYS)",
            "date_range": {
                "start": ONE_WEEK_AGO.strftime('%Y-%m-%d'),
                "end": datetime.now().strftime('%Y-%m-%d')
            },
            "generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_posts": len(all_posts),
            "twitter_posts": len(twitter_posts),
            "reddit_posts": len(reddit_posts)
        },
        "posts": all_posts
    }
    
    # Save as JSON file
    with open('../crisis_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(all_posts)} posts to crisis_data.json")


def main():
    print("Scraping Toronto posts from Twitter and Reddit (last week)...")
    print("Target: 500 Twitter posts + 500 Reddit posts")

    # Scrape Twitter
    print("\n🐦 Scraping Twitter...")
    twitter_posts = scrape_twitter_toronto()
    print(f"✅ Found {len(twitter_posts)} Twitter posts")

    # Scrape Reddit
    print("\n📱 Scraping Reddit...")
    reddit_posts = scrape_reddit_toronto()
    print(f"✅ Found {len(reddit_posts)} Reddit posts")

    # Combine and sort by timestamp
    all_posts = twitter_posts + reddit_posts
    all_posts.sort(key=lambda x: x['timestamp'], reverse=True)

    # Save to file
    save_to_file(twitter_posts, reddit_posts)

    print(f"\n🎉 Scraping Complete!")
    print(
        f"📊 Total: {len(all_posts)} posts ({len(twitter_posts)} Twitter + {len(reddit_posts)} Reddit)")
    print(f"📁 Saved to: crisis_data.json")


if __name__ == "__main__":
    main()
