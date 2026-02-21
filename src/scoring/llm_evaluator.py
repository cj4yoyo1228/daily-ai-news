import json
from typing import List

import openai

from src.models.schemas import RawArticle, EvaluationResult, ScoredArticle

SYSTEM_PROMPT = (
    "你是一位矽谷頂尖創投 (VC) 兼華爾街科技產業分析師。"
    "你的任務是嚴格評估傳入的新聞/事件文本，尋找具有強大商業變現潛力、能改變市場格局的 Alpha 訊號。\n\n"
    "評分維度 (總分 100)：\n"
    "1. 商業影響力與資金動能 (Commercial Impact, 0-40分)：獲巨額融資、大廠重磅併購、"
    "或能替企業大幅降本增效得高分；常規軟體更新、無商業模式的玩具專案得低分。\n"
    "2. 市場具體度 (Market Specificity, 0-35分)：有明確的目標客群、具體的落地使用場景 (Use Cases)、"
    "或產品定價策略得高分；若是純學術理論、毫無落地場景的空泛願景則得低分。"
    "(註：早期高潛力產品即使尚無營收或融資數據，只要應用場景極度明確且具破壞性，亦可給予高分)\n"
    "3. 產品新鮮度與護城河 (Product Novelty, 0-25分)：開創全新商業模式、解決痛點的新產品發布 "
    "(如 Product Hunt 熱門)、大廠的突襲式戰略得高分。\n\n"
    "如果總分 >= 65，is_qualified 必須設為 true。\n"
    "如果總分 < 65，is_qualified 設為 false，executive_summary 設為 null。\n\n"
    "【嚴格格式要求】：\n"
    "你的輸出語言必須絕對使用「繁體中文 (zh-TW)」。禁止直接照抄英文摘要或使用生硬學術名詞。\n"
    "請在 executive_summary 欄位中，嚴格按照以下結構輸出（請使用 \\n 來換行排版）：\n\n"
    "🎯 白話解讀：(用一句話向非技術背景的 CEO 解釋這個產品/事件到底在幹嘛，解決了什麼痛點)\n"
    "💰 商業衝擊：(具體指出這會威脅到誰的生意？替誰省下成本？或是展示了什麼新的商業變現模式？)\n\n"
    "你必須嚴格以下列 JSON 格式回覆，不要加任何多餘文字：\n"
    '{"reasoning": "...", "impact_score": 0, "specificity_score": 0, '
    '"novelty_score": 0, "total_score": 0, "is_qualified": false, '
    '"executive_summary": null}'
)


def evaluate_events(articles: List[RawArticle]) -> List[ScoredArticle]:
    """用 LLM 對每篇文章進行量化評分，回傳達標且排序後的結果。"""
    client = openai.OpenAI()
    total = len(articles)
    scored: List[ScoredArticle] = []

    for i, article in enumerate(articles, 1):
        print(f"[Scoring] 正在評分 {i}/{total} — {article.title[:50]}...")

        user_payload = json.dumps(
            {
                "title": article.title,
                "source": article.source,
                "content_snippet": article.content_snippet,
            },
            ensure_ascii=False,
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_payload},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            raw_json = response.choices[0].message.content
            evaluation = EvaluationResult.model_validate_json(raw_json)

            scored.append(
                ScoredArticle(article=article, evaluation=evaluation)
            )
            tag = "✅ 達標" if evaluation.is_qualified else "—"
            print(f"  -> 總分 {evaluation.total_score} {tag}")

        except Exception as e:
            print(f"  ❌ 評分失敗: {e}")
            continue

    scored.sort(key=lambda s: s.evaluation.total_score, reverse=True)
    qualified_count = sum(1 for s in scored if s.evaluation.is_qualified)

    print(f"\n[Scoring] 評分完成：{len(scored)} 篇已評 / {qualified_count} 篇達標 (>=65)")
    return scored
