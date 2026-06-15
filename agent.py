# ============================================================
#  Content Agent — Agent 02 ✍️
#  เขียนคอนเทนต์การตลาด ด้วย Claude API
# ============================================================

import os
import anthropic
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
MODEL  = "claude-haiku-4-5-20251001"   # เร็วกว่า + ถูกกว่า Sonnet ~70%

# ── Slack (optional) ─────────────────────────────────────────────────────────
SLACK_TOKEN   = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_NEWS_CHANNEL_ID")

# ── System Prompts แยกตามประเภทคอนเทนต์ ─────────────────────────────────────

BASE_BRAND = """คุณคือนักการตลาดคอนเทนต์ของบริษัท Jet8 ผู้เชี่ยวชาญด้าน Freight Forwarder
นำเข้า-ส่งออกอาหารและยาระหว่างประเทศ กลุ่มลูกค้าหลักคือผู้ประกอบการ B2B
ในอุตสาหกรรม Food & Pharmaceutical ทั้งรายเล็กและรายใหญ่

จุดแข็งของ Jet8 ที่ต้องสื่อสาร:
- ประสบการณ์ด้านกฎระเบียบ อย. / FDA / ศุลกากร สำหรับสินค้าอาหารและยา
- เครือข่ายคู่ค้าทั่วโลก ดูแลเอกสารและ compliance ครบวงจร
- ทีมผู้เชี่ยวชาญที่ติดตามสถานะสินค้าได้ตลอด 24/7
"""

PROMPTS = {
    "facebook": BASE_BRAND + """
สไตล์การเขียน: Facebook สำหรับกลุ่มธุรกิจ (B2B)
- Hook ประโยคแรกดึงดูดใจ อาจเป็นคำถาม ตัวเลข หรือ pain point
- เนื้อหา 3-5 ประโยค กระชับ ให้คุณค่า
- อิโมจิ 3-5 ตัว วางตำแหน่งให้เหมาะ ไม่รก
- Call-to-action ปิดท้าย (เช่น "ปรึกษาทีมงาน Jet8 ได้เลย")
- Hashtag 3-5 อัน เช่น #Jet8 #FreightForwarder #นำเข้าส่งออก
""",

    "linkedin": BASE_BRAND + """
สไตล์การเขียน: LinkedIn สำหรับมืออาชีพและผู้บริหาร B2B
- เปิดด้วย insight หรือ pain point ของอุตสาหกรรม
- เนื้อหา 4-6 ประโยค เป็นทางการ น่าเชื่อถือ แสดงความเชี่ยวชาญ
- ไม่ใช้อิโมจิหรือใช้น้อยมาก (1-2 ตัว)
- จบด้วย thought leadership หรือ CTA แบบสุภาพ
- Hashtag 3-4 อัน เน้นอุตสาหกรรม
""",

    "website": BASE_BRAND + """
สไตล์การเขียน: คอนเทนต์สำหรับหน้าเว็บไซต์
- ภาษาทางการ กระชับ ชัดเจน SEO-friendly
- มี Headline หลัก (H1) และ Subheadline (H2) ที่ชัดเจน
- เนื้อหาอธิบายบริการ จุดแข็ง และประโยชน์ที่ลูกค้าได้รับ
- ใช้ bullet point หรือ numbered list เพื่อให้อ่านง่าย
- ปิดท้ายด้วย CTA ที่ชัดเจน เช่น "ติดต่อขอใบเสนอราคา"
- ไม่ใช้อิโมจิ ไม่ใช้ hashtag
""",
}

CONTENT_TYPES = {
    "1": ("facebook",  "Facebook Post"),
    "2": ("linkedin",  "LinkedIn Post"),
    "3": ("website",   "คอนเทนต์เว็บไซต์"),
}

# เก็บจำนวนโทเคนของการเรียกครั้งล่าสุด
last_usage = {"input": 0, "output": 0, "total": 0}


def send_to_slack(message: str) -> bool:
    """ส่งข้อความไป Slack (ข้ามเงียบๆ ถ้าไม่มี token)"""
    if not SLACK_TOKEN or not SLACK_CHANNEL:
        return False
    try:
        slack = WebClient(token=SLACK_TOKEN)
        slack.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        return True
    except SlackApiError as e:
        print(f"⚠️ Slack error: {e.response['error']}")
        return False


def generate_content(
    user_request: str,
    content_type: str = "facebook",
    post_to_slack: bool = False,
) -> str:
    """รับโจทย์ + ประเภทคอนเทนต์ → เรียก Claude → คืนค่า Content

    Parameters:
        user_request  — หัวข้อหรือโจทย์ที่ต้องการ
        content_type  — "facebook" | "linkedin" | "website"
        post_to_slack — ส่งผลลัพธ์ไป Slack ด้วยหรือไม่
    """
    system = PROMPTS.get(content_type, PROMPTS["facebook"])

    # max_tokens แยกตามประเภท: โพสต์โซเชียลสั้นกว่าเว็บไซต์
    max_tok = {"facebook": 600, "linkedin": 700, "website": 1200}.get(content_type, 700)

    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tok,
        system=[{"type": "text", "text": system,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_request}],
    )
    last_usage["input"]  = response.usage.input_tokens
    last_usage["output"] = response.usage.output_tokens
    last_usage["total"]  = response.usage.input_tokens + response.usage.output_tokens

    result = response.content[0].text

    if post_to_slack:
        send_to_slack(result)

    return result


if __name__ == "__main__":
    print("=" * 55)
    print("✍️  Content Agent 02 — ผู้ช่วยเขียนคอนเทนต์ Jet8")
    print("=" * 55)
    slack_status = "🟢 Slack เชื่อมต่อแล้ว" if (SLACK_TOKEN and SLACK_CHANNEL) else "⚪ Slack ยังไม่ตั้งค่า"
    print(f"   {slack_status}\n")

    while True:
        # เลือกประเภทคอนเทนต์
        print("เลือกประเภทคอนเทนต์:")
        for key, (_, label) in CONTENT_TYPES.items():
            print(f"  {key}. {label}")
        print("  0. ออกจากโปรแกรม")

        choice = input("\nเลือก (1/2/3): ").strip()
        if choice == "0":
            print("👋 บายครับ!")
            break
        if choice not in CONTENT_TYPES:
            print("⚠️  กรุณาเลือก 0-3\n")
            continue

        ctype, clabel = CONTENT_TYPES[choice]
        req = input(f"\n📝 โจทย์สำหรับ {clabel}: ").strip()
        if not req:
            continue

        print("\n🤔 กำลังเขียน...\n")
        result = generate_content(req, content_type=ctype, post_to_slack=True)
        print("-" * 55)
        print(result)
        print("-" * 55)
        print(f"🔢 Tokens: {last_usage['total']:,}\n")
