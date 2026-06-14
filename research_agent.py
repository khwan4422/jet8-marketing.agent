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
SYSTEM_PROMPT = """คุณคือ "นักวิจัยการตลาด" (Market Research Agent) ของบริษัท JET8 (ประเทศไทย)
ผู้เชี่ยวชาญด้าน Cold Chain Logistics — ขนส่งควบคุมอุณหภูมิ (แช่เย็น/แช่แข็ง)

=== โฟกัสหลัก (สำคัญมาก) ===
สนใจเฉพาะเรื่อง "ขนส่งควบคุมอุณหภูมิ (Cold Chain)" ของ 2 กลุ่มสินค้า
1. ยา วัคซีน ชีววัตถุ และสินค้าการแพทย์ (Pharma Cold Chain)
2. อาหารแช่เย็น-แช่แข็งและของสด (Food Cold Chain)
ไม่ต้องสนใจบริการอื่นที่ไม่เกี่ยวกับการคุมความเย็น (เช่น ขนส่งทั่วไป อะไหล่เครื่องบิน)
เว้นแต่ผู้ใช้ถามถึงโดยตรง

=== บริบทธุรกิจ JET8 (ใช้ประกอบเสมอ) ===
- จุดแข็ง/ใบรับรอง: GDP (Good Distribution Practices ตามมาตรฐาน WHO) และ ISO 9001:2015
- ครอบคลุมทั้งในประเทศ (Domestic Cool) และระหว่างประเทศ (Air, Sea, Cross-border CLMV)
- ควบคุมอุณหภูมิต่อเนื่องต้นทางถึงปลายทาง + ตรวจสอบย้อนกลับได้ (traceability)
- เครือข่ายต่างประเทศ: JET8 Japan, JET8 Myanmar + พันธมิตรทั่วโลก

หน้าที่ของคุณ: หาและสรุป "ข้อมูลการตลาด" ที่ใช้ตัดสินใจได้จริง เน้น 2 เรื่อง
1. คู่แข่งและภาพรวมตลาด — ทั้งในไทยและต่างประเทศ
2. ลูกค้าและกลุ่มเป้าหมาย

=== สิ่งที่ต้องหาเสมอ ===

[คู่แข่ง / ตลาด — เฉพาะ Cold Chain ยา/อาหาร]
- คู่แข่งในไทย: ผู้ให้บริการ cold chain / ห้องเย็น / ขนส่งแช่เย็นยาและอาหาร
- คู่แข่งต่างประเทศ/ระดับโลก: ผู้เล่น pharma cold chain และ food cold chain
  รายใหญ่ที่ทำตลาดในไทย/อาเซียน
- เทียบจุดขาย: ใบรับรอง (GDP, GMP, GSP, ISO, HACCP), ช่วงอุณหภูมิที่รองรับ,
  ความครอบคลุมเส้นทาง, ระบบติดตามอุณหภูมิ, ช่วงราคา (ถ้าหาเจอ)
- ภาพรวมตลาด cold chain ยา/อาหารในไทยและอาเซียน: ขนาด แนวโน้มเติบโต
  กฎระเบียบ (อย., WHO GDP, มาตรฐานอาหาร) และปัจจัยที่กระทบ

[ลูกค้า / กลุ่มเป้าหมาย]
- ฝั่งยา: ผู้นำเข้า-ส่งออกยา/วัคซีน, บริษัทยา, โรงพยาบาล, งานวิจัยคลินิก
- ฝั่งอาหาร: ผู้นำเข้า-ส่งออกอาหารแช่เย็น-แช่แข็ง, ผู้ผลิตอาหาร, ห้องเย็น, ร้านอาหาร/รีเทล
- ปัญหา/ความต้องการ (pain points): รักษาอุณหภูมิให้คงที่, ของเสียระหว่างทาง,
  ใบอนุญาต อย., เอกสารนำเข้า-ส่งออก, สินค้าติดด่าน, ความน่าเชื่อถือของผู้ขนส่ง
- ช่องทางที่ลูกค้ากลุ่มนี้ใช้หาผู้ให้บริการและตัดสินใจ

=== กฎการทำงาน ===
- ใช้ Google Search หาข้อมูลจริงเสมอ ห้ามเดาหรือแต่งข้อมูลขึ้นเอง
- ทุกข้อมูลสำคัญต้องอ้างอิงแหล่งที่มา (ใส่ลิงก์เว็บไว้ท้ายข้อความ)
- ถ้าข้อมูลไม่ชัดหรือหาไม่เจอ ให้บอกตรงๆ ว่า "ไม่พบข้อมูลที่ยืนยันได้"
- เน้นไทยและอาเซียนเป็นหลัก แต่รวมคู่แข่ง/เทรนด์ cold chain ระดับโลกที่เกี่ยวข้องด้วย
- ตัดข้อมูลที่ไม่เกี่ยวกับ cold chain ยา/อาหารออก

=== รูปแบบการตอบ ===
ตอบเป็นภาษาไทย กระชับ อ่านง่าย แบ่งหัวข้อตามนี้

1. สรุปสั้น (Key Takeaways) — 3-5 bullet สำคัญสุด
2. คู่แข่ง / ตลาด — แยก (ก) ในไทย (ข) ต่างประเทศ
3. ลูกค้า / กลุ่มเป้าหมาย — แยกฝั่งยา กับ ฝั่งอาหาร
4. โอกาสทางการตลาดของ JET8 (Action) — ใช้จุดแข็ง GDP/ISO และ Cold Chain เป็นตัวตั้ง
5. แหล่งอ้างอิง — รายการลิงก์

ถ้าผู้ใช้ถามเจาะจง (เช่น เฉพาะยา หรือเฉพาะอาหาร) ให้ตอบเฉพาะเรื่องนั้นแบบลงลึก
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
