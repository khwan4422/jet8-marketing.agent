# ============================================================
#  Research Agent — Agent ตัวที่ 2 ของทีม 🔍
#  ค้นข้อมูลจากเว็บจริง (Google Search) แล้วสรุปให้ + เซฟเป็นไฟล์
#  ใช้ Google Gemini (ฟรี) — ใช้ไฟล์ .env เดียวกับ agent.py ได้เลย
# ============================================================

import os
from datetime import datetime          # ใช้ตั้งชื่อไฟล์ตามวันเวลา
from google import genai
from google.genai import types         # ใช้เปิดเครื่องมือค้นเว็บ
from dotenv import load_dotenv

# --- ขั้นที่ 1: โหลดกุญแจ (ใช้ตัวเดียวกับ Content Agent) ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ ไม่เจอ GEMINI_API_KEY — เช็คไฟล์ .env ก่อนนะครับ")
    raise SystemExit

# --- ขั้นที่ 2: เชื่อมต่อ Gemini ---
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"

# --- ขั้นที่ 3: บุคลิก/หน้าที่ของ Research Agent ---
SYSTEM_PROMPT = """คุณคือนักวิจัยตลาด (Market Researcher) มืออาชีพ
หน้าที่ของคุณคือค้นหาข้อมูลล่าสุดจากอินเทอร์เน็ต แล้วสรุปให้นักการตลาดเข้าใจง่าย

กติกาการสรุป:
- ตอบเป็นภาษาไทย กระชับ ตรงประเด็น
- จัดเป็นหัวข้อชัดเจน เช่น ภาพรวม / เทรนด์สำคัญ / คู่แข่ง / โอกาสทางการตลาด
- อ้างอิงตัวเลขหรือข้อเท็จจริงเมื่อเจอ และบอกที่มาคร่าวๆ
- ปิดท้ายด้วยข้อเสนอแนะเชิงปฏิบัติ 3 ข้อ ที่เอาไปใช้ทำการตลาดต่อได้
"""

# --- ขั้นที่ 4: เปิด "เครื่องมือค้นเว็บ" ให้ Agent ---
# นี่คือ tool แรกของเรา! ทำให้ Agent ไม่ได้เดาจากความจำ แต่ค้นข้อมูลจริง
search_tool = types.Tool(google_search=types.GoogleSearch())

# เก็บจำนวนโทเคนของการเรียกครั้งล่าสุด (ไฟล์อื่นมาอ่านค่านี้ได้)
last_usage = {"input": 0, "output": 0, "total": 0}

# --- ขั้นที่ 5: ฟังก์ชันค้นคว้า ---
def research(topic: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=topic,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[search_tool],          # ใส่เครื่องมือค้นเว็บเข้าไป
        ),
    )
    # ดึงจำนวนโทเคนที่ใช้ไป
    u = response.usage_metadata
    last_usage["input"] = u.prompt_token_count or 0
    last_usage["output"] = u.candidates_token_count or 0
    last_usage["total"] = u.total_token_count or 0
    return response.text

# --- ขั้นที่ 6: tool ตัวที่สอง — เซฟผลลัพธ์เป็นไฟล์ ---
def save_to_file(topic: str, content: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe = "".join(c for c in topic[:30] if c.isalnum() or c in " ก-๙").strip()
    filename = f"research_{safe}_{stamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# ผลการค้นคว้า: {topic}\n\n")
        f.write(f"_สร้างเมื่อ {datetime.now().strftime('%d/%m/%Y %H:%M')}_\n\n")
        f.write(content)
    return filename

# --- ขั้นที่ 7: ส่วนที่รันจริง ---
if __name__ == "__main__":
    print("=" * 50)
    print("🔍  Research Agent — ผู้ช่วยวิจัยตลาด")
    print("=" * 50)
    print("ลองพิมพ์หัวข้อ เช่น: เทรนด์การตลาดกาแฟพิเศษในไทยปี 2026")
    print("(พิมพ์ 'exit' เพื่อออก)\n")

    while True:
        topic = input("🔎 อยากรู้เรื่องอะไร: ").strip()

        if topic.lower() in ("exit", "quit", "ออก"):
            print("👋 บายครับ!")
            break
        if not topic:
            continue

        print("\n🌐 กำลังค้นเว็บและสรุป...\n")
        result = research(topic)
        print("-" * 50)
        print(result)
        print("-" * 50)

        # ถามว่าจะเซฟไหม
        ans = input("\n💾 เซฟผลเป็นไฟล์ไหม? (y/n): ").strip().lower()
        if ans in ("y", "yes", "ใช่"):
            fname = save_to_file(topic, result)
            print(f"✅ เซฟแล้ว: {fname}\n")
        else:
            print()
