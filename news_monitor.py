"""
Agent 4 — Import/Export News Monitor
=====================================
ดึงข่าวนำเข้า-ส่งออก อาหาร ยา และ logistics จาก 3 กลุ่มแหล่งข่าว
แล้วส่งสรุปรายสัปดาห์เข้า Slack channel ที่กำหนด

รันทุก: วันจันทร์ และ วันพฤหัสบดี เวลา 09:00 AM
ผ่าน: Windows Task Scheduler
"""

import os
import json
import logging
import feedparser
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ── โหลด Environment Variables ──────────────────────────────────────────────
load_dotenv()

SLACK_BOT_TOKEN    = os.getenv("SLACK_BOT_TOKEN")
SLACK_NEWS_CHANNEL = os.getenv("SLACK_NEWS_CHANNEL_ID")   # channel ใหม่สำหรับข่าว
SLACK_USER_ID      = os.getenv("SLACK_USER_ID")

# Slack เป็น optional — ถ้าไม่มี token จะข้ามการส่ง (ใช้ได้ทั้งใน Streamlit และ standalone)
SLACK_ENABLED = bool(SLACK_BOT_TOKEN and SLACK_NEWS_CHANNEL)

# ── ตั้งค่า Logging ──────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

log_file = f"logs/news_{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── ไฟล์เก็บประวัติข่าวที่เคยส่งแล้ว ────────────────────────────────────────
HISTORY_FILE = "data/news_history.json"

# ── RSS Feeds แยกตามกลุ่ม ───────────────────────────────────────────────────
RSS_FEEDS = {

    # ── กลุ่มที่ 1: ข่าวไทย ──────────────────────────────────────────────────
    "ไทย": [
        {
            "name": "Bangkok Post — Business",
            "url": "https://www.bangkokpost.com/rss/data/business.xml",
        },
        {
            "name": "Prachachat",
            "url": "https://www.prachachat.net/feed/",
        },
        {
            "name": "Thairath — เศรษฐกิจ",
            "url": "https://www.thairath.co.th/rss/economic",
        },
        {
            "name": "Matichon",
            "url": "https://www.matichon.co.th/feed/",
        },
    ],

    # ── กลุ่มที่ 2: ข่าวต่างประเทศ ───────────────────────────────────────────
    "ต่างประเทศ": [
        {
            "name": "Reuters — Business",
            "url": "https://feeds.reuters.com/reuters/businessNews",
        },
        {
            "name": "FreightWaves",
            "url": "https://www.freightwaves.com/news/feed",
        },
        {
            "name": "Supply Chain Dive",
            "url": "https://www.supplychaindive.com/feeds/news/",
        },
    ],

    # ── กลุ่มที่ 3: อุตสาหกรรม Food / Pharma ─────────────────────────────────
    "Food/Pharma": [
        {
            "name": "Food Navigator",
            "url": "https://www.foodnavigator.com/rss",
        },
        {
            "name": "Food Navigator Asia",
            "url": "https://www.foodnavigator-asia.com/rss",
        },
        {
            "name": "Just Food",
            "url": "https://www.just-food.com/rss/",
        },
        {
            "name": "Pharma Manufacturing",
            "url": "https://www.pharmamanufacturing.com/rss/",
        },
    ],
}

# ── Keywords สำหรับกรองข่าว ──────────────────────────────────────────────────
#    ข่าวต้องมีคำเหล่านี้อย่างน้อย 1 คำ (ไม่สนใจตัวพิมพ์ใหญ่-เล็ก)
KEYWORDS = [
    # ภาษาไทย
    "นำเข้า", "ส่งออก", "ศุลกากร", "ภาษีนำเข้า", "สินค้าเกษตร",
    "อาหารนำเข้า", "ยานำเข้า", "ขนส่ง", "โลจิสติกส์", "พิธีการศุลกากร",
    "กรมศุลกากร", "กระทรวงพาณิชย์", "อย.", "อาหารและยา",
    # English
    "import", "export", "customs", "tariff", "freight", "logistics",
    "supply chain", "trade", "food safety", "pharma", "fda", "regulatory",
    "shipping", "cargo", "border", "duty", "quota",
]

# ── จำนวนวันย้อนหลังที่จะดึงข่าว (3 วัน ครอบคลุม Mon↔Thu gap) ──────────────
LOOKBACK_DAYS = 4


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: โหลดและบันทึก History
# ════════════════════════════════════════════════════════════════════════════

def load_history() -> set:
    """โหลด URL ที่เคยส่งแล้วจาก JSON file"""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("seen_urls", []))


def save_history(seen_urls: set):
    """บันทึก URL ที่ส่งแล้วกลับเข้า JSON"""
    # เก็บแค่ 500 URLs ล่าสุด เพื่อไม่ให้ไฟล์ใหญ่เกินไป
    url_list = list(seen_urls)[-500:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen_urls": url_list, "last_run": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: ดึงและกรองข่าวจาก RSS
# ════════════════════════════════════════════════════════════════════════════

def is_relevant(title: str, summary: str) -> bool:
    """เช็คว่าข่าวตรงกับ keyword ที่กำหนดหรือไม่"""
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in KEYWORDS)


