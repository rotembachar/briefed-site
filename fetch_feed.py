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


FEEDS = {
    "Marketing Dive": "https://www.marketingdive.com/feeds/news/",
    "Adweek Technology": "https://www.adweek.com/category/technology/feed/",
    "Social Media Today": "https://www.socia
