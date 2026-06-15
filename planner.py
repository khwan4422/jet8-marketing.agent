# ============================================================
#  Planner Agent — วางแผนธีมและตารางโพสต์รายเดือน
#  สำหรับ Jet8 Freight Forwarder (Food & Pharma)
# ============================================================

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]

SYSTEM_PROMPT = """คุณเป็น Content Strategist อาวุโสของบริษัท Jet8
บริษัทนำเข้า-ส่งออกอาหารและยาระหว่างประเทศ กลุ่มลูกค้าหลักเป็น B2B (ผู้ประกอบการ Food & Pharma)

วางแผนคอนเทนต์โดยคำนึงถึง:
- เทศกาลและวันหยุดของไทย
- งานแสดงสินค้าและอีเวนต์อุตสาหกรรม
- กฎระเบียบ อย./FDA ที่ควรสื่อสาร
- เทรนด์การนำเข้า-ส่งออกช่วงนั้น

ตอบเป็นภาษาไทย จัดรูปแบบ Markdown ให้อ่านง่าย"""

last_usage = {"input": 0, "output": 0, "total": 0}


def generate_plan(month: int, year: int, focus: str = "", events: list = None) -> str:
    """สร้างแผนคอนเทนต์รายเดือน

    Parameters:
        month  — เดือน (1-12)
        year   — ปี ค.ศ.
        focus  — หัวข้อพิเศษที่อยากเน้นเดือนนี้ (optional)
        events — รายการอีเวนต์จาก event_tracker (optional)
    """
    month_name = THAI_MONTHS[month]
    extras = []

    if focus:
        extras.append(f"**โฟกัสพิเศษ:** {focus}")
    if events:
        lines = "\n".join(
            f"- {e['name']} ({e['start_date']} ถึง {e['end_date']}): {e['purpose']}"
            for e in events
        )
        extras.append(f"**อีเวนต์ในเดือนนี้:**\n{lines}")

    extra_text = "\n\n" + "\n\n".join(extras) if extras else ""

    prompt = f"""วางแผนคอนเทนต์เดือน{month_name} {year}{extra_text}

สร้างแผนในรูปแบบนี้:

## 🎯 ธีมหลักเดือน{month_name}
(1-2 ประโยค อธิบายทิศทางภาพรวมของเดือน)

## 📋 แผนรายสัปดาห์
| สัปดาห์ | ธีม | แนวคิดหลัก | ช่องทางแนะนำ |
|---------|-----|-----------|-------------|
| สัปดาห์ 1 | | | |
| สัปดาห์ 2 | | | |
| สัปดาห์ 3 | | | |
| สัปดาห์ 4 | | | |

## 💡 หัวข้อคอนเทนต์แนะนำ

**Facebook (3-4 หัวข้อ)**
- ...

**LinkedIn (3-4 หัวข้อ)**
- ...

**เว็บไซต์/บล็อก (2-3 หัวข้อ)**
- ...

## 🗓️ วันสำคัญที่ควรทำคอนเทนต์
(เทศกาล, งานแสดงสินค้า, กำหนดนำเข้า-ส่งออก)

## ⚠️ ข้อควรระวังเดือนนี้
(ประเด็นที่ต้องระมัดระวัง หรือหัวข้อที่ควรหลีกเลี่ยง)
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    last_usage["input"]  = response.usage.input_tokens
    last_usage["output"] = response.usage.output_tokens
    last_usage["total"]  = response.usage.input_tokens + response.usage.output_tokens
    return response.content[0].text


if __name__ == "__main__":
    from datetime import datetime
    now = datetime.now()
    print(generate_plan(now.month, now.year))
    print(f"\n🔢 Tokens: {last_usage['total']:,}")
