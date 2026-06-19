# ============================================================
#  MARKETING OPS v2.0 — Jet8 Social Media Team Dashboard
#  รันด้วย:  streamlit run app.py
#  6 แท็บ: Planner | Research | Documents | Events | Content | Review
# ============================================================

import os
import json
import base64
from datetime import datetime, timezone, timedelta
import streamlit as st
import requests as _requests
from dotenv import load_dotenv

load_dotenv()

TH = timezone(timedelta(hours=7))

# ── ตั้งค่าหน้า ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MARKETING OPS v2.0", page_icon="🟡", layout="wide")

# ── โหลด Secrets (สำหรับ deploy บน Streamlit Cloud) ─────────────────────────
for key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "SLACK_BOT_TOKEN",
            "SLACK_CHANNEL_ID", "SLACK_NEWS_CHANNEL_ID",
            "CLICKUP_TOKEN", "CUSTOMS_LIST_ID", "FDA_LIST_ID", "MOC_LIST_ID",
            "APP_PASSWORD"]:
    try:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
    except Exception:
        pass

# ── Import Agents (graceful — ไม่ crash ถ้าไฟล์หาย) ──────────────────────────
try:
    import agent as content_agent
    CONTENT_OK = True
except Exception:
    CONTENT_OK = False

try:
    import supervisor_agent
    REVIEW_OK = True
except Exception:
    REVIEW_OK = False

try:
    import news_monitor
    NEWS_OK = True
except Exception:
    NEWS_OK = False

try:
    import marketing_researcher
    RESEARCH_OK = True
except Exception:
    RESEARCH_OK = False

try:
    import planner as planner_agent
    PLANNER_OK = True
except Exception:
    PLANNER_OK = False

try:
    import document_researcher
    DOC_OK = True
except Exception:
    DOC_OK = False

try:
    import event_tracker
    EVENT_OK = True
except Exception:
    EVENT_OK = False

try:
    import trend_summarizer
    TREND_OK = True
except Exception:
    TREND_OK = False

# ── CSS — ธีมนีออน Retro + Pac-Man 🟡 ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Kanit:wght@400;600&display=swap');

