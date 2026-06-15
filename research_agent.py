# ============================================================
#  Research Agent — Agent 01 🔍
#  วิจัยตลาด คู่แข่ง กลุ่มเป้าหมาย ด้วย Claude API
# ============================================================

import os
import anthropic
from dotenv import load_dotenv

# ── โหลด Environment Variables ──────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    raise ValueError(
        "❌ Missing ANTHROPIC_API_KEY in .env\n"
        "   ขอ Key ได้ที่: https://console.anthropic.com/"
    )

# ── ตั้งค่า Claude ───────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=API_KEY)
MODEL  = "claude-sonnet-4-6"

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """คุณเป็นนักวิจัยการตลาดอาวุโสของบริษัท Jet8 (Freight Forwarder นำเข้า-ส่งออกอาหารและยาในไทย)
หน้าที่ของคุณคือวิเคราะห์ตลาด คู่แข่ง เทรนด์ และกลุ่มเป้าหมาย

รูปแบบการตอบ:
1. **ภาพรวมตลาด** — สถานการณ์ปัจจุบัน ขนาดตลาด เทรนด์หลัก
2. **กลุ่มเป้าหมาย** — ใครคือลูกค้าหลัก ความต้องการ pain points
3. **คู่แข่งหลัก** — ใครเป็นคู่แข่ง จุดเด่น-จุดด้อย
4. **โอกาสสำหรับ Jet8** — ช่องว่างในตลาดที่เราเข้าไปได้
5. **ข้อแนะนำสำหรับการตลาด** — แนวทางที่ควรโฟกัส

ตอบเป็นภาษาไทย กระชับ ตรงประเด็น ใช้ bullet points ให้อ่านง่าย
"""

# เก็บจำนวนโทเคนของการเรียกครั้งล่าสุด
last_usage = {"input": 0, "output": 0, "total": 0}


def research(query: str) -> str:
    """รับหัวข้อวิจัย → เรียก Claude → คืนผลการวิเคราะห์"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": query}],
    )
    last_usage["input"]  = response.usage.input_tokens
    last_usage["output"] = response.usage.output_tokens
    last_usage["total"]  = response.usage.input_tokens + response.usage.output_tokens

    return response.content[0].text


if __name__ == "__main__":
    print("=" * 50)
    print("🔍  Research Agent 01 — นักวิจัยการตลาด")
    print("=" * 50)
    while True:
        q = input("📊 หัวข้อที่อยากวิจัย: ").strip()
        if q.lower() in ("exit", "quit", "ออก"):
            break
        if not q:
            continue
        print("\n🤔 กำลังวิจัย...\n")
        print(research(q))
        print(f"\n🔢 Tokens: {last_usage['total']:,}\n")
