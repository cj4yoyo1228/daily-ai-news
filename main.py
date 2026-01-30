import os
import telebot
from openai import OpenAI
from tavily import TavilyClient
from datetime import datetime

# 從 GitHub Secrets 讀取金鑰
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# 🌟 設定區：配送清單
TARGET_CHAT_IDS = [
    "-5249899047",  # 原本的群組
    "-5159224987"   # 新增的群組
]

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

def generate_and_send_report():
    print(f"🚀 [{get_today_date()}] GitHub Action 啟動：開始執行全域掃描...")
    
    queries = [
        "Latest strategic moves and acquisitions by major AI tech giants (Apple, Google, Microsoft, Meta) last 24 hours",
        "Breaking news in AI semiconductor and hardware industry (Nvidia, AMD, TSMC) last 24 hours",
        "Most trending new AI agents and open source LLMs on GitHub/HuggingFace today",
        "Major AI security breaches, vulnerabilities and ethical controversies reported today"
    ]
    
    combined_results = []
    
    for q in queries:
        try:
            res = tavily.search(query=q, search_depth="advanced", max_results=2, days=1)
            combined_results.extend(res['results'])
        except: pass

    if not combined_results:
        print("⚠️ 24小時內資訊不足，擴大範圍...")
        for q in queries:
             try:
                res = tavily.search(query=q, search_depth="advanced", max_results=2, days=2)
                combined_results.extend(res['results'])
             except: pass

    raw_text = "\n".join([f"來源:{i['title']}|URL:{i['url']}|內容:{i['content']}" for i in combined_results[:12]])

    prompt = f"""
    你現在是**科技情報局的總編輯**。
    請從以下資料篩選出 **3 則** 對全球市場或技術發展 **最具影響力** 的新聞。
    
    【格式 - HTML】
    <b>1. [新聞標題]</b>
    <a href="URL">🔗 來源</a>
    
    🔥 <b>深度戰略解讀：</b>
    (這件事背後的商業或技術意義)
    
    ⚖️ <b>贏家與輸家：</b>
    • <b>贏家：</b> ...
    • <b>輸家：</b> ...
    
    💡 <b>決策觀點：</b> (給管理層的建議)
    ━━━━━━━━━━
    
    請產出 3 則。使用繁體中文。
    
    【原始資料庫】：
    {raw_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        
        report_content = response.choices[0].message.content.replace("```html", "").replace("```", "")
        header = f"🤖 <b>Yoyo AI 全域情報 (廣播版)</b> | {get_today_date()}\n\n"
        footer = "\n💬 <i>(此報告由 GitHub Actions 自動廣播)</i>"
        
        # 🚚 開始迴圈發送
        print("🚚 開始進行多群組廣播...")
        for chat_id in TARGET_CHAT_IDS:
            try:
                bot.send_message(
                    chat_id, 
                    header + report_content + footer, 
                    parse_mode="HTML", 
                    disable_web_page_preview=True
                )
                print(f"✅ 已發送至群組: {chat_id}")
            except Exception as e:
                print(f"❌ 發送至群組 {chat_id} 失敗: {e}")
        
        print("🎉 任務全部完成。")
        
    except Exception as e:
        print(f"❌ 核心錯誤: {e}")
        exit(1)

if __name__ == "__main__":
    generate_and_send_report()
