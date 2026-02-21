import os
from datetime import datetime
from typing import List

import telebot

from src.models.schemas import ScoredArticle


def format_daily_briefing(articles: List[ScoredArticle], is_downgraded: bool = False) -> str:
    """將評分後的文章格式化為 HTML 廣播訊息。"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"🤖 <b>Yoyo AI 全域情報 (2.0 嚴格版)</b> | {today}\n"]

    if is_downgraded:
        lines.append(
            "⚠️ <i>今日雷達未偵測到 S 級情報，"
            "啟動降級播報 (顯示 Top 3 潛力事件)。</i>\n"
        )

    for article in articles:
        ev = article.evaluation
        a = article.article
        summary = ev.executive_summary or ev.reasoning[:80]

        lines.append(
            f'<b>[{ev.total_score}分] {a.title}</b>\n'
            f'來源: {a.source} | <a href="{a.url}">🔗 閱讀原文</a>\n'
            f'🔥 <b>戰略簡報:</b> {summary}\n'
            f'━━━━━━━━━━'
        )

    lines.append("\n💬 <i>(此報告由 2.0 系統自動產出)</i>")
    return "\n".join(lines)


def send_telegram_broadcast(message: str):
    """將訊息廣播至所有 Telegram 群組。"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat_ids_raw = os.environ.get("TARGET_CHAT_IDS", "")

    if not token:
        print("[廣播] ⚠️ 未設定 TELEGRAM_BOT_TOKEN，跳過發送")
        return

    if not chat_ids_raw:
        print("[廣播] ⚠️ 未設定 TARGET_CHAT_IDS，跳過發送")
        return

    bot = telebot.TeleBot(token)
    chat_ids = [cid.strip() for cid in chat_ids_raw.split(",") if cid.strip()]

    print(f"[廣播] 開始發送至 {len(chat_ids)} 個群組 ...")
    for chat_id in chat_ids:
        try:
            bot.send_message(
                chat_id,
                message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            print(f"  ✅ 已發送至: {chat_id}")
        except Exception as e:
            print(f"  ❌ 發送至 {chat_id} 失敗: {e}")

    print("[廣播] 發送完畢")
