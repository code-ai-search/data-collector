import tempfile
import unittest
from pathlib import Path

from scrape_cnn_lite import (
    extract_article_data,
    get_article_hash,
    load_existing_text_hashes,
    split_author_text,
)


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class FakeSession:
    def __init__(self, text):
        self._text = text

    def get(self, url, timeout=30):
        return FakeResponse(self._text)


class TestScrapeCnnLite(unittest.TestCase):
    def test_split_author_text_handles_conjunctions_and_suffixes(self):
        authors = split_author_text("By Jane Doe and John Smith, Jr.")
        self.assertEqual(authors, ["Jane Doe", "John Smith, Jr."])

    def test_split_author_text_handles_last_first_name(self):
        authors = split_author_text("Smith, John")
        self.assertEqual(authors, ["Smith, John"])

    def test_split_author_text_strips_cnn_suffix(self):
        authors = split_author_text("By Jane Doe, CNN and John Smith, CNN")
        self.assertEqual(authors, ["Jane Doe", "John Smith"])

    def test_extract_article_data_uses_text_hash_and_authors(self):
        html = (
            "<html><body>"
            "<h1>Sample Title</h1>"
            '<div class="author">By Jane Doe and John Smith</div>'
            "<article><p>Paragraph one.</p><p>Paragraph two.</p></article>"
            "</body></html>"
        )
        session = FakeSession(html)
        article_data = extract_article_data("https://lite.cnn.com/sample", session)

        expected_text = "Paragraph one.\n\nParagraph two."
        self.assertEqual(article_data["authors"], ["Jane Doe", "John Smith"])
        self.assertEqual(article_data["text"], expected_text)
        self.assertEqual(article_data["hash"], get_article_hash(expected_text))

    def test_extract_article_data_omits_block_list_links(self):
        html = (
            "<html><body>"
            "<h1>Sample Title</h1>"
            "<article><p>Paragraph one.</p></article>"
            '<a href="https://www.cnn.com/">Home</a>'
            '<a href="https://www.cnn.com/terms">Terms</a>'
            '<a href="https://www.cnn.com/privacy">Privacy</a>'
            '<a href="https://www.cnn.com/ad-choices">Ad choices</a>'
            '<a href="https://www.cnn.com/world/story">Story</a>'
            "</body></html>"
        )
        session = FakeSession(html)
        article_data = extract_article_data("https://lite.cnn.com/sample", session)

        self.assertEqual(article_data["links"], [{"url": "https://www.cnn.com/world/story", "text": "Story"}])

    def test_load_existing_text_hashes_prefers_stored_hash(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            stored_path = output_dir / "stored.json"
            stored_path.write_text(
                '{"hash": "storedhash", "authors": [], "text": "ignored"}',
                encoding="utf-8",
            )
            legacy_path = output_dir / "legacy.json"
            legacy_path.write_text(
                '{"text": "legacy text"}',
                encoding="utf-8",
            )

            hashes = load_existing_text_hashes(output_dir)
            self.assertIn("storedhash", hashes)
            self.assertIn(get_article_hash("legacy text"), hashes)


if __name__ == "__main__":
    unittest.main()