def fetch_feed(feed_info: dict, seen_urls: set, cutoff_date: datetime) -> list:
    """
    ดึงข่าวจาก RSS feed 1 แหล่ง
    คืนค่า list ของข่าวใหม่ที่ยังไม่เคยส่ง
    """
    name = feed_info["name"]
    url  = feed_info["url"]
    new_articles = []

    try:
        feed = feedparser.parse(url)

        if feed.bozo and not feed.entries:
            logger.warning(f"⚠️ {name}: RSS parse error — {feed.bozo_exception}")
            return []

        logger.info(f"📡 {name}: พบ {len(feed.entries)} รายการ")

        for entry in feed.entries:
            article_url   = entry.get("link", "")
            title         = entry.get("title", "ไม่มีชื่อ")
            summary       = entry.get("summary", "")
            published_raw = entry.get("published_parsed") or entry.get("updated_parsed")

            # ── เช็ควันที่ ────────────────────────────────────────────────
            if published_raw:
                published_dt = datetime(*published_raw[:6])
                if published_dt < cutoff_date:
                    continue  # ข่าวเก่าเกินไป
            # ถ้า feed ไม่มีวันที่ ให้ผ่านไปก่อน (บางเว็บไม่มี)

            # ── เช็ค Duplicate ────────────────────────────────────────────
            if article_url in seen_urls:
                continue

            # ── เช็ค Keyword ─────────────────────────────────────────────
            if not is_relevant(title, summary):
                continue

            new_articles.append({
                "title": title.strip(),
                "url":   article_url,
                "date":  published_raw,
            })
            seen_urls.add(article_url)

    except Exception as e:
        logger.error(f"❌ {name}: {e}")

    return new_articles


# ════════════════════════════════════════════════════════════════════════════
# ฟังก์ชัน: ส่ง Slack
# ════════════════════════════════════════════════════════════════════════════

def send_slack(message: str):
    """ส่งข้อความเข้า Slack channel (ข้ามถ้าไม่มี credentials)"""
    if not SLACK_ENABLED:
        logger.info("⏭️ ข้าม Slack — ไม่มี token (ปกติเมื่อรันใน Streamlit)")
        return
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "channel": SLACK_NEWS_CHANNEL,
        "text": message,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    resp = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload, timeout=15)
    data = resp.json()
    if not data.get("ok"):
        logger.error(f"❌ Slack error: {data.get('error')}")
    else:
        logger.info("✅ ส่ง Slack สำเร็จ")


def format_slack_message(results_by_group: dict, total: int) -> str:
    """สร้างข้อความสรุปข่าวสำหรับ Slack"""
    today = datetime.now().strftime("%d %b %Y")
    mention = f"<@{SLACK_USER_ID}> " if SLACK_USER_ID else ""

    lines = [
        f"{mention}📰 *สรุปข่าวนำเข้า-ส่งออก ประจำสัปดาห์* — {today}",
        f"พบข่าวใหม่ที่เกี่ยวข้องทั้งหมด *{total} รายการ*\n",
    ]

    group_emojis = {"ไทย": "🇹🇭", "ต่างประเทศ": "🌐", "Food/Pharma": "🍽️"}

    for group, articles in results_by_group.items():
        if not articles:
            continue
        emoji = group_emojis.get(group, "📌")
        lines.append(f"{emoji} *{group}* ({len(articles)} รายการ)")
        for art in articles[:5]:   # สูงสุด 5 ข่าวต่อกลุ่ม
            lines.append(f"  • <{art['url']}|{art['title']}>")
        if len(articles) > 5:
            lines.append(f"  _...และอีก {len(articles) - 5} รายการ_")
        lines.append("")

    lines.append("_Agent 4 — Import/Export News Monitor_")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("🚀 เริ่มรัน Import/Export News Monitor")
    logger.info(f"⏰ เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # โหลด history
    seen_urls = load_history()
    logger.info(f"📋 History: {len(seen_urls)} URLs ที่เคยส่งแล้ว")

    # กำหนด cutoff date
    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    # วนดึงข่าวทุกกลุ่ม
    results_by_group = {}
    total_new = 0

    for group, feeds in RSS_FEEDS.items():
        logger.info(f"\n── กลุ่ม: {group} ──")
        group_articles = []

        for feed_info in feeds:
            articles = fetch_feed(feed_info, seen_urls, cutoff_date)
            group_articles.extend(articles)
            logger.info(f"   └─ {feed_info['name']}: {len(articles)} รายการใหม่")

        results_by_group[group] = group_articles
        total_new += len(group_articles)

    logger.info(f"\n✅ รวมข่าวใหม่: {total_new} รายการ")

    # ส่ง Slack
    if total_new > 0:
        message = format_slack_message(results_by_group, total_new)
        send_slack(message)
        logger.info("📨 ส่ง Slack เรียบร้อย")
    else:
        # ยังส่งแจ้งให้รู้ว่า agent ทำงานปกติ แม้ไม่มีข่าวใหม่
        send_slack(
            f"📰 *สรุปข่าวนำเข้า-ส่งออก* — {datetime.now().strftime('%d %b %Y')}\n"
            f"ไม่พบข่าวใหม่ที่เกี่ยวข้องในช่วง {LOOKBACK_DAYS} วันที่ผ่านมา\n"
            "_Agent 4 — Import/Export News Monitor_"
        )
        logger.info("📨 ส่ง Slack (ไม่มีข่าวใหม่)")

    # บันทึก history
    save_history(seen_urls)
    logger.info("💾 บันทึก history เรียบร้อย")

    # ── บันทึกข่าวรอบนี้ลง news_latest.json (สำหรับ Agent 5) ──────────────
    latest_file = "data/news_latest.json"
    latest_payload = {
        "run_date": datetime.now().isoformat(),
        "total": total_new,
        "articles_by_group": {
            group: [
                {"title": a["title"], "url": a["url"]}
                for a in articles
            ]
            for group, articles in results_by_group.items()
        },
    }
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(latest_payload, f, ensure_ascii=False, indent=2)
    logger.info(f"📤 บันทึก news_latest.json ({total_new} รายการ) — พร้อมส่งต่อ Agent 5")

    logger.info("🏁 จบการทำงาน\n")

    # คืนค่า results เผื่อ run_pipeline.py เรียกใช้
    return results_by_group, total_new


if __name__ == "__main__":
    main()
