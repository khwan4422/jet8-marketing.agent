# ============================================================
#  Event Tracker — จัดการอีเวนต์ที่ทีมสนใจจะเข้าร่วม
#  บันทึกลง data/events.json พร้อมนับถอยหลัง
#  (Google Calendar integration: coming soon)
# ============================================================

import os
import json
from datetime import datetime, date

EVENTS_FILE = "data/events.json"
os.makedirs("data", exist_ok=True)


# ── CRUD ─────────────────────────────────────────────────────────────────────

def load_events() -> list:
    """โหลดอีเวนต์ทั้งหมดจากไฟล์"""
    if not os.path.exists(EVENTS_FILE):
        return []
    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events: list):
    """บันทึกอีเวนต์ทั้งหมดลงไฟล์"""
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def add_event(
    name: str,
    start_date: str,
    end_date: str,
    purpose: str,
    channel: str = "",
    notes: str = "",
) -> dict:
    """เพิ่มอีเวนต์ใหม่

    Parameters:
        name       — ชื่ออีเวนต์
        start_date — วันเริ่มต้น (YYYY-MM-DD)
        end_date   — วันสิ้นสุด (YYYY-MM-DD)
        purpose    — เป้าประสงค์การไป
        channel    — ช่องทางที่จะโพสต์ (Facebook/LinkedIn/เว็บไซต์)
        notes      — หมายเหตุเพิ่มเติม
    """
    events = load_events()
    # หา ID สูงสุดที่มีอยู่แล้วบวก 1 (ป้องกัน ID ซ้ำหลังลบ)
    next_id = max((e.get("id", 0) for e in events), default=0) + 1

    new_event = {
        "id":         next_id,
        "name":       name.strip(),
        "start_date": start_date,
        "end_date":   end_date,
        "purpose":    purpose.strip(),
        "channel":    channel,
        "notes":      notes.strip(),
        "created_at": datetime.now().isoformat(),
    }
    events.append(new_event)
    save_events(events)
    return new_event


def delete_event(event_id: int):
    """ลบอีเวนต์ตาม ID"""
    events = load_events()
    events = [e for e in events if e.get("id") != event_id]
    save_events(events)


# ── Query ─────────────────────────────────────────────────────────────────────

def get_countdown(start_date_str: str) -> int:
    """คืนจำนวนวันที่เหลือถึงอีเวนต์ (ติดลบถ้าผ่านมาแล้ว)"""
    try:
        start = date.fromisoformat(start_date_str)
        return (start - date.today()).days
    except Exception:
        return 0


def get_upcoming_events(include_past_days: int = 7) -> list:
    """คืนอีเวนต์ที่ยังไม่ผ่านมา (และที่เพิ่งผ่านมาไม่เกิน X วัน)
    เรียงตามวันที่ใกล้สุดก่อน

    Parameters:
        include_past_days — รวมอีเวนต์ที่ผ่านไปแล้วกี่วัน (default 7)
    """
    events = load_events()
    result = []
    for e in events:
        days = get_countdown(e.get("start_date", ""))
        if days >= -include_past_days:
            result.append({**e, "days_until": days})
    return sorted(result, key=lambda x: x["days_until"])


def get_events_in_month(month: int, year: int) -> list:
    """ดึงอีเวนต์ทั้งหมดในเดือนที่ระบุ (สำหรับ Planner)"""
    events = load_events()
    result = []
    for e in events:
        try:
            start = date.fromisoformat(e["start_date"])
            if start.month == month and start.year == year:
                result.append(e)
        except Exception:
            pass
    return result


# ── Countdown label ───────────────────────────────────────────────────────────

def countdown_label(days: int) -> str:
    """แปลงจำนวนวันเป็นข้อความสำหรับแสดงผล"""
    if days < 0:
        return f"ผ่านมาแล้ว {abs(days)} วัน"
    elif days == 0:
        return "🔴 วันนี้!"
    elif days == 1:
        return "🟠 พรุ่งนี้!"
    elif days <= 7:
        return f"🟡 อีก {days} วัน"
    elif days <= 30:
        return f"🟢 อีก {days} วัน"
    else:
        return f"🔵 อีก {days} วัน"


if __name__ == "__main__":
    # ทดสอบเพิ่มอีเวนต์
    test = add_event(
        name="THAIFEX 2026",
        start_date="2026-05-27",
        end_date="2026-05-31",
        purpose="สร้าง connection กับผู้นำเข้าอาหาร หาลูกค้าใหม่",
        channel="LinkedIn, Facebook",
        notes="ตรวจสอบ booth ล่วงหน้า",
    )
    print(f"✅ เพิ่มอีเวนต์: {test['name']}")

    upcoming = get_upcoming_events()
    print(f"\n📅 อีเวนต์ที่กำลังจะมา ({len(upcoming)} รายการ):")
    for e in upcoming:
        print(f"  {countdown_label(e['days_until'])} — {e['name']} ({e['start_date']})")