.stApp {
  background:
    linear-gradient(rgba(8,12,40,.97), rgba(8,12,40,.97)),
    repeating-linear-gradient(0deg,  #0b1030 0 1px, transparent 1px 26px),
    repeating-linear-gradient(90deg, #0b1030 0 1px, transparent 1px 26px), #070a22;
  font-family: 'Kanit', sans-serif;
}
.block-container { padding-top: 1.5rem; }
header[data-testid="stHeader"], [data-testid="stToolbar"],
.stDeployButton, #MainMenu, footer { display: none !important; visibility: hidden; }

/* Top bar */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  border: 2px solid #22d3ee; border-radius: 8px; padding: 10px 18px;
  background: #0a1140;
  box-shadow: 0 0 14px rgba(34,211,238,.35), inset 0 0 18px rgba(34,211,238,.12);
  margin-bottom: 16px;
}
.topbar .ttl { font-family: 'Press Start 2P'; color: #22d3ee; font-size: .9rem;
  text-shadow: 0 0 8px rgba(34,211,238,.8); }
.topbar .clock { font-family: 'Press Start 2P'; color: #a3e635; font-size: .8rem;
  border: 2px solid #a3e635; border-radius: 6px; padding: 5px 10px;
  text-shadow: 0 0 8px rgba(163,230,53,.7); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: #0a1140; border-radius: 8px; padding: 4px;
  border: 2px solid #1e3a8a; gap: 4px;
}
.stTabs [data-baseweb="tab"] {
  font-family: 'Press Start 2P'; font-size: .58rem; color: #7c8cc4;
  background: transparent; border: none; border-radius: 6px;
  padding: 10px 14px; letter-spacing: .5px;
}
.stTabs [aria-selected="true"] {
  background: #22d3ee !important; color: #07122e !important;
  box-shadow: 0 0 12px rgba(34,211,238,.5);
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px; }

/* Panel cards */
.panel {
  border: 2px solid #3b82f6; border-radius: 8px; background: #0a0f33;
  box-shadow: 0 0 12px rgba(59,130,246,.25), inset 0 0 16px rgba(59,130,246,.06);
  padding: 16px; margin-bottom: 12px;
}
.panel-title {
  font-family: 'Press Start 2P'; font-size: .65rem; color: #67e8f9;
  letter-spacing: 1px; margin-bottom: 12px; text-shadow: 0 0 6px rgba(103,232,249,.7);
}

/* Typography */
h1, h2, h3, p, li, .stMarkdown { color: #dbe4ff !important; }
.stMarkdown h2 { color: #67e8f9 !important; border-bottom: 1px solid #1e3a8a; padding-bottom: 4px; }
.stMarkdown h3 { color: #a3e635 !important; }
.label { font-family: 'VT323'; font-size: 1.15rem; color: #67e8f9; }
.bigstat { font-family: 'Press Start 2P'; color: #a3e635; font-size: 1rem;
  text-shadow: 0 0 8px rgba(163,230,53,.7); }
.minor { font-family: 'VT323'; color: #67e8f9; font-size: 1.1rem; }
.warn { font-family: 'VT323'; color: #fbbf24; font-size: 1.05rem; }

/* Buttons */
.stButton > button {
  background: #0a1140; color: #22d3ee; border: 2px solid #22d3ee;
  border-radius: 8px; font-family: 'Press Start 2P'; font-size: .65rem;
  padding: 12px 0; letter-spacing: 1px;
  box-shadow: 0 0 10px rgba(34,211,238,.3);
}
.stButton > button:hover { background: #22d3ee; color: #07122e; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
  background: #0b1240 !important; color: #e0e7ff !important;
  border: 2px solid #3b82f6 !important; border-radius: 8px !important;
  font-family: 'Kanit' !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stDateInput label, .stNumberInput label, .stRadio label { color: #67e8f9 !important; font-weight: 600; }

/* Event countdown badges */
.badge-red    { background:#7f1d1d; color:#fca5a5; border-radius:6px; padding:2px 8px; font-size:.85rem; }
.badge-orange { background:#7c2d12; color:#fdba74; border-radius:6px; padding:2px 8px; font-size:.85rem; }
.badge-yellow { background:#713f12; color:#fde047; border-radius:6px; padding:2px 8px; font-size:.85rem; }
.badge-green  { background:#14532d; color:#86efac; border-radius:6px; padding:2px 8px; font-size:.85rem; }
.badge-blue   { background:#1e3a5f; color:#93c5fd; border-radius:6px; padding:2px 8px; font-size:.85rem; }
.badge-gray   { background:#374151; color:#9ca3af; border-radius:6px; padding:2px 8px; font-size:.85rem; }

/* Task/doc rows */
.task-row {
  border: 1px solid #1e3a8a; border-radius: 8px; padding: 10px 14px;
  margin-bottom: 8px; background: #0b1240;
}
.task-row:hover { border-color: #22d3ee; }

/* ══════════════════════════════════════════
   🟡 PAC-MAN CHARACTER ANIMATIONS
   ══════════════════════════════════════════ */
@keyframes pm-chomp {
  0%, 100% { transform: rotate(-32deg); }
  50%       { transform: rotate(0deg);  }
}
@keyframes pm-pellet-blink {
  0%, 100% { opacity: .8; transform: scale(1); }
  50%       { opacity: .15; transform: scale(.4); }
}
@keyframes ghost-bounce {
  0%, 100% { transform: translateY(0) rotate(-4deg); }
  50%       { transform: translateY(-10px) rotate(4deg); }
}
@keyframes doc-wave {
  0%, 100% { transform: rotate(-8deg) translateY(0); }
  50%       { transform: rotate(8deg) translateY(-4px); }
}
@keyframes pm-done-pop {
  0%   { transform: scale(.8); opacity: 0; }
  60%  { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); }
}

/* Pac-Man body (border-trick circle with transparent mouth) */
.pm-body {
  display: inline-block;
  width: 0; height: 0;
  border: 24px solid #4fc3f7;
  border-right-color: transparent;
  border-radius: 50%;
  position: relative;
  flex-shrink: 0;
}
.pm-body.chomping { animation: pm-chomp .45s ease-in-out infinite; }
.pm-eye {
  position: absolute;
  width: 5px; height: 5px;
  background: #0a1140;
  border-radius: 50%;
  top: -18px; left: 3px;
}

/* ── IDLE BAR ── */
.pm-idle-bar {
  display: flex; align-items: center; gap: 14px;
  padding: 9px 16px; margin-bottom: 14px;
  border: 2px solid #1e3a8a; border-radius: 8px; background: #0a0f33;
}
.pm-pellets { display: flex; gap: 8px; align-items: center; }
.pm-pellet  {
  width: 7px; height: 7px; background: #4fc3f7;
  border-radius: 50%;
}
.pm-pellet:nth-child(1) { animation: pm-pellet-blink 1.1s 0s   infinite; }
.pm-pellet:nth-child(2) { animation: pm-pellet-blink 1.1s .18s infinite; }
.pm-pellet:nth-child(3) { animation: pm-pellet-blink 1.1s .36s infinite; }
.pm-pellet:nth-child(4) { animation: pm-pellet-blink 1.1s .54s infinite; }
.pm-pellet:nth-child(5) { animation: pm-pellet-blink 1.1s .72s infinite; }
.pm-idle-txt { font-family:'VT323'; font-size:1.05rem; color:#67e8f9; }

/* ── WORKING BAR (ผีกำลังชูเอกสารวิ่งอยู่กับที่) ── */
.pm-work-bar {
  display: flex; align-items: center; gap: 18px;
  padding: 9px 16px; margin-bottom: 14px;
  border: 2px solid #3b82f6; border-radius: 8px; background: #0a0f33;
  box-shadow: 0 0 10px rgba(59,130,246,.2);
}
/* Ghost body */
.ghost {
  position: relative; width: 40px; height: 42px; flex-shrink: 0;
  animation: ghost-bounce .55s ease-in-out infinite;
}
.ghost-head {
  width: 40px; height: 34px;
  background: #a78bfa;           /* ม่วง Inky สไตล์ */
  border-radius: 20px 20px 0 0;
  position: relative;
}
.ghost-skirt {
  width: 40px; height: 12px;
  background: #a78bfa;
  clip-path: polygon(0% 0%, 12% 100%, 25% 0%, 37% 100%, 50% 0%, 63% 100%, 75% 0%, 88% 100%, 100% 0%);
}
.ghost-eye { position: absolute; width: 11px; height: 13px;
  background: white; border-radius: 50%; top: 9px; }
.ghost-eye.l { left: 7px; }
.ghost-eye.r { right: 7px; }
.ghost-eye::after {
  content: ''; position: absolute; width: 5px; height: 6px;
  background: #1e3a8a; border-radius: 50%; top: 3px; left: 3px;
}
/* Document held above ghost */
.ghost-doc {
  position: absolute; top: -22px; left: 50%;
  transform: translateX(-50%);
  font-size: 1.2rem; line-height: 1;
  animation: doc-wave .55s ease-in-out infinite;
}
.pm-work-txt {
  font-family:'VT323'; font-size:1.05rem; color:#fbbf24; white-space:nowrap;
}

/* ── DONE BAR (ถือป้ายติ๊กถูก) ── */
.pm-done-bar {
  display: flex; align-items: center; gap: 14px;
  padding: 9px 16px; margin-bottom: 14px;
  border: 2px solid #22c55e; border-radius: 8px; background: #052e16;
  box-shadow: 0 0 10px rgba(34,197,94,.25);
  animation: pm-done-pop .4s ease-out;
}
.pm-done-sign { font-size: 1.7rem; }
.pm-done-txt  { font-family:'VT323'; font-size:1.1rem; color:#86efac; }
</style>
""", unsafe_allow_html=True)


# ── Auth ──────────────────────────────────────────────────────────────────────
def check_password():
    expected = os.getenv("APP_PASSWORD")
    if not expected:
        return
    if st.session_state.get("authed"):
        return
    pwd = st.text_input("🔒 ใส่รหัสผ่าน", type="password")
    if pwd == "":
        st.stop()
    if pwd == expected:
        st.session_state.authed = True
        st.rerun()
    else:
        st.error("❌ รหัสผ่านไม่ถูกต้อง")
        st.stop()

check_password()

# ── Session State ─────────────────────────────────────────────────────────────
if "review_queue"    not in st.session_state:
    st.session_state.review_queue = []
if "tok_total"       not in st.session_state:
    st.session_state.tok_total = 0
if "tok_log"         not in st.session_state:
    st.session_state.tok_log = []          # [(label, n)] สำหรับแสดง breakdown
if "generated_plan"  not in st.session_state:
    st.session_state.generated_plan = None
if "plan_month"      not in st.session_state:
    st.session_state.plan_month = None
if "plan_year"       not in st.session_state:
    st.session_state.plan_year = None
if "content_req"     not in st.session_state:
    st.session_state.content_req = ""      # pre-fill text area จาก Planner
if "clickup_ctx_ch"  not in st.session_state:
    st.session_state.clickup_ctx_ch = ""   # ClickUp channel ที่เลือกเป็น context
if "last_generated"  not in st.session_state:
    st.session_state.last_generated = None  # เก็บผล content ล่าสุด (fix review bug)


def _add_tokens(label: str, n: int):
    """เพิ่ม token เข้า session แบบ tracked"""
    if n > 0:
        st.session_state.tok_total += n
        st.session_state.tok_log.append((label, n))

# ── Top Bar ───────────────────────────────────────────────────────────────────
now_th = datetime.now(TH)
_sync_ok   = github_configured()
_sync_icon = "☁️ ซิงค์ GitHub ✅" if _sync_ok else "⚠️ ยังไม่ได้ตั้ง GitHub Sync"
_sync_color = "#86efac" if _sync_ok else "#fbbf24"
st.markdown(f"""
<div class="topbar">
  <span class="ttl">▣ MARKETING OPS v2.0 — JET8</span>
  <span style="font-family:'VT323';font-size:1rem;color:{_sync_color};">{_sync_icon}</span>
  <span class="clock">{now_th.strftime('%d/%m/%Y %H:%M')}</span>
</div>
""", unsafe_allow_html=True)

if not _sync_ok:
    st.warning(
        "⚠️ **ข้อมูลจะหายเมื่อแอปรีสตาร์ท** — ยังไม่ได้ตั้งค่า GitHub Sync  \n"
        "เพิ่มใน Streamlit Cloud → Settings → Secrets:  \n"
        "```\nGITHUB_TOKEN = \"ghp_xxxxxxxxxxxx\"\n"
        "GITHUB_REPO  = \"username/jet8-marketing-ops\"\n```  \n"
        "วิธีสร้าง Token: GitHub → Settings → Developer settings → Personal access tokens → Generate (เลือก scope **repo**)"
    )

# ── Helper ───────────────────────────────────────────────────────────────────

import json as _json

PLANS_DIR = "data/plans"
os.makedirs(PLANS_DIR, exist_ok=True)

def _plan_path(month: int, year: int) -> str:
    return os.path.join(PLANS_DIR, f"plan_{year}_{month:02d}.json")


def _gh_token_repo() -> tuple[str, str]:
    """คืน (token, repo) จาก env หรือ st.secrets — คืน ("","") ถ้ายังไม่ตั้งค่า"""
    token = os.getenv("GITHUB_TOKEN", "")
    repo  = os.getenv("GITHUB_REPO",  "")
    try:
        if not token: token = st.secrets.get("GITHUB_TOKEN", "")
        if not repo:  repo  = st.secrets.get("GITHUB_REPO",  "")
    except Exception:
        pass
    return token, repo

def github_configured() -> bool:
    t, r = _gh_token_repo()
    return bool(t and r)

def _github_commit_file(local_path: str, commit_msg: str = "") -> bool:
    """
    Commit ไฟล์ local ขึ้น GitHub repo เพื่อ persist ข้ามการ restart
    ต้องตั้ง GITHUB_TOKEN และ GITHUB_REPO ใน Streamlit Secrets:
      GITHUB_TOKEN = "ghp_xxxx"
      GITHUB_REPO  = "username/jet8-marketing-ops"
    """
    try:
        token, repo = _gh_token_repo()
        if not token or not repo:
            return False
        if not os.path.exists(local_path):
            return False

        with open(local_path, "rb") as f:
            raw = f.read()

        url     = f"https://api.github.com/repos/{repo}/contents/{local_path}"
        headers = {"Authorization": f"token {token}",
                   "Accept": "application/vnd.github.v3+json"}

        r   = _requests.get(url, headers=headers, timeout=10)
        sha = r.json().get("sha") if r.status_code == 200 else None

        payload = {
            "message": commit_msg or f"💾 auto-save: {local_path}",
            "content": base64.b64encode(raw).decode(),
            "branch":  "main",
        }
        if sha:
            payload["sha"] = sha

        resp = _requests.put(url, headers=headers, json=payload, timeout=15)
        return resp.status_code in (200, 201)
    except Exception:
        return False


def save_plan(month: int, year: int, content: str):
    path     = _plan_path(month, year)
    existing = load_plan(month, year)
    data = {
        "month":      month,
        "year":       year,
        "content":    content,
        "saved_at":   existing.get("saved_at", datetime.now(TH).isoformat()),
        "updated_at": datetime.now(TH).isoformat(),
    }
    json_str = _json.dumps(data, ensure_ascii=False, indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json_str)
    _github_commit_file(path, f"💾 Plan: {month:02d}/{year}")

def load_plan(month: int, year: int) -> dict:
    path = _plan_path(month, year)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)

def list_saved_plans() -> list:
    """คืน list ของแผนที่บันทึกไว้ เรียงล่าสุดก่อน"""
    plans = []
    for fname in sorted(os.listdir(PLANS_DIR), reverse=True):
        if fname.endswith(".json"):
            with open(os.path.join(PLANS_DIR, fname), "r", encoding="utf-8") as f:
                plans.append(_json.load(f))
    return plans

def pacman_html(state: str = "idle") -> str:
    """คืน HTML สำหรับ Pac-Man น้อย 3 สถานะ: idle | working | done"""
    if state == "idle":
        return """<div class="pm-idle-bar">
  <div class="pm-body chomping"><div class="pm-eye"></div></div>
  <div class="pm-pellets">
    <div class="pm-pellet"></div><div class="pm-pellet"></div>
    <div class="pm-pellet"></div><div class="pm-pellet"></div>
    <div class="pm-pellet"></div>
  </div>
  <span class="pm-idle-txt">รอรับคำสั่งอยู่นะคะ... 🎮</span>
</div>"""
    elif state == "working":
        return """<div class="pm-work-bar">
  <div class="ghost">
    <div class="ghost-doc">📄📄</div>
    <div class="ghost-head">
      <div class="ghost-eye l"></div>
      <div class="ghost-eye r"></div>
    </div>
    <div class="ghost-skirt"></div>
  </div>
  <span class="pm-work-txt">กำลังทำงานค่ะ ✨</span>
</div>"""
    else:  # done
        return """<div class="pm-done-bar">
  <div class="pm-body"><div class="pm-eye"></div></div>
  <span class="pm-done-sign">📋✅</span>
  <span class="pm-done-txt">เสร็จแล้วค่ะ! 🎉</span>
</div>"""


def _render_tasks(tasks: list):
    """แสดงผล task list สำหรับแท็บ Documents"""
    if not tasks:
        st.markdown('<div class="minor">  // ไม่มีรายการ</div>', unsafe_allow_html=True)
        return
    for task in tasks:
        if "error" in task:
            st.error(f"❌ {task['error']}")
        else:
            url_part = f'<a href="{task["url"]}" target="_blank">↗</a>' if task["url"] else ""
            st.markdown(f"""
<div class="task-row">
  <b>{task['name']}</b> {url_part}<br>
  <span style="color:#7c8cc4;font-size:.85rem">
    🏷️ {task['status']} &nbsp;|&nbsp; 🕐 {task['updated_at']}
  </span>
</div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📅 Planner",
    "🔍 Research",
    "📄 Documents",
    "🗓️ Events",
    "✍️ Content",
    "✅ Review",
])


# ════════════════════════════════════════════════════════════════
#  TAB 1 — PLANNER
# ════════════════════════════════════════════════════════════════
with t1:
    st.markdown('<div class="panel-title">📅 วางแผนธีมและตารางโพสต์รายเดือน</div>', unsafe_allow_html=True)

    if not PLANNER_OK:
        st.error("❌ ไม่พบไฟล์ planner.py")
    else:
        # ── ส่วนบน: สร้างแผนใหม่ ──────────────────────────────────────────
        col1, col2 = st.columns([1, 2])
        with col1:
            sel_month = st.selectbox("เดือน", list(range(1, 13)),
                index=now_th.month - 1,
                format_func=lambda m: planner_agent.THAI_MONTHS[m])
            sel_year = st.number_input("ปี (ค.ศ.)", value=now_th.year, step=1,
                min_value=2020, max_value=2030)
            focus_text = st.text_area("โฟกัสพิเศษเดือนนี้ (optional)",
                placeholder="เช่น งาน THAIFEX, กฎระเบียบ อย. ใหม่ ...", height=80)

            month_events = []
            if EVENT_OK:
                month_events = event_tracker.get_events_in_month(sel_month, sel_year)
                if month_events:
                    st.info(f"🗓️ พบ {len(month_events)} อีเวนต์ในเดือนนี้")

            # แสดงสถานะแผนที่มีอยู่แล้ว
            existing = load_plan(sel_month, sel_year)
            if existing:
                updated = existing.get("updated_at", "")[:10]
                st.info(f"📌 มีแผนบันทึกไว้แล้ว (อัปเดต {updated})")

            gen_btn = st.button("► สร้างแผนใหม่", use_container_width=True)

        with col2:
            pm_plan = st.empty()
            pm_plan.markdown(pacman_html("idle"), unsafe_allow_html=True)

            if gen_btn:
                pm_plan.markdown(pacman_html("working"), unsafe_allow_html=True)
                trends_ctx = trend_summarizer.get_latest_trend_for_planner() if TREND_OK else ""
                try:
                    plan = planner_agent.generate_plan(
                        month=sel_month, year=sel_year,
                        focus=focus_text, events=month_events or None,
                        trends_context=trends_ctx,
                    )
                except TypeError:
                    # planner.py เวอร์ชันเก่า (ยังไม่มี trends_context) — fallback
                    plan = planner_agent.generate_plan(
                        month=sel_month, year=sel_year,
                        focus=focus_text, events=month_events or None,
                    )
                pm_plan.markdown(pacman_html("done"), unsafe_allow_html=True)
                _add_tokens("Planner", planner_agent.last_usage["total"])
                st.session_state.generated_plan   = plan
                st.session_state.plan_month       = sel_month
                st.session_state.plan_year        = sel_year

            # แสดงแผนที่เพิ่งสร้าง (ถ้าตรงเดือน/ปีที่เลือก)
            if (st.session_state.generated_plan
                    and st.session_state.plan_month == sel_month
                    and st.session_state.plan_year  == sel_year):

                plan = st.session_state.generated_plan
                st.markdown(plan)
                st.markdown(f'<div class="minor">🔢 Tokens: {planner_agent.last_usage["total"]:,}</div>',
                    unsafe_allow_html=True)

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("✅ ใช้แผนนี้ — บันทึกเข้าระบบ", use_container_width=True):
                        save_plan(sel_month, sel_year, plan)
                        st.session_state.generated_plan = None
                        st.success(f"✅ บันทึกแผน {planner_agent.THAI_MONTHS[sel_month]} {sel_year} แล้ว!")
                        st.rerun()
                with bc2:
                    st.download_button("⬇ ดาวน์โหลด (.md)", data=plan,
                        file_name=f"plan_{sel_year}_{sel_month:02d}.md",
                        mime="text/markdown", use_container_width=True)
            elif not gen_btn:
                st.markdown('<div class="minor">// เลือกเดือน แล้วกด "สร้างแผนใหม่"</div>',
                    unsafe_allow_html=True)

        # ── แจ้งเตือนบน Streamlit Cloud ───────────────────────────────────
        _on_cloud = not os.path.exists(".env")   # ไม่มี .env = น่าจะรันบน cloud
        if _on_cloud:
            st.info(
                "☁️ **รันบน Streamlit Cloud** — แผนที่สร้างในหน้านี้จะหายเมื่อแอปรีสตาร์ท  \n"
                "📥 **ดาวน์โหลดแผนไว้** และ **อัปโหลดกลับ** ด้านล่างได้เลยค่ะ"
            )

        # ── ส่วนล่าง: แผนที่บันทึกไว้ (โหลด + แก้ไข) ─────────────────────
        st.divider()

        # ── อัปโหลดแผนที่ดาวน์โหลดไว้ (สำหรับ Streamlit Cloud) ─────────────
        with st.expander("📤 อัปโหลดแผนที่บันทึกไว้ (.json)", expanded=False):
            uploaded_plan = st.file_uploader(
                "เลือกไฟล์ plan_YYYY_MM.json", type=["json"], key="plan_upload")
            if uploaded_plan is not None:
                try:
                    plan_data = _json.loads(uploaded_plan.read().decode("utf-8"))
                    save_plan(plan_data["month"], plan_data["year"], plan_data["content"])
                    st.success(f"✅ อัปโหลดแผน {planner_agent.THAI_MONTHS[plan_data['month']]} {plan_data['year']} สำเร็จ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ไฟล์ไม่ถูกต้อง: {e}")

        saved_plans = list_saved_plans()
        if saved_plans:
            st.markdown('<div class="panel-title">📂 แผนที่บันทึกไว้</div>', unsafe_allow_html=True)
            for p in saved_plans:
                m, y = p["month"], p["year"]
                label = f"{planner_agent.THAI_MONTHS[m]} {y}"
                updated = p.get("updated_at", "")[:10]
                with st.expander(f"📅 {label}  —  อัปเดต {updated}"):
                    edited = st.text_area(
                        "แก้ไขแผน",
                        value=p["content"],
                        height=400,
                        key=f"edit_{y}_{m:02d}",
                    )
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.button("💾 บันทึกการแก้ไข", key=f"save_{y}_{m:02d}",
                                     use_container_width=True):
                            save_plan(m, y, edited)
                            st.success("✅ บันทึกแล้ว!")
                            st.rerun()
                    with sc2:
                        st.download_button("⬇ ดาวน์โหลด", data=edited,
                            file_name=f"plan_{y}_{m:02d}.md", mime="text/markdown",
                            key=f"dl_{y}_{m:02d}", use_container_width=True)


# ════════════════════════════════════════════════════════════════
#  TAB 2 — RESEARCH
# ════════════════════════════════════════════════════════════════
with t2:
    st.markdown('<div class="panel-title">🔍 ติดตามข่าวและเทรนด์อุตสาหกรรม</div>', unsafe_allow_html=True)

    if not NEWS_OK or not RESEARCH_OK:
        st.error("❌ ไม่พบ news_monitor.py หรือ marketing_researcher.py")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="label">STEP 1 — ดึงข่าวใหม่</div>', unsafe_allow_html=True)
            pm_news = st.empty()
            pm_news.markdown(pacman_html("idle"), unsafe_allow_html=True)
            if st.button("► ดึงข่าว (News Monitor)", use_container_width=True):
                pm_news.markdown(pacman_html("working"), unsafe_allow_html=True)
                results, total = news_monitor.main()
                pm_news.markdown(pacman_html("done"), unsafe_allow_html=True)
                if total > 0:
                    st.success(f"✅ พบข่าวใหม่ {total} รายการ — ส่ง Slack แล้ว")
                    for group, arts in results.items():
                        if arts:
                            st.markdown(f"**{group}** ({len(arts)} รายการ)")
                            for a in arts[:3]:
                                st.markdown(f"- [{a['title']}]({a['url']})")
                else:
                    st.info("ℹ️ ไม่พบข่าวใหม่ในรอบนี้")

        with col2:
            st.markdown('<div class="label">STEP 2 — วิเคราะห์เชิงธุรกิจ</div>', unsafe_allow_html=True)
            pm_research = st.empty()
            pm_research.markdown(pacman_html("idle"), unsafe_allow_html=True)
            if st.button("► วิเคราะห์ข่าว (Research Analyst)", use_container_width=True):
                pm_research.markdown(pacman_html("working"), unsafe_allow_html=True)
                filepath = marketing_researcher.main()
                pm_research.markdown(pacman_html("done"), unsafe_allow_html=True)
                _add_tokens("Research", marketing_researcher.last_usage.get("total", 0))
                if filepath:
                    with open(filepath, "r", encoding="utf-8") as f:
                        report_content = f.read()
                    st.success(f"✅ บันทึกรายงานแล้ว: {filepath}")
                    st.markdown(report_content)
                    st.download_button("⬇ ดาวน์โหลดรายงาน", data=report_content,
                        file_name=os.path.basename(filepath), mime="text/markdown",
                        use_container_width=True)
                else:
                    st.warning("⚠️ ไม่มีข่าวให้วิเคราะห์ — รัน Step 1 ก่อน")

    # ── STEP 3 — TREND SUMMARIZER ──────────────────────────────────────────────
    st.divider()
    st.markdown('<div class="label">STEP 3 — สรุปเทรนด์รายเดือน (Trend Summarizer)</div>',
        unsafe_allow_html=True)

    if not TREND_OK:
        st.error("❌ ไม่พบ trend_summarizer.py")
    else:
        tr_c1, tr_c2 = st.columns([1, 2])
        with tr_c1:
            # เลือกเดือน/ปีที่จะสรุป
            tr_month = st.selectbox("เดือนที่จะสรุป", list(range(1, 13)),
                index=(now_th.month - 2) % 12,        # default = เดือนที่แล้ว
                format_func=lambda m: trend_summarizer.THAI_MONTHS[m],
                key="tr_month")
            tr_year  = st.number_input("ปี (ค.ศ.)", value=now_th.year
                if now_th.month > 1 else now_th.year - 1,
                step=1, min_value=2020, max_value=2035, key="tr_year")

            # แสดงถ้ามีสรุปอยู่แล้ว
            saved_trends = trend_summarizer.list_saved_trends()
            saved_labels = [t["label"] for t in saved_trends]
            check_label  = f"{trend_summarizer.THAI_MONTHS[tr_month]} {int(tr_year)}"
            if check_label in saved_labels:
                st.info(f"✅ มีสรุปเดือน {check_label} แล้ว — สร้างใหม่ได้เพื่ออัปเดต")

            gen_trend_btn = st.button("► สรุปเทรนด์ (ใช้ Claude)", use_container_width=True)

        with tr_c2:
            pm_trend = st.empty()
            pm_trend.markdown(pacman_html("idle"), unsafe_allow_html=True)

            if gen_trend_btn:
                pm_trend.markdown(pacman_html("working"), unsafe_allow_html=True)
                trend_content, trend_path = trend_summarizer.generate_trend_summary(
                    int(tr_month), int(tr_year))
                pm_trend.markdown(pacman_html("done"), unsafe_allow_html=True)
                _add_tokens("Trend", trend_summarizer.last_usage.get("total", 0))
                st.success(f"✅ บันทึกแล้ว: {trend_path}")
                st.markdown(trend_content)
                st.download_button("⬇ ดาวน์โหลด (.md)", data=trend_content,
                    file_name=os.path.basename(trend_path), mime="text/markdown",
                    use_container_width=True)

        # แสดงสรุปเทรนด์ที่มีอยู่แล้ว
        if saved_trends:
            st.markdown('<div class="label" style="margin-top:12px">📂 สรุปเทรนด์ที่บันทึกไว้</div>',
                unsafe_allow_html=True)
            for trend in saved_trends[:3]:   # แสดงแค่ 3 อันล่าสุด
                with st.expander(f"📊 {trend['label']}"):
                    st.markdown(trend["content"])
                    st.download_button(
                        "⬇ ดาวน์โหลด",
                        data=trend["content"],
                        file_name=os.path.basename(trend["filepath"]),
                        mime="text/markdown",
                        key=f"dl_trend_{trend['year']}_{trend['month']:02d}",
                        use_container_width=True,
                    )


# ════════════════════════════════════════════════════════════════
#  TAB 3 — DOCUMENTS (ClickUp)
# ════════════════════════════════════════════════════════════════
with t3:
    st.markdown('<div class="panel-title">📄 เอกสารและอัปเดตจาก ClickUp</div>', unsafe_allow_html=True)

    if not DOC_OK:
        st.error("❌ ไม่พบ document_researcher.py")
    elif not document_researcher.is_configured():
        st.warning("⚠️ ยังไม่ตั้งค่า ClickUp — เพิ่มใน .env:")
        st.code("CLICKUP_TOKEN=pk_xxxxxxxxxxxx\nCUSTOMS_LIST_ID=xxxxxxxxx\nFDA_LIST_ID=xxxxxxxxx\nMOC_LIST_ID=xxxxxxxxx")
        st.markdown("วิธีหา API Token: ClickUp → Settings → Apps → API Token")
    else:
        col1, col2 = st.columns([1, 2.5])

        with col1:
            days_back  = st.slider("ดูย้อนหลัง (วัน)", 7, 90, 30)
            search_kw  = st.text_input("ค้นหา keyword (optional)",
                placeholder="เช่น อย., import, regulation")

            # แสดงสถานะ List ID แต่ละช่อง
            st.markdown('<div class="label" style="margin-top:12px">สถานะช่องทาง</div>',
                unsafe_allow_html=True)
            for key, ch in document_researcher.get_channels().items():
                ok = bool(ch["list_id"])
                dot = "🟢" if ok else "🔴"
                st.markdown(f"{dot} {ch['label']}", unsafe_allow_html=False)

            fetch_btn = st.button("► ดึงข้อมูลจาก ClickUp", use_container_width=True)

        with col2:
            pm_doc = st.empty()
            pm_doc.markdown(pacman_html("idle"), unsafe_allow_html=True)
            if fetch_btn:
                pm_doc.markdown(pacman_html("working"), unsafe_allow_html=True)
                if search_kw.strip():
                    all_data_s = {key: document_researcher.search_in_channel(key, search_kw.strip())
                                  for key in document_researcher.get_channels()}
                    pm_doc.markdown(pacman_html("done"), unsafe_allow_html=True)
                    for key, ch in document_researcher.get_channels().items():
                        st.markdown(f'**{ch["label"]}** — ผลการค้นหา "{search_kw}"')
                        _render_tasks(all_data_s[key])
                else:
                    all_data = document_researcher.fetch_all_channels(days=days_back)
                    pm_doc.markdown(pacman_html("done"), unsafe_allow_html=True)
                    for key, ch in document_researcher.get_channels().items():
                        tasks = all_data.get(key, [])
                        real = [t for t in tasks if "error" not in t]
                        st.markdown(f'**{ch["label"]}** — {len(real)} รายการใน {days_back} วัน')
                        _render_tasks(tasks)


# ════════════════════════════════════════════════════════════════
#  TAB 4 — EVENTS
# ════════════════════════════════════════════════════════════════
with t4:
    st.markdown('<div class="panel-title">🗓️ ติดตามอีเวนต์ที่สนใจ</div>', unsafe_allow_html=True)
    st.markdown('<div class="warn">⚙️ Google Calendar integration: coming soon</div>',
        unsafe_allow_html=True)
    st.markdown(pacman_html("idle"), unsafe_allow_html=True)

    if not EVENT_OK:
        st.error("❌ ไม่พบ event_tracker.py")
    else:
        col1, col2 = st.columns([1, 1.3])

        with col1:
            st.markdown('<div class="label">➕ เพิ่มอีเวนต์ใหม่</div>', unsafe_allow_html=True)
            with st.form("add_event_form", clear_on_submit=True):
                ev_name    = st.text_input("ชื่ออีเวนต์ *", placeholder="เช่น THAIFEX 2026")
                ev_start   = st.date_input("วันเริ่มต้น *", value=now_th.date())
                ev_end     = st.date_input("วันสิ้นสุด *",  value=now_th.date())
                ev_purpose = st.text_area("เป้าประสงค์ *",
                    placeholder="เช่น สร้าง connection, หาลูกค้าใหม่ในกลุ่ม Pharma", height=70)
                ev_channel = st.selectbox("ช่องทางที่จะโพสต์",
                    ["Facebook", "LinkedIn", "Facebook + LinkedIn", "เว็บไซต์", "ทุกช่องทาง", "—"])
                ev_notes   = st.text_input("หมายเหตุ (optional)")
                submitted  = st.form_submit_button("✅ บันทึกอีเวนต์", use_container_width=True)

            if submitted:
                if not ev_name or not ev_purpose:
                    st.error("กรุณากรอกชื่ออีเวนต์และเป้าประสงค์")
                else:
                    event_tracker.add_event(
                        name=ev_name, start_date=str(ev_start), end_date=str(ev_end),
                        purpose=ev_purpose, channel=ev_channel, notes=ev_notes,
                    )
                    _github_commit_file("data/events.json", f"💾 Event: {ev_name}")
                    st.success(f'✅ บันทึก "{ev_name}" แล้ว!')
                    st.rerun()

        with col2:
            st.markdown('<div class="label">📌 อีเวนต์ที่กำลังจะมา</div>', unsafe_allow_html=True)
            upcoming = event_tracker.get_upcoming_events()

            if not upcoming:
                st.markdown('<div class="minor">// ยังไม่มีอีเวนต์ — เพิ่มทางซ้ายได้เลย</div>',
                    unsafe_allow_html=True)
            else:
                for ev in upcoming:
                    days = ev["days_until"]
                    if days < 0:
                        badge = f'<span class="badge-gray">ผ่านมา {abs(days)} วัน</span>'
                    elif days == 0:
                        badge = '<span class="badge-red">🔴 วันนี้!</span>'
                    elif days <= 7:
                        badge = f'<span class="badge-orange">🟠 อีก {days} วัน</span>'
                    elif days <= 30:
                        badge = f'<span class="badge-yellow">🟡 อีก {days} วัน</span>'
                    else:
                        badge = f'<span class="badge-blue">🔵 อีก {days} วัน</span>'

                    channel_txt = f"📢 {ev['channel']}" if ev.get("channel") and ev["channel"] != "—" else ""
                    st.markdown(f"""
<div class="task-row">
  {badge} &nbsp; <b>{ev['name']}</b><br>
  <span style="color:#a3e635;font-size:.85rem">🗓️ {ev['start_date']} – {ev['end_date']}</span><br>
  <span style="color:#dbe4ff;font-size:.9rem">🎯 {ev['purpose']}</span><br>
  <span style="color:#7c8cc4;font-size:.85rem">{channel_txt}</span>
</div>""", unsafe_allow_html=True)

                    if st.button("🗑️ ลบ", key=f"del_{ev['id']}"):
                        event_tracker.delete_event(ev["id"])
                        _github_commit_file("data/events.json", f"🗑️ Del event: {ev['name']}")
                        st.rerun()


# ════════════════════════════════════════════════════════════════
#  TAB 5 — CONTENT
# ════════════════════════════════════════════════════════════════
with t5:
    st.markdown('<div class="panel-title">✍️ เขียนคอนเทนต์การตลาด</div>', unsafe_allow_html=True)

    if not CONTENT_OK:
        st.error("❌ ไม่พบ agent.py")
    else:
        # ── แหล่งอ้างอิง: Planner + ClickUp ─────────────────────────────────
        with st.expander("📅 เลือกหัวข้อจากแผน + อ้างอิงข้อมูล ClickUp", expanded=False):
            ref_c1, ref_c2 = st.columns(2)

            with ref_c1:
                st.markdown('<div class="label" style="margin-bottom:6px">หัวข้อจากแผนเดือนนี้</div>',
                    unsafe_allow_html=True)
                cur_plan = load_plan(now_th.month, now_th.year)
                plan_topics = ["— เลือกเองได้เลย —"]
                if cur_plan.get("content"):
                    for line in cur_plan["content"].split("\n"):
                        stripped = line.strip()
                        if stripped.startswith("- ") and len(stripped) > 4:
                            plan_topics.append(stripped[2:].strip())

                if len(plan_topics) > 1:
                    sel_topic = st.selectbox("หัวข้อจากแผน", plan_topics, key="sel_topic_plan")
                    if sel_topic != plan_topics[0]:
                        if st.button("✏️ ใส่หัวข้อนี้ในช่องโจทย์", use_container_width=True):
                            st.session_state.content_req = sel_topic
                            st.rerun()
                else:
                    st.info("ยังไม่มีแผนเดือนนี้ — สร้างในแท็บ 📅 Planner ก่อนนะคะ")

            with ref_c2:
                st.markdown('<div class="label" style="margin-bottom:6px">อ้างอิงข้อมูล ClickUp</div>',
                    unsafe_allow_html=True)
                if DOC_OK and document_researcher.is_configured():
                    ch_map = {k: v["label"] for k, v in document_researcher.get_channels().items()}
                    ch_keys = ["— ไม่ใช้ —"] + list(ch_map.keys())
                    sel_ch_display = st.selectbox(
                        "ช่องทาง ClickUp",
                        ch_keys,
                        format_func=lambda k: ch_map.get(k, k),
                        key="clickup_ctx_sel",
                    )
                    if sel_ch_display != ch_keys[0]:
                        st.session_state.clickup_ctx_ch = sel_ch_display
                        st.caption(f"จะดึงงานล่าสุด 7 รายการจาก {ch_map[sel_ch_display]} ใส่เป็น context ให้ AI")
                    else:
                        st.session_state.clickup_ctx_ch = ""
                else:
                    st.warning("ClickUp ยังไม่ตั้งค่า — ไปตั้งค่าในแท็บ 📄 Documents")

        # ── ฟอร์มหลัก ───────────────────────────────────────────────────────
        col1, col2 = st.columns([1, 1.3])

        with col1:
            ctype_label = st.radio("ประเภทคอนเทนต์",
                ["Facebook Post", "LinkedIn Post", "คอนเทนต์เว็บไซต์"])
            ctype_map = {
                "Facebook Post":     "facebook",
                "LinkedIn Post":     "linkedin",
                "คอนเทนต์เว็บไซต์": "website",
            }
            ctype = ctype_map[ctype_label]
            content_request = st.text_area(
                "โจทย์ที่ต้องการ *",
                placeholder="เช่น เขียนโพสต์อธิบายกระบวนการนำเข้ายาสำหรับ SME",
                height=120,
                key="content_req",          # ← sync กับ session state (pre-fill จาก Planner)
            )
            post_slack  = st.checkbox("ส่งไป Slack หลังเขียนเสร็จ", value=False)
            gen_btn_c   = st.button("► เขียนคอนเทนต์", use_container_width=True)

        with col2:
            pm_content = st.empty()

            if gen_btn_c:
                if not content_request.strip():
                    st.warning("กรุณาใส่โจทย์ก่อน")
                    pm_content.markdown(pacman_html("idle"), unsafe_allow_html=True)
                else:
                    # เพิ่ม ClickUp context ถ้าเลือกไว้
                    full_req = content_request.strip()
                    ctx_ch = st.session_state.get("clickup_ctx_ch", "")
                    if ctx_ch and DOC_OK and document_researcher.is_configured():
                        ctx_tasks = document_researcher.fetch_by_channel(ctx_ch, days=30, max_results=7)
                        ctx_lines = [f"- {t['name']} (สถานะ: {t['status']})"
                                     for t in ctx_tasks if "error" not in t]
                        if ctx_lines:
                            ch_lbl = document_researcher.get_channels()[ctx_ch]["label"]
                            full_req += (f"\n\n[ข้อมูลอ้างอิงจาก ClickUp — {ch_lbl}]\n"
                                         + "\n".join(ctx_lines)
                                         + "\n\nใช้ข้อมูลด้านบนประกอบการเขียนคอนเทนต์ให้น่าเชื่อถือ")

                    pm_content.markdown(pacman_html("working"), unsafe_allow_html=True)
                    result = content_agent.generate_content(
                        full_req, content_type=ctype, post_to_slack=post_slack)
                    pm_content.markdown(pacman_html("done"), unsafe_allow_html=True)
                    _add_tokens("Content", content_agent.last_usage["total"])
                    # ── เก็บผลใน session_state เพื่อให้ปุ่ม Review ทำงานได้ ──
                    st.session_state.last_generated = {
                        "content": result,
                        "type":    ctype_label,
                        "request": content_request,
                        "tokens":  content_agent.last_usage["total"],
                    }

            # ── แสดงผล + ปุ่ม Review อยู่ "นอก" if gen_btn_c ────────────────
            # สำคัญ: ถ้าปุ่ม Review ถูกกด Streamlit rerun → gen_btn_c = False
            # แต่ last_generated ยังอยู่ใน session_state → ปุ่มแสดงผลถูกต้อง
            if st.session_state.last_generated:
                gen = st.session_state.last_generated
                pm_content.markdown(pacman_html("done"), unsafe_allow_html=True)
                st.markdown(gen["content"])
                st.markdown(f'<div class="minor">🔢 {gen["tokens"]:,} tokens</div>',
                    unsafe_allow_html=True)
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("📨 ส่งให้ Reviewer ตรวจ", use_container_width=True):
                        st.session_state.review_queue.append({
                            "type":     gen["type"],
                            "request":  gen["request"],
                            "content":  gen["content"],
                            "added_at": now_th.strftime("%H:%M"),
                        })
                        st.session_state.last_generated = None
                        st.success("✅ ส่งไปแท็บ ✅ Review แล้ว!")
                        st.rerun()
                with rc2:
                    if st.button("🗑️ ล้าง / เขียนใหม่", use_container_width=True):
                        st.session_state.last_generated = None
                        st.rerun()
            elif not gen_btn_c:
                pm_content.markdown(pacman_html("idle"), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 6 — REVIEW
# ════════════════════════════════════════════════════════════════
with t6:
    st.markdown('<div class="panel-title">✅ ตรวจสอบคุณภาพคอนเทนต์</div>', unsafe_allow_html=True)

    if not REVIEW_OK:
        st.error("❌ ไม่พบ supervisor_agent.py")
    else:
        queue = st.session_state.review_queue

        if not queue:
            st.markdown(
                '<div class="minor">// ยังไม่มีคอนเทนต์รอตรวจ<br>'
                'ไปแท็บ ✍️ Content แล้วกด "ส่งให้ Reviewer"</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="label">คิวรอตรวจ: {len(queue)} รายการ</div>',
                unsafe_allow_html=True)

            for i, item in enumerate(list(queue)):
                with st.expander(
                    f"[{item['type']}] {item['request'][:60]}... — {item['added_at']}",
                    expanded=(i == 0)):

                    st.markdown("**คอนเทนต์ต้นฉบับ:**")
                    st.markdown(item["content"])
                    st.divider()

                    col_a, col_b = st.columns(2)
                    with col_a:
                        pm_rev = st.empty()
                        pm_rev.markdown(pacman_html(
                            "done" if f"qc_{i}" in st.session_state else "idle"),
                            unsafe_allow_html=True)
                        if st.button("🤖 ให้ AI ตรวจ (Supervisor)", key=f"ai_{i}",
                                     use_container_width=True):
                            pm_rev.markdown(pacman_html("working"), unsafe_allow_html=True)
                            qc = supervisor_agent.review(item["content"], "content")
                            pm_rev.markdown(pacman_html("done"), unsafe_allow_html=True)
                            _add_tokens("Review", supervisor_agent.last_usage["total"])
                            st.session_state[f"qc_{i}"] = qc

                        if f"qc_{i}" in st.session_state:
                            st.markdown("**ผล QC จาก Supervisor:**")
                            st.markdown(st.session_state[f"qc_{i}"])

                    with col_b:
                        human_comment = st.text_area(
                            "💬 ความคิดเห็น / ข้อแก้ไขของคุณ", key=f"cmt_{i}", height=120,
                            placeholder="ระบุสิ่งที่ต้องแก้ไข หรือพิมพ์ 'อนุมัติ' ถ้าโอเค")

                    btn1, btn2 = st.columns(2)
                    with btn1:
                        if st.button("✅ อนุมัติ — พร้อมโพสต์", key=f"ok_{i}",
                                     use_container_width=True):
                            st.success("✅ อนุมัติแล้ว! พร้อมส่งให้ทีมโพสต์")
                            st.session_state.review_queue.pop(i)
                            st.rerun()
                    with btn2:
                        if st.button("🔄 ส่งกลับแก้ไข", key=f"rej_{i}",
                                     use_container_width=True):
                            cmt = st.session_state.get(f"cmt_{i}", "").strip()
                            if not cmt:
                                st.warning("กรุณาใส่ความคิดเห็นก่อนส่งกลับ")
                            else:
                                st.session_state.review_queue[i]["feedback"] = cmt
                                st.info(f"📨 บันทึกความคิดเห็นแล้ว: {cmt[:60]}...")

# ── Footer: Token Counter ─────────────────────────────────────────────────────
log_parts = " &nbsp;|&nbsp; ".join(
    f"{lbl}: {n:,}" for lbl, n in st.session_state.tok_log[-6:]
) if st.session_state.tok_log else "ยังไม่มีการใช้งาน"
st.markdown(f"""
<div style="border-top:1px solid #1e3a8a; margin-top:16px; padding-top:10px;
            display:flex; justify-content:space-between; align-items:center;">
  <span style="font-family:'VT323';font-size:.95rem;color:#475569;">{log_parts}</span>
  <span class="bigstat" style="font-size:.85rem;">
    🔢 {st.session_state.tok_total:,} tokens
  </span>
</div>
""", unsafe_allow_html=True)
