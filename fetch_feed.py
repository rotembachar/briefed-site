"""
Script to fetch articles from multiple RSS feeds, categorize them (AI, B2B, Research, General),
and generate an index.html file with tabs to switch between categories.

Usage::
    python fetch_feed.py
"""

import xml.etree.ElementTree as ET
import requests
import re
from pathlib import Path

AI_KEYWORDS = [
    r"\bai\b", r"\bartificial intelligence\b", r"\bmachine learning\b",
    r"\bgen ai\b", r"\bchatgpt\b", r"\bopenai\b", r"\bdeep learning\b",
    r"\bneural network\b", r"\bgenerative ai\b", r"\bagent ai\b",
    r"\bagentic ai\b", r"\bgpt\b"
]

RESEARCH_KEYWORDS = [
    r"\bstudy\b", r"\bresearch\b", r"\bsurvey\b", r"\breport\b",
    r"\bwhitepaper\b", r"\banalysis\b", r"\binsight\b",
    r"\bacademic\b", r"\binstitute\b", r"\bdata-driven\b"
]


FEEDS = {
    "Marketing Dive": "https://www.marketingdive.com/feeds/news/",
    "Adweek Technology": "https://www.adweek.com/category/technology/feed/",
    "Social Media Today": "https://www.socialmediatoday.com/feeds/news/",
    "The B2B Marketer": "https://theb2bmarketer.pro/feed/",
    "Search Engine Journal": "https://www.searchenginejournal.com/category/news/feed/",
    "Marketing Beat": "https://www.marketing-beat.co.uk/feed/",
    "Marketing Tech News": "https://www.marketingtechnews.net/feed/",
    "American Marketing Association": "https://www.ama.org/feed/",
}


def summarize_text(text: str, max_sentences: int = 2) -> str:
    """Return a naive summary by taking the first ``max_sentences`` sentences."""
    text = re.sub(r"<[^<]+?>", "", text)  # strip HTML tags
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:max_sentences])


def fetch_feed_items(feed_url: str, count: int = 5) -> list[dict]:
    """Fetch ``count`` items from a given RSS feed URL."""
    items: list[dict] = []
    try:
        response = requests.get(feed_url, timeout=10)  # ⏱ timeout למניעת תקיעות
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
    except Exception as exc:
        print(f"⚠️ Failed to fetch {feed_url}: {exc}")
    return items


def categorize_entry(entry: dict) -> list[str]:
    """Return a list of categories (AI, B2B, Research, General) for an entry."""
    text = (entry["title"] + " " + entry["summary"]).lower()
    categories = []

    # חוקים לפי מקור
    if entry["source"] == "The B2B Marketer":
        categories.append("B2B")
    if entry["source"] == "American Marketing Association":
        categories.append("Research")

    # AI
    if any(re.search(pattern, text) for pattern in AI_KEYWORDS):
    categories.append("AI")

    # Research
    if any(re.search(pattern, text) for pattern in RESEARCH_KEYWORDS):
    categories.append("Research")


    # General
    if not categories:
        categories.append("General")

    return list(set(categories))  # הסרה של כפילויות


def process_entries(feed_dict: dict) -> list[dict]:
    """Fetch and summarize all entries from a feed dictionary."""
    entries: list[dict] = []
    for source, url in feed_dict.items():
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

    # sort by date
    def parse_date(entry):
        from email.utils import parsedate
        return parsedate(entry.get("published", "")) or (0,)
    entries.sort(key=parse_date, reverse=True)

    # format dates
    for entry in entries:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(entry.get("published", ""))
            entry["date"] = dt.strftime("%d %b %Y") if dt else ""
        except Exception:
            entry["date"] = ""
    return entries


def generate_html(all_entries: list[dict], output_path: Path) -> None:
    """Generate HTML file with tabs for categories."""
    categories_map = {"AI": [], "B2B": [], "Research": [], "General": []}
    for entry in all_entries:
        cats = categorize_entry(entry)
        for c in cats:
            categories_map[c].append(entry)

    parts: list[str] = []
    parts.append("<html><head><meta charset='UTF-8'><title>Briefed. Feed</title>")
    parts.append("<link href='https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap' rel='stylesheet'>")
    parts.append(
        "<style>\n"
        "body {font-family:'Poppins',sans-serif; background:#f8f9fc; margin:0;}\n"
        ".header {background:linear-gradient(90deg,#1f2eb8,#525cff); padding:20px 40px; color:#fff;}\n"
        ".header h1 {margin:0; font-size:2.2em; font-weight:600;}\n"
        ".tabs {display:flex; justify-content:center; gap:10px; margin:20px;}\n"
        ".tabs button {padding:8px 16px; border:1px solid #ccc; border-radius:6px; cursor:pointer; background:#fff;}\n"
        ".tabs button.active {background:#1f2eb8; color:#fff; border-color:#1f2eb8;}\n"
        ".entries {max-width:1100px; margin:20px auto; padding:0 20px; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px;}\n"
        ".card {background:#fff; border-radius:10px; padding:20px; box-shadow:0 4px 12px rgba(0,0,0,0.08);}\n"
        ".card .source {color:#525cff; font-size:0.75em; text-transform:uppercase; margin-bottom:4px;}\n"
        ".card .date {color:#757575; font-size:0.8em; margin-top:6px;}\n"
        ".card a {color:#1f2eb8; text-decoration:none; font-size:1.1em; font-weight:600;}\n"
        ".card a:hover {text-decoration:underline;}\n"
        ".card .summary {margin-top:10px; font-size:0.9em; color:#444;}\n"
        ".footer {background:#fff; text-align:center; padding:15px; font-size:0.8em; color:#1f2eb8; border-top:1px solid #eee;}\n"
        ".hidden {display:none;}\n"
        "</style></head><body>"
    )

    # Header
    parts.append("<div class='header'><h1>Briefed.</h1><p>Your marketing news in One place</p></div>")

    # Tabs
    parts.append("<div class='tabs'>")
    for cat in categories_map.keys():
        parts.append(f"<button onclick=\"showTab('{cat}')\" id='btn-{cat}'>{cat}</button>")
    parts.append("</div>")

    # Content sections
    for cat, entries in categories_map.items():
        parts.append(f"<div id='tab-{cat}' class='entries hidden'>")
        for entry in entries:
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

    # JS for tabs
    parts.append("""
<script>
function showTab(cat) {
  const tabs = document.querySelectorAll('.entries');
  const buttons = document.querySelectorAll('.tabs button');
  tabs.forEach(t => t.classList.add('hidden'));
  buttons.forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + cat).classList.remove('hidden');
  document.getElementById('btn-' + cat).classList.add('active');
}
// Show AI by default
showTab('AI');
</script>
    """)

    parts.append("</body></html>")
    output_path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    all_entries = process_entries(FEEDS)
    output_html = Path(__file__).resolve().parent / "index.html"
    generate_html(all_entries, output_html)
    print(f"✅ Generated {output_html}")


if __name__ == "__main__":
    main()
