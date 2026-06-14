# ============================================================
#  Content Agent ตัวแรกของคุณ 🤖✍️
#  ผู้ช่วย AI เขียนคอนเทนต์การตลาด — ใช้ Google Gemini (ฟรี)
#  อ่านคู่มือติดตั้งในไฟล์ README.md ก่อนรันนะครับ
# ============================================================

import os                          # ใช้ดึงค่าจากไฟล์ตั้งค่า (.env)
from google import genai           # ไลบรารีของ Google สำหรับคุยกับ Gemini
from dotenv import load_dotenv     # ตัวช่วยอ่านไฟล์ .env

# --- ขั้นที่ 1: โหลด API Key จากไฟล์ .env ---
load_dotenv()                              # อ่านไฟล์ .env เข้ามา
API_KEY = os.getenv("GEMINI_API_KEY")      # ดึงค่ากุญแจออกมา

if not API_KEY:
    print("❌ ไม่เจอ GEMINI_API_KEY")
    print("   เปิดไฟล์ .env แล้วใส่กุญแจของคุณก่อนนะครับ (ดูวิธีใน README.md)")
    raise SystemExit            # หยุดโปรแกรมอย่างสุภาพ

# --- ขั้นที่ 2: เชื่อมต่อกับ Gemini ---
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"      # รุ่นฟรี เร็วและคุ้ม (ถ้า error ลองเปลี่ยนเป็น "gemini-2.0-flash")

# --- ขั้นที่ 3: กำหนด "บุคลิก/หน้าที่" ของ Agent (System Prompt) ---
# ตรงนี้คือหัวใจ! เราบอกว่า Agent เป็นใคร ทำงานยังไง พูดภาษาอะไร
SYSTEM_PROMPT = """คุณคือนักการตลาดคอนเทนต์มืออาชีพของไทย
หน้าที่ของคุณคือช่วยเขียนแคปชั่นและโพสต์โซเชียลมีเดียที่ดึงดูด น่าสนใจ และกระตุ้นให้คนอยากซื้อ

กติกาการเขียน:
- เขียนเป็นภาษาไทยที่เป็นธรรมชาติ อ่านลื่น
- มี hook (ประโยคเปิด) ที่สะดุดตาในบรรทัดแรก
- ใส่อิโมจิพอประมาณ ให้ดูมีชีวิตชีวาแต่ไม่รก
- ปิดท้ายด้วย call-to-action (ชวนให้ทำอะไรต่อ เช่น ทักแชท สั่งเลย)
- แนะนำ hashtag ที่เกี่ยวข้อง 3-5 อัน
"""

# เก็บจำนวนโทเคนของการเรียกครั้งล่าสุด (ไฟล์อื่นมาอ่านค่านี้ได้)
last_usage = {"input": 0, "output": 0, "total": 0}

# --- ขั้นที่ 4: ฟังก์ชันหลัก — ส่งโจทย์ไปให้ Agent แล้วรับคำตอบ ---
def generate_content(user_request: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=user_request,
        config={"system_instruction": SYSTEM_PROMPT},   # ใส่บุคลิกที่ตั้งไว้
    )
    # ดึงจำนวนโทเคนที่ใช้ไปจากผลลัพธ์ (Gemini แนบมาให้เสมอ)
    u = response.usage_metadata
    last_usage["input"] = u.prompt_token_count or 0
    last_usage["output"] = u.candidates_token_count or 0
    last_usage["total"] = u.total_token_count or 0
    return response.text

# --- ขั้นที่ 5: ส่วนที่รันจริง — ถามผู้ใช้แล้วให้ Agent ทำงาน ---
if __name__ == "__main__":
    print("=" * 50)
    print("✍️  Content Agent — ผู้ช่วยเขียนคอนเทนต์การตลาด")
    print("=" * 50)
    print("ลองพิมพ์โจทย์ เช่น: เขียนแคปชั่นขายกาแฟดริปคั่วใหม่ สำหรับ Facebook")
    print("(พิมพ์ 'exit' เพื่อออก)\n")

    while True:
        user_request = input("📝 โจทย์ของคุณ: ").strip()

        if user_request.lower() in ("exit", "quit", "ออก"):
            print("👋 บายครับ แล้วเจอกันใหม่!")
            break

        if not user_request:
            continue        # ถ้าไม่พิมพ์อะไร ให้ถามใหม่

        print("\n🤔 กำลังคิด...\n")
        result = generate_content(user_request)
        print("-" * 50)
        print(result)
        print("-" * 50 + "\n")
