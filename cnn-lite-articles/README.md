# CNN Lite Articles

This directory contains scraped articles from lite.cnn.com.

## File Naming

Each article is stored as a JSON file named by its SHA256 hash:
- Format: `{hash}.json`
- Example: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2.json`

## File Structure

Each JSON file contains:
```json
{
  "url": "https://lite.cnn.com/article/...",
  "title": "Article Title",
  "date": "2024-02-11T10:00:00Z",
  "author": "Author Name",
  "text": "Full article text...",
  "links": [
    {
      "url": "https://...",
      "text": "Link text"
    }
  ],
  "hash": "SHA256 hash of article content",
  "scraped_at": "2024-02-11T15:45:00Z"
}
```

## Updates

If an article's content changes, the scraper will detect the different hash and update the file accordingly.
