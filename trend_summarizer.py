# ============================================================
#  Trend Summarizer Agent — สรุปเทรนด์รายเดือนอัตโนมัติ
#  รันทุกวันที่ 5 ของเดือน (สรุปเดือนก่อนหน้า)
#
#  รันด้วยมือ:  python trend_summarizer.py
#  อัตโนมัติ:  Windows Task Scheduler / Cowork Schedule
# ============================================================

import os
import json
import anthropic
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── ยืม RSS config + keyword filter จาก news_monitor ────────────────────────
from news_monitor import RSS_FEEDS, is_relevant

# ── ค่าคงที่ ─────────────────────────────────────────────────────────────────
TRENDS_DIR   = "data/trends"
MODEL        = "claude-sonnet-4-6"
LOOKBACK_DAYS = 38   # ดึงย้อนหลัง ~5 สัปดาห์ ให้ครอบคลุม 1 เดือนเต็ม

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

os.makedirs(TRENDS_DIR, exist_ok=True)

SYSTEM_PROMPT = """คุณเป็น Market Intelligence Analyst ของบริษัท Jet8
Freight Forwarder เชี่ยวชาญด้านนำเข้า-ส่งออกอาหารและยาระหว่างประเทศในไทย

หน้าที่: วิเคราะห์พาดหัวข่าวและสรุปเทรนด์ที่สำคัญต่อธุรกิจ B2B นำเข้า-ส่งออก

เน้นวิเคราะห์:
- กฎระเบียบและประกาศจาก อย. / FDA / กรมศุลกากร / กระทรวงพาณิชย์
- ความเคลื่อนไหวของตลาดอาหารและยาในไทยและภูมิภาค
- สถานการณ์โลจิสติกส์ ค่าระวาง ความล่าช้าของห่วงโซ่อุปทาน
- โอกาสและความเสี่ยงต่อผู้นำเข้า-ส่งออก SME ไทย

ตอบเป็นภาษาไทย รูปแบบ Markdown อ่านง่าย กระชับ ตรงประเด็น"""

last_usage = {"input": 0, "output": 0, "total": 0}


# ════════════════════════════════════════════════════════════════
#  ดึงข่าวจาก RSS ย้อนหลัง 1 เดือน (ไม่กรอง history)
# ════════════════════════════════════════════════════════════════

def fetch_monthly_articles() -> dict[str, list[dict]]:
    """
    ดึงข่าวจากทุก RSS feed ย้อนหลัง LOOKBACK_DAYS วัน
    Returns: {"กลุ่ม": [{"title": ..., "url": ...}, ...]}
    """
    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    results: dict[str, list[dict]] = {}

    for group, feeds in RSS_FEEDS.items():
        articles: list[dict] = []
        seen: set[str] = set()

        for feed_info in feeds:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries:
                    url     = entry.get("link", "").strip()
                    title   = entry.get("title", "").strip()
                    summary = entry.get("summary", "")
                    pub_raw = entry.get("published_parsed") or entry.get("updated_parsed")

                    # กรองตามวันที่
                    if pub_raw:
                        try:
                            pub_dt = datetime(*pub_raw[:6])
                            if pub_dt < cutoff:
                                continue
                        except Exception:
                            pass  # ถ้า parse date ไม่ได้ ให้ผ่าน

                    # กรอง duplicate และ keyword
                    if not url or url in seen:
                        continue
                    if not is_relevant(title, summary):
                        continue

                    articles.append({"title": title, "url": url})
                    seen.add(url)

            except Exception as e:
                print(f"⚠️ RSS {feed_info['name']}: {e}")

        results[group] = articles

    return results


# ════════════════════════════════════════════════════════════════
#  สร้าง Prompt สำหรับ Claude
# ════════════════════════════════════════════════════════════════

def _build_prompt(month: int, year: int, articles_by_group: dict) -> str:
    month_name = THAI_MONTHS[month]
    total = sum(len(arts) for arts in articles_by_group.values())

    # จัดเรียงพาดหัวข่าวแยกกลุ่ม
    news_block = ""
    group_emojis = {"ไทย": "🇹🇭", "ต่างประเทศ": "🌐", "Food/Pharma": "🍽️"}
    for group, arts in articles_by_group.items():
        if not arts:
            continue
        emoji = group_emojis.get(group, "📌")
        news_block += f"\n### {emoji} {group} ({len(arts)} รายการ)\n"
        for a in arts[:25]:   # สูงสุด 25 รายการต่อกลุ่ม
            news_block += f"- {a['title']}\n"

    return f"""วิเคราะห์พาดหัวข่าวนำเข้า-ส่งออกประจำเดือน{month_name} {year}
รวม {total} รายการจาก 3 กลุ่มแหล่งข่าว:
{news_block}

สรุปในรูปแบบนี้เท่านั้น:

# 📊 สรุปเทรนด์อุตสาหกรรม เดือน{month_name} {year}
*Jet8 Market Intelligence — จัดทำโดย Trend Summarizer Agent*
*อ้างอิงจากพาดหัวข่าว {total} รายการ ช่วง {LOOKBACK_DAYS} วันล่าสุด*

---

## 🔥 เทรนด์สำคัญ 5 อันดับ
*(เรียงตามความสำคัญต่อธุรกิจนำเข้า-ส่งออก Jet8)*

1. **[ชื่อเทรนด์ที่ 1]**
   [อธิบาย 2-3 ประโยค — เกิดจากอะไร ส่งผลอย่างไร]

2. **[ชื่อเทรนด์ที่ 2]**
   [...]

3. **[ชื่อเทรนด์ที่ 3]**
   [...]

4. **[ชื่อเทรนด์ที่ 4]**
   [...]

5. **[ชื่อเทรนด์ที่ 5]**
   [...]

---

## 📈 สถานการณ์รายอุตสาหกรรม

### 🍽️ อาหารและเกษตร
- ...

### 💊 ยาและเวชภัณฑ์
- ...

### 🚢 โลจิสติกส์และขนส่ง
- ...

---

## ⚠️ ความเสี่ยงที่ต้องจับตาเดือนหน้า
- ...

## 💡 โอกาสสำหรับ Jet8
- ...

---

## 🎯 หัวข้อคอนเทนต์แนะนำสำหรับเดือนหน้า
*(พร้อมส่งต่อให้ Planner Agent)*

| # | หัวข้อ | ช่องทาง | เหตุผล |
|---|--------|---------|--------|
| 1 | | Facebook | |
| 2 | | LinkedIn | |
| 3 | | Facebook | |
| 4 | | เว็บไซต์ | |
| 5 | | LinkedIn | |
"""


