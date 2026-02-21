from dotenv import load_dotenv
load_dotenv()

from src.data_ingestion.hn_scraper import fetch_hn_ai_stories
from src.data_ingestion.rss_parser import fetch_official_rss
from src.filtering.dedup_engine import ArticleFilter
from src.scoring.llm_evaluator import evaluate_events


if __name__ == "__main__":
    print("🚀 開始測試 LLM 量化評分矩陣\n")

    print("📡 階段一：數據採集 (HN + RSS only) ...")
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

    print(f"\n🔬 階段二：語意去重 ...")
    engine = ArticleFilter()
    unique_articles = engine.process(all_articles)

    print(f"\n🧠 階段三：LLM 評分 ({len(unique_articles)} 篇送入) ...\n")
    qualified = evaluate_events(unique_articles)

    print(f"\n{'='*60}")
    print(f"  打分完畢！合格文章共 {len(qualified)} 篇")
    print(f"{'='*60}\n")

    for i, scored in enumerate(qualified, 1):
        ev = scored.evaluation
        print(f"  [{i}] {scored.article.title}")
        print(f"      總分: {ev.total_score} (影響力:{ev.impact_score} 具體:{ev.specificity_score} 新鮮:{ev.novelty_score})")
        print(f"      📌 {ev.executive_summary}")
        if scored.article.similar_sources:
            print(f"      🔗 合併來源: {', '.join(scored.article.similar_sources)}")
        print()

    print(f"{'='*60}")
    print("🏁 評分層測試完畢")
    print(f"{'='*60}")
