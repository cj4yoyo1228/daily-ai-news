import os
from dotenv import load_dotenv

from src.data_ingestion.hn_scraper import fetch_hn_ai_stories
from src.data_ingestion.rss_parser import fetch_official_rss
from src.filtering.dedup_engine import ArticleFilter
from src.scoring.llm_evaluator import evaluate_events
from src.notifications.broadcaster import format_daily_briefing, send_telegram_broadcast


if __name__ == "__main__":
    load_dotenv()

    print("=" * 60)
    print("  🚀 Yoyo AI 商業情報系統 2.0 — 啟動")
    print("=" * 60)

    # ── 階段 1：數據採集 ──
    print("\n📡 【階段 1/4】數據採集中 ...")
    all_articles = []

    for name, fetcher, kwargs in [
        ("Hacker News", fetch_hn_ai_stories, {"hours": 24}),
        ("RSS Feeds", fetch_official_rss, {"hours": 24}),
    ]:
        try:
            results = fetcher(**kwargs)
            all_articles.extend(results)
            print(f"  ✅ {name}: {len(results)} 篇")
        except Exception as e:
            print(f"  ❌ {name} 失敗: {e}")

    print(f"  📊 採集總計: {len(all_articles)} 篇原始文章")

    if not all_articles:
        print("\n❌ 沒有採集到任何文章，系統終止")
        exit(1)

    # ── 階段 2：語意去重 ──
    print("\n🔬 【階段 2/4】語意去重中 ...")
    dedup_engine = ArticleFilter()
    unique_articles = dedup_engine.process(all_articles)

    # ── 階段 3：LLM 量化評分 ──
    print(f"\n🧠 【階段 3/4】LLM 評分中 ({len(unique_articles)} 篇送入) ...")
    all_scored = evaluate_events(unique_articles)

    # ── 篩選與降級邏輯 ──
    qualified = [s for s in all_scored if s.evaluation.is_qualified]

    if qualified:
        is_downgraded = False
        top_articles = qualified[:3]
        print(f"\n🏆 S 級情報命中！共 {len(qualified)} 篇達標，取前 3 名")
    else:
        is_downgraded = True
        top_articles = all_scored[:3]
        print("\n⚠️ 今日無 S 級情報，啟動降級播報 (Top 3 潛力事件)")

    # ── 階段 4：格式化與廣播 ──
    print("\n📢 【階段 4/4】格式化與廣播 ...")
    message = format_daily_briefing(top_articles, is_downgraded=is_downgraded)
    print("\n--- 預覽訊息 ---")
    print(message)
    print("--- 預覽結束 ---\n")

    send_telegram_broadcast(message)

    print("\n" + "=" * 60)
    print("  🏁 Yoyo AI 全域情報系統 2.0 — 任務完成")
    print("=" * 60)
