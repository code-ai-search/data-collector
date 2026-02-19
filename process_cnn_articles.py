#!/usr/bin/env python3
"""
Process all CNN articles under a directory and format each article's 'text' field
as a list of sentences. Writes a single JSONL file where each line is:
  {"id": "<article-id>", "sentences": ["Sentence 1.", "Sentence 2.", ...]}

Usage:
  python process_cnn_articles.py cnn-lite-articles output.jsonl

Options:
  --use-nltk   Use NLTK's punkt sentence tokenizer (recommended for better splitting).
               If used, install with: pip install nltk
               Then run once in Python:
                   import nltk; nltk.download('punkt')
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Optional


def remove_blank_lines(file):
    with open(file, 'r') as my_file, open("temp.txt", 'w') as temp_file:
        for line in my_file:
            if not line.isspace(): # Checks if line is not just whitespace
                temp_file.write(line)
    import shutil
    shutil.move("temp.txt", file) # Replaces the original file with the temporary one


def split_sentences_regex(text: str) -> List[str]:
    """Simple regex-based sentence splitter (no external deps)."""
    if not text:
        return []
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Split on sentence-ending punctuation followed by whitespace and a capital or quote/number.
    # This is not perfect but works well for many news articles.
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'“‘])', text)
    # Trim and filter empties
    sentences = [p.strip() for p in parts if p.strip()]
    return sentences

def split_sentences_nltk(text: str):
    from nltk.tokenize import sent_tokenize
    return sent_tokenize(text) if text else []

def extract_articles_from_json(path: Path):
    """Yield article dicts from a .json file. Supports single object, list of objects."""
    with path.open('r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON file {path}: {e}")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        # Some JSON files may contain one article; others may embed under a key.
        # Try to find dicts with 'text' key in nested structure.
        if 'text' in data:
            yield data
        else:
            # Search top-level values for dicts with 'text'
            for v in data.values():
                if isinstance(v, dict) and 'text' in v:
                    yield v
            # Fallback: yield the dict anyway
            yield data
    else:
        # Unknown structure
        return

def extract_articles_from_jsonl(path: Path):
    """Yield article dicts from a .jsonl file (one JSON object per line)."""
    with path.open('r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                raise RuntimeError(f"Failed to parse JSONL {path} line {lineno}: {e}")
            if isinstance(obj, dict):
                yield obj

def find_text_field(article: dict) -> Optional[str]:
    """Return the text content for an article dict or None."""
    # Common keys
    for key in ('text', 'content', 'article_text', 'body', 'full_text'):
        if key in article and isinstance(article[key], str):
            return article[key]
    # Sometimes 'text' could be nested or list
    val = article.get('text')
    if isinstance(val, list):
        # join list of strings
        return ' '.join(str(x) for x in val)
    if val is not None:
        return str(val)
    # No text found
    return None

def choose_id(article: dict, fallback: str) -> str:
    """Choose an identifier for the article."""
    for key in ('id', 'guid', 'url', 'article_id', 'link'):
        if key in article and article[key]:
            return str(article[key])
    return fallback

def process_directory(input_dir: Path, output_file: Path, use_nltk: bool = False):
    if use_nltk:
        # lazy import and ensure punkt is available (user must download beforehand)
        try:
            import nltk  # noqa: F401
        except Exception as e:
            raise RuntimeError("NLTK selected but not installed. Install with: pip install nltk") from e

    files = list(input_dir.rglob('*'))
    files = [p for p in files if p.is_file() and p.suffix.lower() in ('.json', '.jsonl', '.txt')]
    total_articles = 0
    written = 0
    with output_file.open('w', encoding='utf-8') as out:
        for path in files:
            try:
                if path.suffix.lower() == '.jsonl':
                    generator = extract_articles_from_jsonl(path)
                elif path.suffix.lower() == '.json':
                    generator = extract_articles_from_json(path)
                elif path.suffix.lower() == '.txt':
                    # treat each txt file as one document
                    text = path.read_text(encoding='utf-8').strip()
                    article = {'text': text}
                    generator = (article for _ in (0,) for article in (article,))
                else:
                    continue

                for idx, article in enumerate(generator):
                    total_articles += 1
                    text = find_text_field(article)
                    if not text:
                        continue
                    # Choose id: prefer article id/url otherwise filename + index
                    fallback = f"{path.name}"
                    if path.suffix.lower() in ('.jsonl',):
                        # for jsonl, incorporate line idx to make unique
                        fallback = f"{path.name}:{idx}"
                    aid = choose_id(article, fallback)

                    if use_nltk:
                        sentences = split_sentences_nltk(text)
                    else:
                        sentences = split_sentences_regex(text)

                    # Normalize sentences: ensure strings, strip
                    sentences = [s.strip() for s in sentences if s and s.strip()]
                    if not sentences:
                        continue

                    #record = {"id": aid, "sentences": sentences}
                    record = sentences
                    for sentence in record:
                        if not sentence.startswith("Source: CNN") and not sentence.startswith("See Full Web Article"):
                            if sentence.endswith('\n\n'):
                                sentence.rstrip('\n')
                            out.write(sentence)
                            if not sentence.endswith("\n"):
                                out.write("\n")
                    written += 1
            except Exception as e:
                print(f"Warning: failed to process {path}: {e}")

    print(f"Finished. Files scanned: {len(files)}. Articles seen: {total_articles}. Articles written: {written}.")
    print(f"Output written to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Process CNN articles and split 'text' into sentences.")
    parser.add_argument("input_dir", type=Path, help="Path to directory containing cnn-lite-articles")
    parser.add_argument("output_file", type=Path, help="Output JSONL file (one JSON object per line)")
    parser.add_argument("--use-nltk", action="store_true", help="Use NLTK punkt tokenizer (better quality)")
    args = parser.parse_args()

    if not args.input_dir.exists() or not args.input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist or is not a directory: {args.input_dir}")

    process_directory(args.input_dir, args.output_file, use_nltk=args.use_nltk)
    remove_blank_lines(args.output_file)


if __name__ == "__main__":
    main()
