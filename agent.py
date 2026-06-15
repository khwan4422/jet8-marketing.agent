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
MODEL  = "claude-sonnet-4-6"    # ประหยัดกว่า: claude-haiku-4-5-20251001

# ── Slack (optional) ─────────────────────────────────────────────────────────
SLACK_TOKEN   = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID") or os.getenv("SLACK_NEWS_CHANNEL_ID")

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """คุณคือนักการตลาดคอนเทนต์มืออาชีพของบริษัท Jet8 (Freight Forwarder นำเข้า-ส่งออกอาหารและยาในไทย)
หน้าที่ของคุณคือช่วยเขียนคอนเทนต์สำหรับโซเชียลมีเดียและเว็บไซต์ที่ดึงดูด น่าเชื่อถือ และกระตุ้นให้กลุ่มเป้าหมายสนใจ

กติกาการเขียน:
- เขียนเป็นภาษาไทยที่เป็นธรรมชาติ อ่านลื่น มืออาชีพ
- มี hook (ประโยคเปิด) ที่สะดุดตาในบรรทัดแรก
- เน้นความเชี่ยวชาญด้านนำเข้า-ส่งออก โดยเฉพาะอาหารและยา
- ใส่อิโมจิพอประมาณ (ไม่เกิน 5 ตัว) ให้ดูมีชีวิตชีวา
- ปิดท้ายด้วย call-to-action ที่ชัดเจน
- แนะนำ hashtag ที่เกี่ยวข้อง 3-5 อัน
"""

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


def generate_content(user_request: str, post_to_slack: bool = False) -> str:
    """รับโจทย์ → เรียก Claude → คืนค่า Content"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
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
    print("=" * 50)
    print("✍️  Content Agent 02 — ผู้ช่วยเขียนคอนเทนต์")
    print("=" * 50)
    while True:
        req = input("📝 โจทย์: ").strip()
        if req.lower() in ("exit", "quit", "ออก"):
            break
        if not req:
            continue
        print("\n🤔 กำลังคิด...\n")
        print(generate_content(req))
        print(f"\n🔢 Tokens: {last_usage['total']:,}\n")
