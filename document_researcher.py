# ============================================================
#  Document Researcher — ดึงงาน/เอกสารล่าสุดจาก ClickUp
#  แยก 3 ช่องทาง: ศุลกากร | อย./FDA | กรมพาณิชย์
#
#  ต้องตั้งค่าใน .env หรือ Streamlit Secrets:
#    CLICKUP_TOKEN=pk_xxxxxxxxxxxxxxxx
#    CUSTOMS_LIST_ID=xxxxxxxxx
#    FDA_LIST_ID=xxxxxxxxx
#    MOC_LIST_ID=xxxxxxxxx
# ============================================================

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.clickup.com/api/v2"

# label และ env key ของแต่ละช่องทาง (ไม่ cache ค่า — อ่าน os.environ ตอนใช้)
CHANNEL_DEFS = {
    "customs": ("🛃 ศุลกากร",    "CUSTOMS_LIST_ID"),
    "fda":     ("💊 อย./FDA",    "FDA_LIST_ID"),
    "moc":     ("🏛️ กรมพาณิชย์", "MOC_LIST_ID"),
}


# ── helpers อ่านค่าแบบ dynamic (ไม่ cache ตอน import) ───────────────────────

def _token() -> str:
    return os.getenv("CLICKUP_TOKEN", "")

def _headers() -> dict:
    return {"Authorization": _token(), "Content-Type": "application/json"}

def get_channels() -> dict:
    """อ่าน channel config ทุกครั้งที่เรียก — รองรับ Streamlit secrets"""
    return {
        key: {"label": label, "list_id": os.getenv(env_key, "")}
        for key, (label, env_key) in CHANNEL_DEFS.items()
    }


# ── Public API ────────────────────────────────────────────────────────────────

def is_configured() -> bool:
    """ตรวจว่าตั้งค่าครบหรือยัง (token + อย่างน้อย 1 list)"""
    channels = get_channels()
    has_list = any(ch["list_id"] for ch in channels.values())
    return bool(_token() and has_list)


def fetch_by_channel(channel_key: str, days: int = 30, max_results: int = 15) -> list:
    """ดึง tasks จาก List ของช่องทางที่ระบุ"""
    ch = get_channels().get(channel_key)
    if not ch or not ch["list_id"]:
        return [{"error": f"ยังไม่ตั้งค่า List ID ของ {channel_key} ใน .env / Secrets"}]

    since_ms = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    try:
        resp = requests.get(
            f"{BASE_URL}/list/{ch['list_id']}/task",
            headers=_headers(),
            params={"date_updated_gt": since_ms, "order_by": "updated",
                    "reverse": "true", "subtasks": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        tasks = resp.json().get("tasks", [])
        return [_format_task(t, ch["label"]) for t in tasks[:max_results]]

    except requests.HTTPError as e:
        return [{"error": f"ClickUp {e.response.status_code}: {e.response.text[:200]}"}]
    except Exception as e:
        return [{"error": str(e)}]


def fetch_all_channels(days: int = 30, max_per_channel: int = 10) -> dict:
    """ดึง tasks จากทั้ง 3 ช่องทางพร้อมกัน → {"customs": [...], "fda": [...], "moc": [...]}"""
    return {key: fetch_by_channel(key, days=days, max_results=max_per_channel)
            for key in CHANNEL_DEFS}


def fetch_recent_tasks(days: int = 30, max_results: int = 30) -> list:
    """ดึงรวมทุกช่องทาง (backward-compat)"""
    combined = []
    for tasks in fetch_all_channels(days=days, max_per_channel=max_results // 3 or 10).values():
        combined.extend(tasks)
    return combined


def search_in_channel(channel_key: str, query: str, max_results: int = 10) -> list:
    """ค้นหา tasks ใน List ของช่องทางที่ระบุ"""
    ch = get_channels().get(channel_key)
    if not ch or not ch["list_id"]:
        return [{"error": f"ยังไม่ตั้งค่า List ID ของ {channel_key}"}]
    try:
        resp = requests.get(
            f"{BASE_URL}/list/{ch['list_id']}/task",
            headers=_headers(),
            params={"query": query, "subtasks": "true"},
            timeout=15,
        )
        resp.raise_for_status()
        tasks = resp.json().get("tasks", [])
        return [_format_task(t, ch["label"]) for t in tasks[:max_results]]
    except Exception as e:
        return [{"error": str(e)}]


def _format_task(task: dict, channel_label: str = "—") -> dict:
    return {
        "id":            task.get("id", ""),
        "name":          task.get("name", "—"),
        "status":        task.get("status", {}).get("status", "—"),
        "url":           task.get("url", ""),
        "updated_at":    _ms_to_date(task.get("date_updated")),
        "channel_label": channel_label,
    }


def _ms_to_date(ms_str) -> str:
    if not ms_str:
        return "—"
    try:
        return datetime.fromtimestamp(int(ms_str) / 1000).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "—"


if __name__ == "__main__":
    if not is_configured():
        print("⚠️  ยังไม่ตั้งค่า ClickUp ใน .env")
        print("   เพิ่ม CLICKUP_TOKEN, CUSTOMS_LIST_ID, FDA_LIST_ID, MOC_LIST_ID")
    else:
        print("🔍 ดึง tasks จากทุกช่องทาง (30 วันล่าสุด)...\n")
        for key, ch in get_channels().items():
            print(f"{'='*40}\n{ch['label']}")
            for t in fetch_by_channel(key, days=30):
                if "error" in t:
                    print(f"  ❌ {t['error']}")
                else:
                    print(f"  📄 {t['name']} — {t['status']} ({t['updated_at']})")
        print()