# ════════════════════════════════════════════════════════════════
#  Public API
# ════════════════════════════════════════════════════════════════

def generate_trend_summary(month: int, year: int) -> tuple[str, str]:
    """
    สร้างสรุปเทรนด์รายเดือน → บันทึก .md → คืน (content, filepath)

    Parameters:
        month — เดือน (1-12)
        year  — ปี ค.ศ.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print(f"📡 กำลังดึงข่าวจาก RSS feeds (ย้อนหลัง {LOOKBACK_DAYS} วัน)...")
    articles_by_group = fetch_monthly_articles()
    total = sum(len(arts) for arts in articles_by_group.values())
    print(f"   พบข่าวที่เกี่ยวข้อง {total} รายการ")

    if total == 0:
        content = (
            f"# สรุปเทรนด์ เดือน{THAI_MONTHS[month]} {year}\n\n"
            f"⚠️ ไม่พบข่าวในช่วง {LOOKBACK_DAYS} วันที่ผ่านมา\n"
            "RSS feeds อาจไม่มีบทความใหม่ หรือ keyword ไม่ match — ลองรันใหม่ในอีกไม่กี่วัน"
        )
    else:
        print("🤖 กำลังวิเคราะห์กับ Claude...")
        prompt = _build_prompt(month, year, articles_by_group)
        response = client.messages.create(
            model=MODEL,
            max_tokens=2500,
            system=[{"type": "text", "text": SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        last_usage["input"]  = response.usage.input_tokens
        last_usage["output"] = response.usage.output_tokens
        last_usage["total"]  = response.usage.input_tokens + response.usage.output_tokens
        content = response.content[0].text
        print(f"   ✅ วิเคราะห์เสร็จ (tokens: {last_usage['total']:,})")

    # บันทึกไฟล์
    fname = f"trend_{year}_{month:02d}.md"
    fpath = os.path.join(TRENDS_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 บันทึกแล้ว: {fpath}")

    return content, fpath


def list_saved_trends() -> list[dict]:
    """คืนรายการสรุปเทรนด์ที่บันทึกไว้ เรียงล่าสุดก่อน"""
    trends = []
    if not os.path.exists(TRENDS_DIR):
        return trends
    for fname in sorted(os.listdir(TRENDS_DIR), reverse=True):
        if not (fname.endswith(".md") and fname.startswith("trend_")):
            continue
        parts = fname.replace(".md", "").split("_")  # ["trend", "YYYY", "MM"]
        try:
            y, m = int(parts[1]), int(parts[2])
            fpath = os.path.join(TRENDS_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            trends.append({
                "year": y, "month": m, "filepath": fpath, "content": content,
                "label": f"{THAI_MONTHS[m]} {y}",
            })
        except Exception:
            pass
    return trends


def get_latest_trend_for_planner() -> str:
    """คืน content เทรนด์ล่าสุด (ส่วน 🎯 หัวข้อคอนเทนต์) สำหรับ Planner"""
    trends = list_saved_trends()
    if not trends:
        return ""
    full = trends[0]["content"]
    # ตัดเฉพาะส่วน 🎯 เป็นต้นไป ถ้ามี
    marker = "## 🎯"
    idx = full.find(marker)
    if idx >= 0:
        # คืนทั้งหมดตั้งแต่ trend หัวข้อขึ้นไป (เพื่อให้ Planner เห็นภาพรวมด้วย)
        return full[:3000]   # จำกัด 3000 ตัวอักษรไม่ให้ใช้ token มากเกินไป
    return full[:3000]


# ════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    now = datetime.now()

    # รันวันที่ 5 → สรุปเดือนที่แล้ว
    if now.month == 1:
        target_month, target_year = 12, now.year - 1
    else:
        target_month, target_year = now.month - 1, now.year

    print("=" * 60)
    print(f"📊 Trend Summarizer — เดือน{THAI_MONTHS[target_month]} {target_year}")
    print("=" * 60)

    content, fpath = generate_trend_summary(target_month, target_year)
    print(f"\n✅ เสร็จแล้ว!")
    print(f"📄 ไฟล์: {fpath}")
    print(f"🔢 Tokens: {last_usage['total']:,}")
    print("\n--- ตัวอย่าง 10 บรรทัดแรก ---")
    print("\n".join(content.split("\n")[:10]))
