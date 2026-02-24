#!/usr/bin/env python3
"""
CNN Lite Article Scraper
Scrapes articles from lite.cnn.com and stores them with metadata
"""

import os
import json
import hashlib
import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pathlib import Path
from time import sleep
from urllib.parse import urljoin, urlparse

# Configuration constants
MAX_ARTICLES_PER_RUN = 110
SLEEP_TIME = 2
DEFAULT_TITLE = 'No title found'
DEFAULT_TEXT = 'No text found'
AUTHOR_SUFFIXES = {'jr', 'sr', 'ii', 'iii', 'iv'}
URL_BLOCK_LIST = {
    'https://www.cnn.com/',
    'https://www.cnn.com/terms',
    'https://www.cnn.com/privacy',
    'https://www.cnn.com/ad-choices',
}
# Normalize to handle equivalent URLs with or without trailing slash.
NORMALIZED_URL_BLOCK_LIST = {url.rstrip('/') for url in URL_BLOCK_LIST}
CNN_SUFFIX_PATTERN = re.compile(r',\s*CNN\s*$', re.IGNORECASE)
CNN_AUTHOR_TOKEN = 'CNN'

def get_article_hash(content):
    """Generate SHA256 hash of article text for deduplication"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def extract_article_links(soup, base_url):
    """Extract all anchor tag links from the article"""
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, href)
        if absolute_url.rstrip('/') in NORMALIZED_URL_BLOCK_LIST:
            continue
        link_text = a_tag.get_text(strip=True)
        links.append({
            'url': absolute_url,
            'text': link_text
        })
    return links


def split_author_text(author_text):
    """Split author text into individual author names."""
    if not author_text:
        return []
    cleaned = re.sub(r'^\s*by\s+', '', author_text, flags=re.IGNORECASE).strip()
    if not cleaned:
        return []
    has_conjunction = bool(re.search(r'\s+(?:and|&)\s+', cleaned))
    parts = re.split(r'\s+(?:and|&)\s+', cleaned)
    authors = []
    for part in parts:
        comma_parts = [entry.strip() for entry in part.split(',') if entry.strip()]
        if not comma_parts:
            continue
        appears_to_be_last_first_format = (
            not has_conjunction and len(parts) == 1 and len(comma_parts) == 2
        )
        if appears_to_be_last_first_format:
            authors.append(f"{comma_parts[0]}, {comma_parts[1]}")
            continue
        current = comma_parts[0]
        for entry in comma_parts[1:]:
            normalized = entry.lower().rstrip('.')
            if normalized in AUTHOR_SUFFIXES and current:
                current = f"{current}, {entry}"
            else:
                if current:
                    authors.append(current)
                current = entry
        if current:
            authors.append(current)
    cleaned_authors = []
    for author in authors:
        normalized_author = CNN_SUFFIX_PATTERN.sub('', author).strip()
        if normalized_author and normalized_author.upper() != CNN_AUTHOR_TOKEN:
            cleaned_authors.append(normalized_author)
    return cleaned_authors


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

        # Extract authors - try multiple selectors
        authors = []
        seen_authors = set()
        # NOTE: the class selector, .byline--lite is the one cnn-lite uses
        author_selectors = ['.author', '[class*="author"]', '[rel="author"]', '.byline--lite']
        for selector in author_selectors:
            author_elems = soup.select(selector)
            for author_elem in author_elems:
                author_text = " ".join(author_elem.stripped_strings)
                for author in split_author_text(author_text):
                    if author not in seen_authors:
                        authors.append(author)
                        seen_authors.add(author)
            if authors:
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

        title_value = title or DEFAULT_TITLE
        text_value = text or DEFAULT_TEXT

        # Generate hash of the article text
        article_hash = get_article_hash(text_value)

        return {
            'url': article_url,
            'title': title_value,
            'date': date or datetime.now(timezone.utc).isoformat(),
            'authors': authors,
            'text': text_value,
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


def load_existing_text_hashes(output_dir) -> set:
    """Load existing article text hashes from stored JSON files."""
    existing_hashes = set()
    for json_file in output_dir.glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            has_authors_field = data.get('authors') is not None
            if data.get('hash') and has_authors_field:
                existing_hashes.add(data['hash'])
                continue
            text_value = data.get('text', '')
            existing_hashes.add(get_article_hash(text_value))
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error reading existing article {json_file}: {e}")
    return existing_hashes


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
    existing_text_hashes = load_existing_text_hashes(output_dir)

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
                if article_data['hash'] in existing_text_hashes:
                    print(f"Skipping article with unchanged text: {article_data['title'][:50]}...")
                else:
                    save_article(article_data, output_dir)
                    existing_text_hashes.add(article_data['hash'])
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
