# ============================================================
#  MARKETING OPS v2.0 — Jet8 Social Media Team Dashboard
#  รันด้วย:  streamlit run app.py
#  6 แท็บ: Planner | Research | Documents | Events | Content | Review
# ============================================================

import os
import json
from datetime import datetime, timezone, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

TH = timezone(timedelta(hours=7))

# ── ตั้งค่าหน้า ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MARKETING OPS v2.0", page_icon="👾", layout="wide")

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

# ── CSS — ธีมนีออน Retro ─────────────────────────────────────────────────────
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
if "review_queue" not in st.session_state:
    st.session_state.review_queue = []   # content รอ review
if "tok_total" not in st.session_state:
    st.session_state.tok_total = 0

# ── Top Bar ───────────────────────────────────────────────────────────────────
now_th = datetime.now(TH)
st.markdown(f"""
<div class="topbar">
  <span class="ttl">▣ MARKETING OPS v2.0 — JET8</span>
  <span class="clock">{now_th.strftime('%d/%m/%Y %H:%M')}</span>
</div>
""", unsafe_allow_html=True)

# ── Helper ───────────────────────────────────────────────────────────────────
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
                    st.info(f"🗓️ พบ {len(month_events)} อีเวนต์ในเดือนนี้ จะนำไปประกอบแผนด้วย")

            gen_btn = st.button("► สร้างแผน", use_container_width=True)

        with col2:
            if gen_btn:
                with st.spinner("🤔 กำลังวางแผน..."):
                    plan = planner_agent.generate_plan(
                        month=sel_month, year=sel_year,
                        focus=focus_text, events=month_events or None,
                    )
                st.session_state.tok_total += planner_agent.last_usage["total"]
                st.markdown(plan)
                st.download_button("⬇ ดาวน์โหลดแผน (.md)", data=plan,
                    file_name=f"plan_{sel_year}_{sel_month:02d}.md", mime="text/markdown",
                    use_container_width=True)
                st.markdown(f'<div class="minor">🔢 Tokens: {planner_agent.last_usage["total"]:,}</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown('<div class="minor">// เลือกเดือน แล้วกด "สร้างแผน"</div>',
                    unsafe_allow_html=True)


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
            if st.button("► ดึงข่าว (News Monitor)", use_container_width=True):
                with st.spinner("📡 กำลังดึงข่าว..."):
                    results, total = news_monitor.main()
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
            if st.button("► วิเคราะห์ข่าว (Research Analyst)", use_container_width=True):
                with st.spinner("🧠 กำลังวิเคราะห์..."):
                    filepath = marketing_researcher.main()
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
            if fetch_btn:
                if search_kw.strip():
                    # ค้นหาทุกช่องทาง
                    with st.spinner("🔄 กำลังค้นหา..."):
                        for key, ch in document_researcher.get_channels().items():
                            results = document_researcher.search_in_channel(key, search_kw.strip())
                            st.markdown(f'**{ch["label"]}** — ผลการค้นหา "{search_kw}"')
                            _render_tasks(results)
                else:
                    # ดึงทั้ง 3 ช่อง
                    with st.spinner("🔄 กำลังดึงข้อมูล..."):
                        all_data = document_researcher.fetch_all_channels(days=days_back)
                    for key, ch in document_researcher.get_channels().items():
                        tasks = all_data.get(key, [])
                        real = [t for t in tasks if "error" not in t]
                        st.markdown(f'**{ch["label"]}** — {len(real)} รายการใน {days_back} วัน')
                        _render_tasks(tasks)
            else:
                st.markdown('<div class="minor">// กดปุ่มเพื่อดึงข้อมูลจาก ClickUp</div>',
                    unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  TAB 4 — EVENTS
# ════════════════════════════════════════════════════════════════
with t4:
    st.markdown('<div class="panel-title">🗓️ ติดตามอีเวนต์ที่สนใจ</div>', unsafe_allow_html=True)
    st.markdown('<div class="warn">⚙️ Google Calendar integration: coming soon</div>',
        unsafe_allow_html=True)

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
                        st.rerun()


# ════════════════════════════════════════════════════════════════
#  TAB 5 — CONTENT
# ════════════════════════════════════════════════════════════════
with t5:
    st.markdown('<div class="panel-title">✍️ เขียนคอนเทนต์การตลาด</div>', unsafe_allow_html=True)

    if not CONTENT_OK:
        st.error("❌ ไม่พบ agent.py")
    else:
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
            content_request = st.text_area("โจทย์ที่ต้องการ *",
                placeholder="เช่น เขียนโพสต์อธิบายกระบวนการนำเข้ายาสำหรับ SME", height=120)
            post_slack  = st.checkbox("ส่งไป Slack หลังเขียนเสร็จ", value=False)
            gen_btn_c   = st.button("► เขียนคอนเทนต์", use_container_width=True)

        with col2:
            if gen_btn_c:
                if not content_request.strip():
                    st.warning("กรุณาใส่โจทย์ก่อน")
                else:
                    with st.spinner("✍️ กำลังเขียน..."):
                        result = content_agent.generate_content(
                            content_request, content_type=ctype, post_to_slack=post_slack)
                    st.session_state.tok_total += content_agent.last_usage["total"]
                    st.markdown(result)
                    st.markdown(f'<div class="minor">🔢 Tokens: {content_agent.last_usage["total"]:,}</div>',
                        unsafe_allow_html=True)

                    if st.button("📨 ส่งให้ Reviewer ตรวจ", use_container_width=True):
                        st.session_state.review_queue.append({
                            "type":     ctype_label,
                            "request":  content_request,
                            "content":  result,
                            "added_at": now_th.strftime("%H:%M"),
                        })
                        st.success("✅ ส่งไปแท็บ ✅ Review แล้ว!")
            else:
                st.markdown('<div class="minor">// ใส่โจทย์ทางซ้าย แล้วกด "เขียนคอนเทนต์"</div>',
                    unsafe_allow_html=True)


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
                        if st.button("🤖 ให้ AI ตรวจ (Supervisor)", key=f"ai_{i}",
                                     use_container_width=True):
                            with st.spinner("🔍 กำลังตรวจ..."):
                                qc = supervisor_agent.review(item["content"], "content")
                            st.session_state.tok_total += supervisor_agent.last_usage["total"]
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
st.markdown(f"""
<div style="border-top:1px solid #1e3a8a; margin-top:16px; padding-top:10px; text-align:right;">
  <span class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</span>
</div>
""", unsafe_allow_html=True)
