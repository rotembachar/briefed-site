"""
Script to fetch marketing and AI & Neuromarketing articles from multiple RSS feeds
and generate a single HTML page with a toggle button to switch between them.

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

FEEDS_AI = {
    "Neuroscience News": "https://neurosciencenews.com/feed/",
    "Marketing Tech News": "https://www.marketingtechnews.net/feed/",
}


def summarize_text(text: str, max_sentences: int = 2) -> str:
    """Return a naive summary by taking the first ``max_sentences`` sentences."""
    text = re.sub(r"<[^<]+?>", "", text)  # strip HTML
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:max_sentences])


def fetch_feed_items(feed_url: str, count: int = 5) -> list[dict]:
    """Fetch ``count`` items from a given RSS feed URL."""
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


def process_entries(feed_dict: dict) -> list[dict]:
    """Fetch and summarize all entries from a feed dictionary."""
    entries: list[dict] = []
    for source, url in feed_dict.items():
        try:
            items = fetch_feed_items(url, count=5)
            for item in items:
                summary = summarize_text(item["description"]) or "No summary available."
                entries.append({
                    "source": source,
                    "title": item["title"],
                    "link": item["link"],
                    "published": item["published"],
                    "summary": summary,
                })
        except Exception as exc:
            print(f"Failed to fetch feed {source}: {exc}")
    # sort by published date if possible
    def parse_date(entry):
        from email.utils import parsedate
        return parsedate(entry.get("published", "")) or (0,)
    entries.sort(key=parse_date, reverse=True)
    # format date nicely
    for entry in entries:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(entry.get("published", ""))
            entry["date"] = dt.strftime("%d %b %Y") if dt else ""
        except Exception:
            entry["date"] = ""
    return entries


def generate_html(entries_marketing: list[dict], entries_ai: list[dict], output_path: Path) -> None:
    """Generate HTML with two sections (marketing + AI) and a toggle button."""
    parts: list[str] = []
    parts.append("<html><head><meta charset='UTF-8'><title>Briefed. Feed</title>")
    parts.append(
        "<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap' rel='stylesheet'>"
    )
    parts.append(
        "<style>\n"
        "body {font-family: 'Poppins', sans-serif; background:#f8f9fc; margin:0;}\n"
        ".header {background:linear-gradient(90deg,#1f2eb8,#525cff); padding:20px 40px; color:#fff;}\n"
        ".header h1 {margin:0; font-size:2.2em; font-weight:600;}\n"
        ".header p {margin:4px 0 0; font-size:0.95em; color:#ffe0b2;}\n"
        ".section-header {display:flex; justify-content:center; align-items:center; gap:10px; margin:20px;}\n"
        ".section-header h2 {margin:0;}\n"
        ".entries {max-width:1100px; margin:20px auto; padding:0 20px; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px;}\n"
        ".hidden {display:none;}\n"
        ".card {background:#fff; border-radius:10px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.08);}\n"
        ".card .source {color:#525cff; font-size:0.75em; text-transform:uppercase; margin-bottom:4px;}\n"
        ".card .date {color:#757575; font-size:0.8em; margin-top:6px;}\n"
        ".card a {color:#1f2eb8; text-decoration:none; font-size:1.1em; font-weight:600;}\n"
        ".card a:hover {text-decoration:underline;}\n"
        ".card .summary {margin-top:10px; font-size:0.9em; color:#444;}\n"
        ".footer {background:#fff; text-align:center; padding:15px; font-size:0.8em; color:#1f2eb8; border-top:1px solid #eee;}\n"
        "#switch-button {padding:5px 10px; font-size:1rem; border:1px solid #ccc; border-radius:6px; cursor:pointer;}\n"
        "</style></head><body>"
    )

    # Header
    parts.append("<div class='header'><h1>Briefed.</h1><p>Your marketing news in One place</p></div>")
    parts.append("<div class='section-header'><h2 id='feed-title'>Marketing Articles</h2><button id='switch-button'>→</button></div>")

    # Marketing section
    parts.append("<div id='entries-marketing' class='entries'>")
    for entry in entries_marketing:
        parts.append("<div class='card'>")
        parts.append(f"<div class='source'>{entry['source']}</div>")
        parts.append(f"<a href='{entry['link']}' target='_blank'>{entry['title']}</a>")
        if entry.get("date"):
            parts.append(f"<div class='date'>{entry['date']}</div>")
        parts.append(f"<div class='summary'>{entry['summary']}</div>")
        parts.append("</div>")
    parts.append("</div>")

    # AI section (hidden by default)
    parts.append("<div id='entries-ai' class='entries hidden'>")
    for entry in entries_ai:
        parts.append("<div class='card'>")
        parts.append(f"<div class='source'>{entry['source']}</div>")
        parts.append(f"<a href='{entry['link']}' target='_blank'>{entry['title']}</a>")
        if entry.get("date"):
            parts.append(f"<div class='date'>{entry['date']}</div>")
        parts.append(f"<div class='summary'>{entry['summary']}</div>")
        parts.append("</div>")
    parts.append("</div>")

    # Footer
    parts.append("<div class='footer'>Updated automatically every day via GitHub Actions · <span style='color:#1f2eb8;font-weight:600;'>Created by Rotem Bachar</span></div>")

    # JS toggle
    parts.append("""
<script>
let current = "marketing";
document.getElementById("switch-button").addEventListener("click", () => {
  if (current === "marketing") {
    document.getElementById("entries-marketing").classList.add("hidden");
    document.getElementById("entries-ai").classList.remove("hidden");
    document.getElementById("feed-title").innerText = "AI & Neuromarketing Articles";
    document.getElementById("switch-button").innerText = "←";
    current = "ai";
  } else {
    document.getElementById("entries-ai").classList.add("hidden");
    document.getElementById("entries-marketing").classList.remove("hidden");
    document.getElementById("feed-title").innerText = "Marketing Articles";
    document.getElementById("switch-button").innerText = "→";
    current = "marketing";
  }
});
</script>
    """)

    parts.append("</body></html>")
    output_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    entries_marketing = process_entries(FEEDS)
    entries_ai = process_entries(FEEDS_AI)
    output_html = Path(__file__).resolve().parent / "index.html"
    generate_html(entries_marketing, entries_ai, output_html)
    print(f"Generated {output_html}")


if __name__ == "__main__":
    main()
