from src.data_ingestion.hn_scraper import fetch_hn_ai_stories
from src.data_ingestion.rss_parser import fetch_official_rss
from src.data_ingestion.hf_papers import fetch_hf_daily_papers
from src.filtering.dedup_engine import ArticleFilter


if __name__ == "__main__":
    print("🚀 開始測試漏斗式過濾與去重層\n")

    print("📡 階段一：數據採集中 ...")
    all_articles = []

    for name, fetcher, kwargs in [
        ("Hacker News", fetch_hn_ai_stories, {"hours": 24}),
        ("RSS Feeds", fetch_official_rss, {"hours": 24}),
        ("HF Papers", fetch_hf_daily_papers, {}),
    ]:
        try:
            results = fetcher(**kwargs)
            all_articles.extend(results)
            print(f"  ✅ {name}: {len(results)} 篇")
        except Exception as e:
            print(f"  ❌ {name} 失敗: {e}")

    print(f"\n{'='*60}")
    print(f"  過濾前：共 {len(all_articles)} 篇文章")
    print(f"{'='*60}\n")

    print("🔬 階段二：語意去重中 ...")
    engine = ArticleFilter()
    unique_articles = engine.process(all_articles)

    print(f"\n{'='*60}")
    print(f"  過濾後：共 {len(unique_articles)} 篇獨立事件")
    print(f"{'='*60}\n")

    print("📋 前 3 篇去重結果預覽：\n")
    for i, article in enumerate(unique_articles[:3]):
        print(f"  [{i+1}] {article.title}")
        print(f"      來源: {article.source}")
        if article.similar_sources:
            print(f"      🔗 已合併相似來源: {', '.join(article.similar_sources)}")
        else:
            print(f"      🔗 無相似文章被合併")
        print()

    print(f"{'='*60}")
    print("🏁 過濾層測試完畢")
    print(f"{'='*60}")
