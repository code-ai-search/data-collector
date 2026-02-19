"""
Lightweight loader for 'cnn lite' news articles in the repo.
Implement functions to discover and yield articles as text and metadata.
"""
from pathlib import Path
import json
from typing import Dict, Iterator, List

DATA_DIR = Path("cnn-lite-articles")  # adjust to actual path in this repo


def iter_article_files(data_dir: Path = DATA_DIR) -> Iterator[Path]:
    """Yield article file paths. Adjust extension filter as needed."""
    for p in data_dir.rglob("*.json"):
        yield p


def load_article(path: Path) -> Dict:
    """Load a single article. Return dict with keys like 'id', 'title', 'body'."""
    with path.open("r", encoding="utf8") as f:
        return json.load(f)


def iter_articles(data_dir: Path = DATA_DIR) -> Iterator[Dict]:
    """Yield articles as dicts."""
    for p in iter_article_files(data_dir):
        try:
            yield load_article(p)
        except Exception as e:
            # consider logging
            continue
