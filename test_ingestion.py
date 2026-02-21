from src.data_ingestion.hn_scraper import fetch_hn_ai_stories
from src.data_ingestion.rss_parser import fetch_official_rss
from src.data_ingestion.hf_papers import fetch_hf_daily_papers


def test_source(name: str, fetcher, **kwargs):
    print(f"\n{'='*60}")
    print(f"  測試資料源：{name}")
    print(f"{'='*60}")

    try:
        articles = fetcher(**kwargs)
        print(f"✅ 成功抓取 {len(articles)} 筆資料\n")

        for i, article in enumerate(articles[:2]):
            print(f"  [{i+1}] 標題:     {article.title}")
            print(f"      來源:     {article.source}")
            print(f"      發布時間: {article.published_at}")
            print(f"      連結:     {article.url[:80]}")
            print()

        if not articles:
            print("  ⚠️ 此資料源在時間窗口內沒有抓到任何文章")

    except Exception as e:
        print(f"❌ 抓取失敗：{e}")


if __name__ == "__main__":
    print("🚀 開始測試數據採集層 (Data Ingestion)")

    test_source("Hacker News (AI 篩選)", fetch_hn_ai_stories, hours=24)
    test_source("官方 RSS Feeds", fetch_official_rss, hours=24)
    test_source("Hugging Face Daily Papers", fetch_hf_daily_papers)

    print(f"\n{'='*60}")
    print("🏁 所有測試執行完畢")
    print(f"{'='*60}")
