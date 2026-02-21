import time
from datetime import datetime, timezone, timedelta
from typing import List

import feedparser

from src.models.schemas import RawArticle

DEFAULT_FEEDS = [
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "name": "TechCrunch AI"},
    {"url": "https://www.producthunt.com/feed", "name": "Product Hunt"},
    {"url": "https://www.theverge.com/rss/technology/index.xml", "name": "The Verge Tech"},
    {"url": "https://blogs.microsoft.com/ai/feed/", "name": "Microsoft AI Blog"},
    {"url": "https://blog.google/technology/ai/rss/", "name": "Google AI Blog"},
    {"url": "https://ai.meta.com/blog/rss/", "name": "Meta AI"},
    {"url": "https://nvidianews.nvidia.com/releases.xml", "name": "NVIDIA Newsroom"},
]


def _parse_published(entry) -> datetime | None:
    """嘗試從 RSS entry 中解析發布時間。"""
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime.fromtimestamp(
                    time.mktime(parsed), tz=timezone.utc
                )
            except Exception:
                continue
    return None


def fetch_official_rss(hours: int = 24) -> List[RawArticle]:
    """從預設的官方 RSS feeds 抓取過去 N 小時內的文章。"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles: List[RawArticle] = []

    for feed_info in DEFAULT_FEEDS:
        feed_url = feed_info["url"]
        feed_name = feed_info["name"]

        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"[RSS] 解析 {feed_name} 失敗: {e}")
            continue

        if feed.bozo and not feed.entries:
            print(f"[RSS] {feed_name} 回傳異常且無內容，跳過")
            continue

        for entry in feed.entries:
            published = _parse_published(entry)
            if not published or published < cutoff:
                continue

            title = entry.get("title", "無標題")
            url = entry.get("link", "")
            summary = entry.get("summary", entry.get("description", ""))

            articles.append(
                RawArticle(
                    title=title,
                    url=url,
                    source=feed_name,
                    published_at=published,
                    content_snippet=summary[:500],
                )
            )

        print(f"[RSS] {feed_name} 解析完成")

    print(f"[RSS] 抓取完成：共 {len(articles)} 篇文章")
    return articles
