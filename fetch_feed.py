"""Script to fetch marketing articles from multiple RSS feeds and generate HTML.

This script pulls the latest entries from several free marketing RSS feeds,
extracts relevant fields, and builds an HTML file for the Briefed. website.
The output HTML file is written to ``index.html`` in the same directory.

Sources used:
- Marketing Dive News RSS feed
- Adweek Technology RSS feed
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
    "Marketing Dive": "https://www.marketingdive.com/feeds/news/",
    "Adweek Technology": "https://www.adweek.com/category/technology/feed/",
    "Social Media Today": "https://www.socialmediatoday.com/feeds/news/",

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
    """Generate an HTML file summarizing RSS feed entries with dates.

    The HTML file is written to ``output_path``. Entries are grouped in a grid of
    cards, each showing the source, title, published date and a short summary.
    A refreshed tagline explains the update schedule and a modern palette and
    font improve the marketing vibe of the site.
    """
    parts: list[str] = []
    # Base HTML head with Google Fonts for improved typography and custom styles
    parts.append("<html><head><meta charset='UTF-8'><title>Briefed. Feed</title>")
    parts.append(
        "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap' rel='stylesheet'>"
    )
    parts.append(
        "<style>\n"
        "body {font-family: 'Poppins', sans-serif; background-color: #f0f4f8; color: #333; margin: 0;}\n"
        ".header {background: linear-gradient(90deg, #ff8a65, #ffa726); padding: 25px 40px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 10;}\n"
        ".header h1 {margin: 0; font-size: 2.4em; font-weight: 600; color: #fff;}\n"
        ".header p {margin: 4px 0 0; font-size: 0.95em; color: #ffe0b2;}\n"
        ".entries {max-width: 1100px; margin: 40px auto; padding: 0 20px; display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px;}\n"
        ".card {background-color: #ffffff; border-radius: 10px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); display: flex; flex-direction: column; height: 100%; transition: transform 0.2s;}\n"
        ".card:hover {transform: translateY(-4px);}\n"
        ".card .source {color: #ff7043; font-size: 0.75em; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px;}\n"
        ".card .date {color: #757575; font-size: 0.8em; margin-top: 6px;}\n"
        ".card a {color: #2e7d32; text-decoration: none; font-size: 1.2em; font-weight: 600; line-height: 1.3;}\n"
        ".card a:hover {text-decoration: underline;}\n"
        ".card .summary {margin-top: 12px; color: #555; font-size: 0.9em; line-height: 1.45;}\n"
        ".footer {background-color: #ffffff; text-align: center; padding: 20px; font-size: 0.8em; color: #999; border-top: 1px solid #eee;}\n"
        "</style></head><body>"
    )
    # Header with tagline describing the essence of the feed rather than the schedule
    # We emphasise that all your marketing news is available in one place and avoid tying it to a specific day.
    parts.append("<div class='header'>")
    parts.append("<h1>Briefed.</h1>")
    # Tagline: a concise description that stays consistent across days
    parts.append("<p>Your marketing news in One place</p>")
    parts.append("</div>")
    # Entries
    parts.append("<div class='entries'>")
    for entry in entries:
        parts.append("<div class='card'>")
        parts.append(f"<div class='source'>{entry['source']}</div>")
        parts.append(
            f"<a href='{entry['link']}' target='_blank' rel='noopener noreferrer'>{entry['title']}</a>"
        )
        # Insert formatted date if available
        if entry.get('date'):
            parts.append(f"<div class='date'>{entry['date']}</div>")
        parts.append(f"<div class='summary'>{entry['summary']}</div>")
        parts.append("</div>")
    parts.append("</div>")  # close entries grid
    parts.append("<div class='footer'>Updated automatically every week via GitHub Actions · Powered by free marketing sources</div>")
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
    # Format dates into a human-readable form and store in each entry. If parsing
    # fails, leave the date empty. Display only the day, month and year for
    # simplicity.
    for entry in all_entries:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(entry.get("published", ""))
            if dt:
                # Convert to local time (Israel time) if needed by the site visitor
                # The feed dates are typically in UTC; we display the date component only.
                entry["date"] = dt.strftime("%d %b %Y")
            else:
                entry["date"] = ""
        except Exception:
            entry["date"] = ""
    # Generate HTML file
    output_html = Path(__file__).resolve().parent / "index.html"
    generate_html(all_entries, output_html)
    print(f"Generated {output_html}")


if __name__ == "__main__":
    main()
