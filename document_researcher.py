# ============================================================
#  Document Researcher — ดึงงาน/เอกสารล่าสุดจาก ClickUp
#  ให้ทีมคอนเทนต์รู้ว่ามีอัปเดตอะไรบ้างที่ต้องสื่อสาร
#
#  ต้องตั้งค่าใน .env:
#    CLICKUP_API_TOKEN=pk_xxxxxxxxxxxxxxxx
#    CLICKUP_TEAM_ID=xxxxxxxxx   (Workspace/Team ID)
# ============================================================

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CLICKUP_TOKEN   = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
BASE_URL        = "https://api.clickup.com/api/v2"

HEADERS = {
    "Authorization": CLICKUP_TOKEN or "",
    "Content-Type": "application/json",
}


def is_configured() -> bool:
    """ตรวจว่าตั้งค่า ClickUp ครบหรือยัง"""
    return bool(CLICKUP_TOKEN and CLICKUP_TEAM_ID)


def fetch_recent_tasks(days: int = 30, max_results: int = 20) -> list:
    """ดึง tasks ที่อัปเดตใน X วันที่ผ่านมา

    Returns:
        list ของ dict: {name, status, url, updated_at, list_name}
        หรือ [{"error": "..."}] ถ้าเกิดปัญหา
    """
    if not is_configured():
        return [{"error": "ยังไม่ตั้งค่า CLICKUP_API_TOKEN และ CLICKUP_TEAM_ID ใน .env"}]

    since_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

    try:
        resp = requests.get(
            f"{BASE_URL}/team/{CLICKUP_TEAM_ID}/task",
            headers=HEADERS,
            params={
                "date_updated_gt": since_ms,
                "order_by": "updated",
                "reverse": "true",
                "subtasks": "true",
                "page": 0,
            },
            timeout=15,
        )
        resp.raise_for_status()
        tasks = resp.json().get("tasks", [])
        return [_format_task(t) for t in tasks[:max_results]]

    except requests.HTTPError as e:
        return [{"error": f"ClickUp API Error {e.response.status_code}: {e.response.text[:200]}"}]
    except Exception as e:
        return [{"error": str(e)}]


def search_tasks(query: str, max_results: int = 15) -> list:
    """ค้นหา tasks ตาม keyword

    Parameters:
        query       — คำค้นหา เช่น "อย." หรือ "import regulation"
        max_results — จำนวนผลลัพธ์สูงสุด
    """
    if not is_configured():
        return [{"error": "ยังไม่ตั้งค่า ClickUp ใน .env"}]

    try:
        resp = requests.get(
            f"{BASE_URL}/team/{CLICKUP_TEAM_ID}/task",
            headers=HEADERS,
            params={"query": query, "subtasks": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        tasks = resp.json().get("tasks", [])
        return [_format_task(t) for t in tasks[:max_results]]

    except Exception as e:
        return [{"error": str(e)}]


def _format_task(task: dict) -> dict:
    """แปลง task object จาก ClickUp ให้เป็น dict ที่ใช้งานง่าย"""
    return {
        "id":         task.get("id", ""),
        "name":       task.get("name", "—"),
        "status":     task.get("status", {}).get("status", "—"),
        "url":        task.get("url", ""),
        "updated_at": _ms_to_date(task.get("date_updated")),
        "list_name":  task.get("list", {}).get("name", "—"),
    }


def _ms_to_date(ms_str) -> str:
    """แปลง millisecond timestamp เป็นวันที่อ่านได้"""
    if not ms_str:
        return "—"
    try:
        return datetime.fromtimestamp(int(ms_str) / 1000).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


if __name__ == "__main__":
    if not is_configured():
        print("⚠️  ยังไม่ตั้งค่า ClickUp ใน .env")
        print("   เพิ่ม CLICKUP_API_TOKEN และ CLICKUP_TEAM_ID แล้วลองใหม่")
    else:
        print("🔍 ดึง tasks ล่าสุด 30 วัน...")
        tasks = fetch_recent_tasks(days=30)
        for t in tasks:
            if "error" in t:
                print(f"❌ {t['error']}")
            else:
                print(f"📄 [{t['list_name']}] {t['name']} — {t['status']} ({t['updated_at']})")
