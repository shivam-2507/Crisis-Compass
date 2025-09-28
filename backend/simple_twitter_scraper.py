#!/usr/bin/env python3
"""
Toronto Social Media Scraper - Last Week Only
"""

import requests
from datetime import datetime, timedelta

# Time window - last week
ONE_WEEK_AGO = datetime.now() - timedelta(days=7)


def scrape_reddit_toronto():
    """Scrape recent Reddit Toronto posts"""
    posts = []

    try:
        url = 'https://www.reddit.com/r/toronto/hot/.json?limit=100'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

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
                        'user': post_data.get('author', 'unknown'),
                        'title': post_data.get('title', ''),
                        'content': post_data.get('selftext', '')[:200],
                        'score': post_data.get('score', 0),
                        'comments': post_data.get('num_comments', 0),
                        'timestamp': post_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'url': f"https://reddit.com{post_data.get('permalink', '')}",
                        'age_days': (datetime.now() - post_timestamp).days
                    })

    except Exception as e:
        print(f"Error scraping Reddit: {e}")

    return posts


def save_to_file(posts):
    """Save posts to text file"""
    with open('toronto_tweets.txt', 'w', encoding='utf-8') as f:
        f.write(f"TORONTO SOCIAL MEDIA POSTS - LAST 7 DAYS\n")
        f.write(f"Date Range: {ONE_WEEK_AGO.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Posts: {len(posts)}\n")
        f.write("=" * 80 + "\n\n")

        for i, post in enumerate(posts, 1):
            f.write(f"POST #{i}\n")
            f.write(f"User: u/{post['user']}\n")
            f.write(f"Posted: {post['timestamp']} ({post['age_days']} days ago)\n")
            f.write(f"Score: {post['score']} | Comments: {post['comments']}\n")
            f.write(f"URL: {post['url']}\n")
            f.write(f"Title: {post['title']}\n")
            if post['content']:
                f.write(f"Content: {post['content']}\n")
            f.write("-" * 60 + "\n\n")


def main():
    print("Scraping Toronto posts from last week...")
    
    posts = scrape_reddit_toronto()
    posts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    save_to_file(posts)
    
    print(f"✅ Found {len(posts)} posts from the last 7 days")
    print(f"📁 Saved to: toronto_tweets.txt")


if __name__ == "__main__":
    main()
