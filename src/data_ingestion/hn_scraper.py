import re
import time
from datetime import datetime, timezone, timedelta
from typing import List

import requests

from src.models.schemas import RawArticle

HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

AI_KEYWORDS = re.compile(
    r"\b(launch|show.hn|funding|startup|revenue|acquisition|"
    r"series.a|raised|pricing|acquired|y.combinator)\b",
    re.IGNORECASE,
)

REQUEST_TIMEOUT = 10
MAX_IDS_TO_SCAN = 120


def fetch_hn_ai_stories(hours: int = 24) -> List[RawArticle]:
    """從 Hacker News 抓取過去 N 小時內與 AI 相關的熱門文章。"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles: List[RawArticle] = []

    try:
        resp = requests.get(HN_TOP_STORIES_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        story_ids: list = resp.json()
    except Exception as e:
        print(f"[HN] 無法取得 Top Stories 列表: {e}")
        return articles

    for story_id in story_ids[:MAX_IDS_TO_SCAN]:
        try:
            item_resp = requests.get(
                HN_ITEM_URL.format(story_id), timeout=REQUEST_TIMEOUT
            )
            item_resp.raise_for_status()
            item = item_resp.json()
        except Exception as e:
            print(f"[HN] 無法取得 story {story_id}: {e}")
            continue

        if not item or item.get("type") != "story":
            continue

        title = item.get("title", "")
        url = item.get("url", f"https://news.ycombinator.com/item?id={story_id}")
        timestamp = item.get("time", 0)
        published = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        if published < cutoff:
            continue

        if not AI_KEYWORDS.search(title):
            continue

        snippet = item.get("text", "") or title
        articles.append(
            RawArticle(
                title=title,
                url=url,
                source="Hacker News",
                published_at=published,
                content_snippet=snippet[:500],
            )
        )

    print(f"[HN] 抓取完成：共 {len(articles)} 篇 AI 相關文章")
    return articles
