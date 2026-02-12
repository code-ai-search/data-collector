#!/usr/bin/env python3
"""
CNN Lite Article Scraper
Scrapes articles from lite.cnn.com and stores them with metadata
"""

import os
import json
import hashlib
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pathlib import Path
from time import sleep
from urllib.parse import urljoin, urlparse

# Configuration constants
MAX_ARTICLES_PER_RUN = 10
SLEEP_TIME = 2

def get_article_hash(content):
    """Generate SHA256 hash of article content for deduplication"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def extract_article_links(soup, base_url):
    """Extract all anchor tag links from the article"""
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        link_text = a_tag.get_text(strip=True)
        links.append({
            'url': absolute_url,
            'text': link_text
        })
    return links


def extract_article_data(article_url, session):
    """Extract article data from a given URL"""
    try:
        response = session.get(article_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title - try multiple selectors
        title = None
        title_selectors = ['h1', 'title', '.article-title', '[class*="headline"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break

        # Extract date - try multiple selectors
        date = None
        date_selectors = ['time', '.timestamp', '[class*="date"]', '[datetime]']
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                break

        # Extract author - try multiple selectors
        author = None
        author_selectors = ['.author', '[class*="author"]', '[rel="author"]']
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                break

        # Extract article text - try multiple selectors for article body
        text = None
        text_selectors = [
            'article',
            '.article-body',
            '[class*="article-content"]',
            '[class*="story-body"]',
            'main'
        ]
        for selector in text_selectors:
            text_elem = soup.select_one(selector)
            if text_elem:
                # Get all paragraphs within the article
                paragraphs = text_elem.find_all('p')
                if paragraphs:
                    text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    break

        # Fallback: get all paragraphs if no article container found
        if not text:
            paragraphs = soup.find_all('p')
            if paragraphs:
                text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # Extract all links from the article
        links = extract_article_links(soup, article_url)

        # Generate hash of the article content
        content_for_hash = f"{title}|{text}"
        article_hash = get_article_hash(content_for_hash)

        return {
            'url': article_url,
            'title': title or 'No title found',
            'date': date or datetime.now(timezone.utc).isoformat(),
            'author': author or 'Unknown',
            'text': text or 'No text found',
            'links': links,
            'hash': article_hash,
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        print(f"Error extracting article from {article_url}: {e}")
        return None


def get_article_links_from_homepage(homepage_url, session):
    """Get all article links from the CNN Lite homepage"""
    try:
        response = session.get(homepage_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links that look like articles
        article_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            # Convert relative URLs to absolute
            absolute_url = urljoin(homepage_url, href)

            # Filter for article URLs (typically contain /2024/, /2025/, /2026/ etc. or /article/)
            parsed = urlparse(absolute_url)
            # Ensure the domain is exactly cnn.com or a subdomain of cnn.com
            if parsed.netloc and (parsed.netloc == 'cnn.com' or parsed.netloc.endswith('.cnn.com')):
                # Basic heuristic: URLs with year patterns or containing "article" or news sections
                if any(x in absolute_url for x in ['/202', '/article/', '/news/', '/politics/', '/business/', '/world/']):
                    if absolute_url not in article_links:
                        article_links.append(absolute_url)

        return article_links

    except Exception as e:
        print(f"Error getting article links from homepage: {e}")
        return []


def save_article(article_data, output_dir):
    """Save article data to a JSON file"""
    if not article_data:
        return

    # Create filename from hash
    filename = f"{article_data['hash']}.json"
    filepath = output_dir / filename

    # Save the article data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(article_data, f, indent=2, ensure_ascii=False)

    print(f"Saved article: {article_data['title'][:50]}... -> {filename}")


def main():
    """Main function to scrape CNN Lite articles"""
    print("Starting CNN Lite article scraper...")

    # Create output directory
    output_dir = Path('cnn-lite-articles')
    output_dir.mkdir(exist_ok=True)

    # CNN Lite homepage
    homepage_url = 'https://lite.cnn.com'

    # Create a session for connection pooling
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; ArticleScraper/1.0)'
    })

    # Get all article links from homepage
    print(f"Fetching article links from {homepage_url}...")
    article_links = get_article_links_from_homepage(homepage_url, session)

    print(f"Found {len(article_links)} potential article links")

    if not article_links:
        print("No article links found. This might be due to website structure changes.")
        print("Please check the website manually.")
        return

    # Process each article
    successful_articles = 0
    for idx, article_url in enumerate(article_links[:MAX_ARTICLES_PER_RUN], 1):
        print(f"\n[{idx}/{min(MAX_ARTICLES_PER_RUN, len(article_links))}] Processing: {article_url}")

        article_data = extract_article_data(article_url, session)
        try:
            if article_data:
                save_article(article_data, output_dir)
                successful_articles += 1
            # sleep for some seconds to not overload servers
            sleep(SLEEP_TIME)
        except Exception as e:
            print(f"Exception on article: {e!r}")
            print(f"Article data for root causing: {article_data!r}")
            continue

    print(f"\n{'='*60}")
    print(f"Scraping completed!")
    print(f"Successfully scraped {successful_articles} articles")
    print(f"Articles saved to: {output_dir.absolute()}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
