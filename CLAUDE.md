# CLAUDE.md — 專案交接文件

## 專案概述

**Yoyo AI 商業情報系統 2.0** — 一個企業級的 AI 商業情報自動化推播系統。
每日自動從多個來源採集科技商業新聞，經語意去重、LLM 量化評分後，將 Top 3 高價值情報推播至 Telegram 群組。

## 技術架構（四層漏斗）

```
採集層 → 去重層 → 評分層 → 廣播層
```

### 1. 採集層 (Data Ingestion)

- `src/data_ingestion/hn_scraper.py` — Hacker News 爬蟲，過濾商業相關關鍵字（launch, funding, acquisition 等）
- `src/data_ingestion/rss_parser.py` — RSS 解析器，7 個商業科技來源（TechCrunch, Product Hunt, The Verge, Microsoft, Google, Meta, NVIDIA）
- 所有採集器回傳 `List[RawArticle]`

### 2. 去重層 (Filtering)

- `src/filtering/dedup_engine.py` — 使用 `all-MiniLM-L6-v2` 語意模型做 Embedding + Cosine Similarity 貪婪分群，閾值 0.85
- 清洗 HTML 標籤、亂碼，過濾過短文章（<30 字元）

### 3. 評分層 (Scoring)

- `src/scoring/llm_evaluator.py` — 使用 GPT-4o-mini + JSON mode 進行量化評分
- 三維度：商業影響力 (0-40)、市場具體度 (0-35)、產品新鮮度 (0-25)
- 及格線：總分 >= 65 為 qualified
- 強制繁體中文輸出，executive_summary 含「🎯 白話解讀」+「💰 商業衝擊」

### 4. 廣播層 (Notifications)

- `src/notifications/broadcaster.py` — HTML 格式化 + Telegram 多群組廣播
- 支援降級模式：無及格文章時取 Top 3 潛力事件播報

## 資料模型 (`src/models/schemas.py`)

- `RawArticle` — title, url, source, published_at, content_snippet, similar_sources
- `EvaluationResult` — reasoning, impact_score, specificity_score, novelty_score, total_score, is_qualified, executive_summary
- `ScoredArticle` — article (RawArticle) + evaluation (EvaluationResult)

## 進入點

- `main.py` — 系統總指揮，執行完整四階段流程
- `test_ingestion.py` — 測試採集層
- `test_filtering.py` — 測試採集+去重層
- `test_scoring.py` — 測試採集+去重+評分層

## 環境變數（`.env` 或 GitHub Secrets）

- `OPENAI_API_KEY` — OpenAI API 金鑰（必要）
- `TELEGRAM_BOT_TOKEN` 或 `TELEGRAM_TOKEN` — Telegram Bot Token（廣播用）
- `TARGET_CHAT_IDS` — 逗號分隔的 Telegram chat ID 列表

## GitHub Actions

- `.github/workflows/main.yml` — v1.0 舊版 workflow（使用 Tavily，已被 2.0 取代但檔案仍保留）
- `.github/workflows/daily_briefing.yml` — 2.0 版 workflow（目前為空檔，待設定）

## 套件依賴

見 `requirements.txt`，核心：requests, feedparser, sentence-transformers, pydantic, openai, pyTelegramBotAPI, python-dotenv

## 開發注意事項

- Python 版本：3.14（本機）/ 建議 CI 用 3.11+
- 本機測試需先 `pip install -r requirements.txt` 並在 `.env` 設定 `OPENAI_API_KEY`
- `sentence-transformers` 首次執行會下載 ~80MB 的 `all-MiniLM-L6-v2` 模型
- OpenAI 使用 `response_format={"type": "json_object"}` 而非 beta Structured Outputs（因 Python 3.14 編碼相容問題）
- 回覆語言：所有面向使用者的輸出使用繁體中文

## 待辦 / 已知改進方向

- [ ] 設定 `daily_briefing.yml` 的 GitHub Actions workflow（cron 排程、secrets 設定）
- [ ] 去重閾值可考慮從 0.85 降至 0.75，以合併「同事件不同角度」的報導
- [ ] 可新增更多 RSS 來源或 Tavily 搜尋作為補充採集源
- [ ] 可考慮加入 content enrichment（抓取文章全文）以提升評分精度
