"""Script to fetch marketing articles from multiple RSS feeds and generate HTML.

This script pulls the latest entries from several free marketing RSS feeds,
extracts relevant fields, and builds an HTML file for the Briefed. website.
The output HTML file is written to ``index.html`` in the same directory.

Sources used:
  - HubSpot Marketing Blog RSS feed
  - Marketing Dive News RSS feed【535150834247052†L281-L289】
  - Social Media Today News RSS feed

This script does not rely on paid APIs and uses a simple summarization method
to create a two-sentence summary of each article. It is intended for a weekly
run (e.g., via GitHub Actions) to keep the site up to date.

Usage::

    python fetch_feed.py
"""

import xml.etree.ElementTree as ET
import requests
import re
from pathlib import Path


FEEDS = {
    "HubSpot": "https://blog.hubspot.com/marketing/rss.xml",
    "Marketing Dive": "https://www.marketingdive.com/feeds/news",
    "Social Media Today": "https://www.socialmediatoday.com/feeds/news",
}


def summarize_text(text: str, max_sentences: int = 2) -> str:
    """Return a naive summary by taking the first ``max_sentences`` sentences.

    Strips HTML tags and splits on sentence boundaries. If there are fewer
    sentences than ``max_sentences``, returns the entire text.
    """
    # Remove HTML tags
    text = re.sub(r"<[^<]+?>", "", text)
    # Replace multiple whitespace with a single space
    text = re.sub(r"\s+", " ", text).strip()
    # Split into sentences using common punctuation marks
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:max_sentences])


def fetch_feed_items(feed_url: str, count: int = 5) -> list[dict]:
    """Fetch ``count`` items from a given RSS feed URL.

    Returns a list of dictionaries with keys: ``title``, ``link``,
    ``published``, and ``description``.
    """
    items: list[dict] = []
    response = requests.get(feed_url)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    for item in root.findall(".//item")[:count]:
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        pub_date = item.findtext("pubDate", default="")
        description = item.findtext("description", default="")
        items.append({
            "title": title,
            "link": link,
            "published": pub_date,
            "description": description,
        })
    return items


def generate_html(entries: list[dict], output_path: Path) -> None:
    """Generate an HTML file summarizing RSS feed entries.

    The HTML file is written to ``output_path`` and organizes entries by
    source, with titles linking to the original articles and summaries shown
    below each link.
    """
    parts = []
    parts.append("<html><head><meta charset=\"UTF-8\"><title>Briefed. Feed</title>")
    parts.append(
        "<style>body{font-family:Arial,sans-serif;max-width:800px;margin:20px auto;padding:10px;}"
        "h1{border-bottom:1px solid #ccc;padding-bottom:10px;}"
        ".entry{margin-bottom:20px;}"
        ".source{font-weight:bold;color:#333;margin-bottom:2px;}"
        ".title{font-size:1.2em;margin:5px 0;}"
        ".summary{color:#555;}</style></head><body>"
    )
    parts.append("<h1>Briefed. Weekly Feed</h1>")
    for entry in entries:
        parts.append("<div class='entry'>")
        parts.append(f"<div class='source'>{entry['source']}</div>")
        parts.append(
            f"<div class='title'><a href='{entry['link']}' target='_blank' rel='noopener noreferrer'>{entry['title']}</a></div>"
        )
        parts.append(f"<div class='summary'>{entry['summary']}</div>")
        parts.append("</div>")
    parts.append("</body></html>")
    output_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    # Gather entries from all feeds
    all_entries: list[dict] = []
    for source, url in FEEDS.items():
        try:
            items = fetch_feed_items(url, count=5)
            for item in items:
                summary = summarize_text(item["description"]) or "No summary available."
                all_entries.append({
                    "source": source,
                    "title": item["title"],
                    "link": item["link"],
                    "published": item["published"],
                    "summary": summary,
                })
        except Exception as exc:
            print(f"Failed to fetch feed {source}: {exc}")
    # Sort entries by published date descending if available
    def parse_date(entry):
        from email.utils import parsedate
        return parsedate(entry.get("published", "")) or (0,)
    all_entries.sort(key=parse_date, reverse=True)
    # Generate HTML file
    output_html = Path(__file__).resolve().parent / "index.html"
    generate_html(all_entries, output_html)
    print(f"Generated {output_html}")


if __name__ == "__main__":
    main()