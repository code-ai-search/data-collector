# CNN Lite Article Collector

Automated data collection system for CNN Lite articles using GitHub Actions.

## Overview

This repository automatically scrapes articles from lite.cnn.com once daily and stores them as structured JSON files in the `cnn-lite-articles` folder.

## Article Data Structure

Each article is saved as a JSON file with the following information:
- **title**: Article headline
- **date**: Publication date
- **author**: Article author
- **text**: Full article text content
- **links**: List of all anchor tag links found in the article
- **hash**: SHA256 hash of the article content (for deduplication)
- **url**: Original article URL
- **scraped_at**: Timestamp when the article was scraped

## How It Works

1. **Daily Schedule**: GitHub Actions runs the scraper every day at 6:23 AM UTC
2. **Article Discovery**: The scraper fetches the CNN Lite homepage and identifies article links
3. **Data Extraction**: For each article, it extracts title, date, author, text, and all links
4. **Storage**: Articles are saved as JSON files named by their content hash
5. **Deduplication**: If an article's hash changes (content updated), it overwrites the previous version

## Files

- `scrape_cnn_lite.py`: Main Python scraper script
- `scrape.sh`: Shell script that runs the Python scraper
- `requirements.txt`: Python dependencies (requests, beautifulsoup4)
- `.github/workflows/scrape.yml`: GitHub Actions workflow configuration

## Manual Execution

To run the scraper manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scrape_cnn_lite.py
```

Or use the shell script:

```bash
./scrape.sh
```

## Output

Articles are stored in the `cnn-lite-articles/` directory as JSON files:
```
cnn-lite-articles/
├── a1b2c3d4...json
├── e5f6g7h8...json
└── ...
```

Each filename is the SHA256 hash of the article content, ensuring unique storage and easy deduplication.
