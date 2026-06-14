# ============================================================
#  app.py — MARKETING OPS v1.0 🎮 (ธีมเกมพิกเซล + ผี Pac-Man)
#  แดชบอร์ดจอควบคุม แสดงทีม Agent เป็นผี Pac-Man สีต่างๆ
#  วิธีรัน:  streamlit run app.py
#  ต้องอยู่โฟลเดอร์เดียวกับ agent.py + research_agent.py + .env
# ============================================================

import os
import streamlit as st
from datetime import datetime, timezone, timedelta

# โซนเวลาไทย (UTC+7) — บังคับใช้เวลาไทยเสมอ แม้เซิร์ฟเวอร์คลาวด์จะอยู่ต่างประเทศ
TH = timezone(timedelta(hours=7))

st.set_page_config(page_title="MARKETING OPS v1.0", page_icon="👾", layout="wide")

# --- กุญแจ API ---
# ตอนรันในเครื่อง: อ่านจากไฟล์ .env (เหมือนเดิม)
# ตอน deploy บนคลาวด์: อ่านจาก Streamlit Secrets แล้วตั้งเป็น env var ให้ agent ใช้ได้
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# นำเข้า Agent (ต้องอยู่หลังตั้งกุญแจ เพราะตอนนำเข้ามันจะอ่านกุญแจทันที)
import research_agent, agent
from research_agent import research
from agent import generate_content

# ตัวนับโทเคนสะสมตลอด session (ไม่รีเซ็ตจนกว่าจะปิดเว็บ)
if "tok_total" not in st.session_state:
    st.session_state.tok_total = 0

# ---------- ธีมเกมพิกเซลเรโทร (จอควบคุมนีออน) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Kanit:wght@400;600&display=swap');

