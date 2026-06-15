"""
Agent 5 — Marketing Research Analyst
======================================
อ่านข่าวที่ Agent 4 สกรีนมาแล้ว (data/news_latest.json)
→ ส่งให้ Claude วิเคราะห์เชิงธุรกิจ
→ บันทึกรายงานเป็น reports/marketing_report_YYYY-MM-DD.md

รันหลังจาก news_monitor.py เสมอ (ผ่าน run_pipeline.py)
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import anthropic                               # ✅ Claude API

# ── โหลด Environment Variables ──────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")      # ✅ เปลี่ยนจาก GEMINI_API_KEY

if not API_KEY:
    raise ValueError(
        "❌ Missing ANTHROPIC_API_KEY in .env\n"
        "   ขอ Key ได้ที่: https://console.anthropic.com/"
    )

# ── ตั้งค่า Claude ───────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=API_KEY)  # ✅ เปลี่ยนจาก genai.Client
MODEL  = "claude-sonnet-4-6"                  # ✅ เปลี่ยนจาก gemini-2.5-flash

# ── System Prompt (บทบาทของ Agent) ──────────────────────────────────────────
SYSTEM_PROMPT = """คุณเป็นนักวิเคราะห์การตลาดอาวุโสของบริษัท Jet8 ซึ่งเป็น Freight Forwarder ในไทย
เชี่ยวชาญด้านนำเข้า-ส่งออก อาหารและยา

หน้าที่ของคุณคืออ่านข่าวที่รวบรวมมา แล้ววิเคราะห์ในมุมธุรกิจ:
- ชี้ประเด็นสำคัญที่กระทบธุรกิจ Freight Forwarder
- ระบุโอกาสและความเสี่ยงอย่างชัดเจน
- แนะนำ action ที่ปฏิบัติได้จริงสำหรับทีมการตลาด
- ตอบเป็นภาษาไทย กระชับ ตรงประเด็น แต่ละ bullet ไม่เกิน 3 ประโยค
"""

# เก็บจำนวนโทเคนของการเรียกครั้งล่าสุด (run_pipeline.py มาอ่านค่านี้ได้)
last_usage = {"input": 0, "output": 0, "total": 0}

# ── ตั้งค่า Logging ──────────────────────────────────────────────────────────
os.makedirs("logs",    exist_ok=True)
os.makedirs("reports", exist_ok=True)

log_file = f"logs/researcher_{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

LATEST_NEWS_FILE = "data/news_latest.json"
REPORTS_DIR      = "reports"


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: โหลดข่าวจาก Agent 4
# ════════════════════════════════════════════════════════════════════════════

def load_latest_news() -> dict:
    """โหลดข่าวจาก news_latest.json ที่ Agent 4 สร้างไว้"""
    if not os.path.exists(LATEST_NEWS_FILE):
        logger.warning("⚠️ ไม่พบ news_latest.json — รัน news_monitor.py ก่อน")
        return {}
    with open(LATEST_NEWS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"📂 โหลดข่าว {data.get('total', 0)} รายการ")
    return data


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: สร้าง Prompt สำหรับ Claude
# ════════════════════════════════════════════════════════════════════════════

def build_user_prompt(articles_by_group: dict) -> str:
    """รวบรวมข่าวทั้งหมดให้ Claude อ่าน"""
    news_lines = []
    for group, articles in articles_by_group.items():
        if not articles:
            continue
        news_lines.append(f"\n### {group}")
        for i, art in enumerate(articles, 1):
            news_lines.append(f"{i}. {art['title']}")
            news_lines.append(f"   URL: {art['url']}")

    news_text = "\n".join(news_lines) if news_lines else "ไม่มีข่าวใหม่"

    return f"""ข่าวและบทความที่คัดสรรมาในสัปดาห์นี้:
{news_text}

กรุณาวิเคราะห์และสรุปในรูปแบบต่อไปนี้:

## 📌 ประเด็นสำคัญประจำสัปดาห์
(3–5 ประเด็นหลัก อธิบายแต่ละประเด็น 2–3 ประโยค)

## 🟢 โอกาสสำหรับ Jet8
(3–5 โอกาสทางธุรกิจ พร้อมอธิบายว่าทำไมถึงเป็นโอกาส)

## 🔴 ความเสี่ยงที่ต้องระวัง
(2–4 ความเสี่ยง พร้อมแนะนำวิธีรับมือ)

## 💡 Action ที่แนะนำสัปดาห์นี้
(2–3 action สำหรับทีมการตลาด เช่น content idea, กลุ่มลูกค้าที่ควรติดต่อ)
"""


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: เรียก Claude วิเคราะห์
# ════════════════════════════════════════════════════════════════════════════

def analyze_with_gemini(user_prompt: str) -> str:
    """ชื่อเดิมเพื่อ backward-compatibility — ใช้ Claude จริง"""
    return analyze(user_prompt)


def analyze(user_prompt: str) -> str:
    """ส่ง prompt ให้ Claude และรับผลวิเคราะห์"""
    logger.info("🤖 ส่งข้อมูลให้ Claude วิเคราะห์...")
    try:
        response = client.messages.create(     # ✅ Claude API
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        last_usage["input"]  = response.usage.input_tokens
        last_usage["output"] = response.usage.output_tokens
        last_usage["total"]  = response.usage.input_tokens + response.usage.output_tokens

        logger.info(f"✅ Claude ตอบกลับแล้ว (tokens: {last_usage['total']:,})")
        return response.content[0].text

    except Exception as e:
        logger.error(f"❌ Claude error: {e}")
        return f"❌ เกิดข้อผิดพลาดในการวิเคราะห์: {e}"


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: บันทึกรายงาน
# ════════════════════════════════════════════════════════════════════════════

def save_report(analysis: str, total_articles: int, run_date: str) -> str:
    """บันทึกรายงานเป็นไฟล์ .md"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(REPORTS_DIR, f"marketing_report_{date_str}.md")

    report = f"""# รายงานวิจัยการตลาด — {date_str}

> **สร้างโดย:** Agent 5 — Marketing Research Analyst (Claude {MODEL})
> **ข้อมูลจาก:** {total_articles} บทความ (รอบ {run_date[:10]})
> **บริษัท:** Jet8 Freight Forwarder

---

{analysis}

---
*รายงานนี้สร้างอัตโนมัติโดย Agent Pipeline: news_monitor → marketing_researcher*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"📄 บันทึกรายงาน: {filepath}")
    return filepath


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("🔬 เริ่มรัน Marketing Research Analyst")
    logger.info(f"⏰ เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    data = load_latest_news()
    if not data:
        logger.warning("⛔ ไม่มีข้อมูลข่าว — หยุดทำงาน")
        return None

    articles_by_group = data.get("articles_by_group", {})
    total             = data.get("total", 0)
    run_date          = data.get("run_date", "")

    if total == 0:
        logger.info("📭 ไม่มีข่าวใหม่ในรอบนี้ — ไม่สร้างรายงาน")
        return None

    user_prompt = build_user_prompt(articles_by_group)
    analysis    = analyze(user_prompt)
    filepath    = save_report(analysis, total, run_date)

    logger.info(f"✅ รายงานพร้อมแล้ว → {filepath}")
    logger.info("🏁 จบการทำงาน\n")
    return filepath


if __name__ == "__main__":
    main()
