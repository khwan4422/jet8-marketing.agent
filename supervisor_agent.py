# ============================================================
#  Supervisor Agent — Agent 00 👑
#  ตรวจสอบคุณภาพ output ก่อนส่งให้ user ด้วย Claude Opus
# ============================================================

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("❌ Missing ANTHROPIC_API_KEY in .env")

client = anthropic.Anthropic(api_key=API_KEY)
MODEL  = "claude-sonnet-4-6"   # ลดจาก Opus → Sonnet ประหยัด ~80%

SYSTEM_PROMPT = """คุณเป็น Marketing Director อาวุโสของบริษัท Jet8 (Freight Forwarder นำเข้า-ส่งออกอาหารและยาในไทย)
หน้าที่ของคุณคือตรวจสอบคุณภาพ output ที่ทีม AI เขียนขึ้นก่อนนำไปใช้จริง

เกณฑ์การประเมิน:
1. ความถูกต้อง — ข้อมูลถูกต้อง ไม่โอ้อวดเกินจริง
2. ความเหมาะสมกับแบรนด์ — ภาษามืออาชีพ น่าเชื่อถือ สอดคล้องกับธุรกิจ B2B
3. ความชัดเจน — อ่านเข้าใจง่าย มี call-to-action ที่ชัดเจน
4. ความเหมาะสมกับกลุ่มเป้าหมาย — ผู้นำเข้า-ส่งออก เจ้าของธุรกิจ Food & Pharma
5. ประสิทธิภาพในการสื่อสาร — ดึงดูดความสนใจ กระตุ้น action

ตอบเป็นภาษาไทย กระชับ ตรงประเด็น ในรูปแบบที่กำหนด
"""

last_usage = {"input": 0, "output": 0, "total": 0}


def review(content: str, content_type: str = "content") -> str:
    """
    รับ content จาก agent ใดก็ได้ → ตรวจสอบคุณภาพ → คืน QC Report

    Parameters:
        content      — ข้อความที่ต้องการตรวจ
        content_type — ประเภท: "content", "report", "news_analysis"
    """
    context_map = {
        "content":       "โพสต์โซเชียลมีเดีย / คอนเทนต์การตลาด",
        "report":        "รายงานการตลาดสำหรับทีมภายใน",
        "news_analysis": "บทวิเคราะห์ข่าวสัปดาห์สำหรับทีมธุรกิจ",
    }
    context_label = context_map.get(content_type, "content")

    prompt = f"""กรุณาตรวจสอบ{context_label}ต่อไปนี้:

---
{content}
---

กรุณาให้ผล QC ในรูปแบบนี้:

## ⭐ คะแนนรวม: [X.X/10]

## ✅ จุดเด่น
(2-3 ข้อที่ดีและควรคงไว้)

## ⚠️ จุดที่ควรปรับปรุง
(2-3 ข้อที่ควรแก้ไข พร้อมตัวอย่างที่แนะนำ)

## 🎯 สรุปคำแนะนำ
(1-2 ประโยค บอกว่า "ใช้ได้เลย" หรือ "ควรปรับก่อน" และเหตุผลสั้นๆ)
"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=700,
            system=[{"type": "text", "text": SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
        )
        last_usage["input"]  = response.usage.input_tokens
        last_usage["output"] = response.usage.output_tokens
        last_usage["total"]  = response.usage.input_tokens + response.usage.output_tokens
        return response.content[0].text
    except Exception as e:
        return f"❌ Supervisor error: {e}"


if __name__ == "__main__":
    sample = "Jet8 พร้อมให้บริการนำเข้า-ส่งออกสินค้าอาหารและยา ครบวงจร ติดต่อเราวันนี้!"
    print(review(sample, "content"))
    print(f"\n🔢 Tokens: {last_usage['total']:,}")