/* พื้นหลังจอเข้ม + เส้นกริด */
.stApp{
  background:
    linear-gradient(rgba(8,12,40,.96),rgba(8,12,40,.96)),
    repeating-linear-gradient(0deg, #0b1030 0 1px, transparent 1px 26px),
    repeating-linear-gradient(90deg, #0b1030 0 1px, transparent 1px 26px),
    #070a22;
  font-family:'Kanit',sans-serif;
}
.block-container{ padding-top:2rem; }

/* ซ่อนแถบเครื่องมือ Streamlit (ปุ่ม Deploy + เมนู) ให้เห็น UI เต็มจอ */
header[data-testid="stHeader"]{ display:none !important; }
[data-testid="stToolbar"]{ display:none !important; }
.stDeployButton{ display:none !important; }
#MainMenu{ visibility:hidden; }
footer{ visibility:hidden; }

/* แถบหัวบนสุด */
.topbar{
  display:flex; justify-content:space-between; align-items:center;
  border:2px solid #22d3ee; border-radius:8px; padding:10px 18px;
  background:#0a1140; box-shadow:0 0 14px rgba(34,211,238,.35), inset 0 0 18px rgba(34,211,238,.12);
  margin-bottom:14px;
}
.topbar .ttl{ font-family:'Press Start 2P'; color:#22d3ee; font-size:.95rem; letter-spacing:1px;
  text-shadow:0 0 8px rgba(34,211,238,.8); }
.topbar .clock{ font-family:'Press Start 2P'; color:#a3e635; font-size:.85rem;
  border:2px solid #a3e635; border-radius:6px; padding:5px 10px; text-shadow:0 0 8px rgba(163,230,53,.7); }

/* แผงนีออนทั่วไป */
.panel{
  border:2px solid #3b82f6; border-radius:8px; background:#0a0f33;
  box-shadow:0 0 12px rgba(59,130,246,.3), inset 0 0 16px rgba(59,130,246,.08);
  padding:14px; height:100%;
}
.panel-title{ font-family:'Press Start 2P'; font-size:.7rem; color:#67e8f9;
  letter-spacing:1px; margin-bottom:14px; text-shadow:0 0 6px rgba(103,232,249,.7); }

/* แถวพนักงาน (ผี) ใน TEAM STATUS */
.agent-row{
  display:flex; align-items:center; gap:12px; padding:10px;
  border:2px solid #1e3a8a; border-radius:8px; margin-bottom:12px; background:#0b1240;
}
.agent-row.working{ border-color:#a3e635; box-shadow:0 0 12px rgba(163,230,53,.45); }
.agent-row.done{ border-color:#22d3ee; }
.agent-row .num{ font-family:'Press Start 2P'; font-size:.62rem; color:#fbbf24; }
.agent-row .ghost{ animation:float 2.2s ease-in-out infinite; }
.agent-row.working .ghost{ animation:bob .5s ease-in-out infinite; }
.agent-row .info{ flex:1; line-height:1.25; }
.agent-row .role{ font-family:'Press Start 2P'; font-size:.6rem; color:#e0e7ff; }
.agent-row .name{ color:#7c8cc4; font-size:.82rem; }
.agent-row .stat{ font-family:'VT323'; font-size:1.15rem; letter-spacing:1px; }
.stat.idle{ color:#64748b; } .stat.working{ color:#a3e635; } .stat.done{ color:#22d3ee; }
.dot{ width:14px; height:14px; border-radius:50%; }
.dot.on{ background:#22c55e; box-shadow:0 0 10px #22c55e; animation:blink 1.1s infinite; }
.dot.off{ background:#334155; }

@keyframes float{ 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }
@keyframes bob{ 0%,100%{transform:translateY(0)} 50%{transform:translateY(-7px)} }
@keyframes blink{ 0%,100%{opacity:1} 50%{opacity:.35} }

/* ป้ายในแผงกลาง */
.bigstat{ font-family:'Press Start 2P'; color:#a3e635; font-size:1.1rem;
  text-shadow:0 0 8px rgba(163,230,53,.7); }
.minor{ font-family:'VT323'; color:#67e8f9; font-size:1.2rem; }
.flow{ font-family:'Press Start 2P'; color:#22d3ee; font-size:.8rem; letter-spacing:2px; }

/* แถบสถานะล่าง */
.statusbar{ display:flex; gap:10px; margin-top:14px; }
.statusbar .cell{ flex:1; text-align:center; }

/* ปุ่ม + ช่องกรอก ให้เข้าธีม */
.stButton>button{
  background:#0a1140; color:#22d3ee; border:2px solid #22d3ee; border-radius:8px;
  font-family:'Press Start 2P'; font-size:.7rem; padding:14px 0; letter-spacing:1px;
  box-shadow:0 0 12px rgba(34,211,238,.4); text-shadow:0 0 6px rgba(34,211,238,.8);
}
.stButton>button:hover{ background:#22d3ee; color:#07122e; }
.stTextInput>div>div>input{ background:#0b1240; color:#e0e7ff; border:2px solid #3b82f6;
  border-radius:8px; font-family:'Kanit'; }
.stTextInput label{ color:#67e8f9 !important; font-weight:600; }
h1,h2,h3,p,.stMarkdown{ color:#dbe4ff; }
</style>
""", unsafe_allow_html=True)


# ---------- ฟังก์ชันวาดผี Pac-Man (SVG) ----------
def ghost(color, size=44):
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 36 34" shape-rendering="crispEdges">
      <path d="M3 17 a15 15 0 0 1 30 0 v15 l-5 -4 l-5 4 l-5 -4 l-5 4 l-5 -4 z"
            fill="{color}" stroke="#0a0f33" stroke-width="1"/>
      <rect x="9" y="11" width="7" height="9" rx="3.5" fill="#fff"/>
      <rect x="20" y="11" width="7" height="9" rx="3.5" fill="#fff"/>
      <rect x="12" y="14" width="4" height="4" fill="#1d4ed8"/>
      <rect x="23" y="14" width="4" height="4" fill="#1d4ed8"/>
    </svg>"""


# ---------- ข้อมูลทีม (ผีแต่ละสี) ----------
TEAM = [
    {"key": "research", "num": "01", "color": "#ef4444", "role": "RESEARCH", "name": "ฝ่ายวิจัยตลาด"},
    {"key": "content",  "num": "02", "color": "#f472b6", "role": "CONTENT",  "name": "ฝ่ายเขียนคอนเทนต์"},
    {"key": "report",   "num": "03", "color": "#fb923c", "role": "REPORT",   "name": "ฝ่ายเรียบเรียงรายงาน"},
]
member_by_key = {m["key"]: m for m in TEAM}

def agent_row(member, status):
    stxt = {"idle": "[ STANDBY ]", "working": "[ WORKING ]", "done": "[ DONE ]"}[status]
    dot = "on" if status in ("working", "done") else "off"
    rowcls = status if status in ("working", "done") else ""
    return f"""
    <div class="agent-row {rowcls}">
      <span class="num">{member['num']}</span>
      <span class="ghost">{ghost(member['color'])}</span>
      <span class="info">
        <span class="role">{member['role']}</span><br>
        <span class="name">{member['name']}</span><br>
        <span class="stat {status}">{stxt}</span>
      </span>
      <span class="dot {dot}"></span>
    </div>
    """

# ---------- แถบหัว ----------
st.markdown(f"""
<div class="topbar">
  <span class="ttl">▣ MARKETING OPS v1.0</span>
  <span class="clock">TIME {datetime.now(TH).strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)

# ---------- ช่องสั่งงาน ----------
product = st.text_input("🎯 สินค้า/บริการที่อยากทำการตลาด",
                        placeholder="เช่น กาแฟดริปคั่วอ่อนสำหรับคนทำงานออฟฟิศ")
start = st.button("► START MISSION", type="primary", use_container_width=True)

# ---------- เลย์เอาต์หลัก: ซ้าย = ทีม / ขวา = จอผลงาน ----------
left, right = st.columns([1, 1.4])

with left:
    st.markdown('<div class="panel"><div class="panel-title">▸ TEAM STATUS</div>', unsafe_allow_html=True)
    slots = {m["key"]: st.empty() for m in TEAM}
    for m in TEAM:
        slots[m["key"]].markdown(agent_row(m, "idle"), unsafe_allow_html=True)
    st.markdown(f'<div class="minor">AGENTS ONLINE &nbsp; {len(TEAM)}/{len(TEAM)}</div>', unsafe_allow_html=True)
    tok_slot = st.empty()       # ที่แสดงโทเคนสะสม (อัปเดตได้)
    tok_slot.markdown(f'<div class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</div></div>',
                      unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">▸ OUTPUT CONSOLE</div>', unsafe_allow_html=True)
    output_box = st.container()
    output_box.markdown('<div class="minor">// ระบบพร้อมทำงาน — กด START MISSION เพื่อเริ่ม</div>',
                        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def set_status(key, status):
    slots[key].markdown(agent_row(member_by_key[key], status), unsafe_allow_html=True)

# ---------- แถบสถานะล่าง ----------
st.markdown(f"""
<div class="panel" style="margin-top:14px;">
  <div class="statusbar">
    <div class="cell"><div class="panel-title">SYSTEM</div><div class="minor">▮▮▮▮▮▮▮▮ OK</div></div>
    <div class="cell"><div class="panel-title">FLOW</div><div class="flow">✉ → 📄 → 📊</div></div>
    <div class="cell"><div class="panel-title">ENGINE</div><div class="minor">GEMINI 2.5</div></div>
    <div class="cell"><div class="panel-title">SECURE</div><div class="minor">🔒 LOCKED</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- เมื่อกดเริ่ม ----------
if start:
    if not product.strip():
        st.warning("กรอกชื่อสินค้า/บริการก่อนนะคะ 🥰")
        st.stop()

    output_box.markdown('<div class="minor">// กำลังประมวลผล... ⏳</div>', unsafe_allow_html=True)

    set_status("research", "working")
    market_info = research(f"ข้อมูลตลาด เทรนด์ กลุ่มเป้าหมาย และคู่แข่ง ของ: {product}")
    r_tok = research_agent.last_usage["total"]        # โทเคนที่ Research ใช้
    set_status("research", "done")

    set_status("content", "working")
    brief = (f'ช่วยเขียนโพสต์โซเชียลมีเดียโปรโมท "{product}" '
             f'โดยใช้ข้อมูลตลาดนี้เป็นวัตถุดิบ:\n\n{market_info}')
    post = generate_content(brief)
    c_tok = agent.last_usage["total"]                 # โทเคนที่ Content ใช้
    set_status("content", "done")

    set_status("report", "working")
    report = f"""# 📋 รายงานการตลาด: {product}
_สร้างโดยทีม Agent เมื่อ {datetime.now(TH).strftime('%d/%m/%Y %H:%M')}_

## 1. ข้อมูลตลาด (โดย Research Agent)

{market_info}

---

## 2. โพสต์พร้อมใช้ (โดย Content Agent)

{post}
"""
    set_status("report", "done")

    # --- รวมโทเคน + อัปเดตยอดสะสม ---
    run_total = r_tok + c_tok                          # Report เป็นการจัดข้อความ ไม่ใช้ AI = 0 โทเคน
    st.session_state.tok_total += run_total
    tok_slot.markdown(
        f'<div class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</div></div>',
        unsafe_allow_html=True)

    # แสดงผลในจอ OUTPUT CONSOLE
    output_box.empty()
    with output_box:
        st.markdown('<div class="bigstat">✔ MISSION COMPLETE</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="minor">🔢 TOKENS รอบนี้ &nbsp; '
            f'Research {r_tok:,} + Content {c_tok:,} = <b>{run_total:,}</b> &nbsp;|&nbsp; '
            f'สะสมทั้งหมด {st.session_state.tok_total:,}</div>',
            unsafe_allow_html=True)
        st.markdown(report)
        st.download_button(
            "⬇ DOWNLOAD REPORT (.md)",
            data=report,
            file_name=f"report_{datetime.now(TH).strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
