"""
Tests for topic discovery adapters.
"""

from unittest.mock import MagicMock, patch
from discovery.google_trends import fetch_google_trends
from discovery.reddit import fetch_reddit_topics
from discovery.rss_sources import fetch_rss_feed
from discovery.nasa import fetch_nasa_news
from discovery.wikipedia import fetch_wikipedia_curiosities


def test_fetch_rss_feed_parses_entries():
    sample_feed_xml = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
      <channel>
        <title>Sample Feed</title>
        <item>
          <title>Test Scientific Discovery</title>
          <link>https://example.com/story1</link>
          <description>Researchers discovered a new clean energy material.</description>
        </item>
      </channel>
    </rss>
    """
    with patch("feedparser.parse") as mock_parse:
        mock_entry = MagicMock()
        mock_entry.get.side_effect = lambda k, d="": {
            "title": "Test Scientific Discovery",
            "link": "https://example.com/story1",
            "summary": "Researchers discovered a new clean energy material.",
            "published": "2026-11-07T00:00:00Z"
        }.get(k, d)
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed

        results = fetch_rss_feed("https://example.com/feed.xml", category="future_is_here")
        assert len(results) == 1
        assert results[0]["title"] == "Test Scientific Discovery"
        assert results[0]["category"] == "future_is_here"
        assert results[0]["source_type"] == "rss"


def test_fetch_reddit_topics_filters_nsfw_and_low_score():
    sample_response = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "TIL that honey never spoils",
                        "selftext": "Archaeologists found 3000 year old honey in Egyptian tombs.",
                        "score": 4500,
                        "stickied": False,
                        "over_18": False,
                        "url": "https://reddit.com/r/til/1",
                        "permalink": "/r/til/1",
                    }
                },
                {
                    "data": {
                        "title": "Pinned Mod Post",
                        "score": 10000,
                        "stickied": True,
                        "over_18": False,
                    }
                },
                {
                    "data": {
                        "title": "Low score topic",
                        "score": 10,
                        "stickied": False,
                        "over_18": False,
                    }
                }
            ]
        }
    }

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_response
        mock_get.return_value = mock_resp

        results = fetch_reddit_topics("todayilearned", category="daily_mystery", min_score=100)
        assert len(results) == 1
        assert "Honey never spoils" in results[0]["title"]
        assert results[0]["category"] == "daily_mystery"
