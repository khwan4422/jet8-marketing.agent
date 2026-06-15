# ============================================================
#  app.py — MARKETING OPS v2.0 🎮
#  Tab 1: CONTENT MISSION  — Research + Content Agent (เดิม)
#  Tab 2: NEWS PIPELINE    — News Scout + Market Analyst (ใหม่)
#  วิธีรัน:  streamlit run app.py
# ============================================================

import os
import streamlit as st
from datetime import datetime, timezone, timedelta

TH = timezone(timedelta(hours=7))

st.set_page_config(page_title="MARKETING OPS v2.0", page_icon="👾", layout="wide")

# ── ตั้งค่า Secrets → Environment Variables ──────────────────────────────────
# ทำก่อน import agent เพราะตอน import มันจะอ่าน env ทันที
try:
    for key in ("GEMINI_API_KEY", "SLACK_BOT_TOKEN", "SLACK_NEWS_CHANNEL_ID",
                "SLACK_USER_ID", "APP_PASSWORD"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass

# ── Import Agents ─────────────────────────────────────────────────────────────
import research_agent, agent
from research_agent import research
from agent import generate_content
import news_monitor
import marketing_researcher
from marketing_researcher import build_user_prompt, analyze_with_gemini

# ── Session State ─────────────────────────────────────────────────────────────
if "tok_total" not in st.session_state:
    st.session_state.tok_total = 0

# ════════════════════════════════════════════════════════════════════════════
#  CSS — ธีมพิกเซลเรโทร (เหมือนเดิม)
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&family=Kanit:wght@400;600&display=swap');

.stApp{
  background:
    linear-gradient(rgba(8,12,40,.96),rgba(8,12,40,.96)),
    repeating-linear-gradient(0deg, #0b1030 0 1px, transparent 1px 26px),
    repeating-linear-gradient(90deg, #0b1030 0 1px, transparent 1px 26px),
    #070a22;
  font-family:'Kanit',sans-serif;
}
.block-container{ padding-top:2rem; }
header[data-testid="stHeader"]{ display:none !important; }
[data-testid="stToolbar"]{ display:none !important; }
.stDeployButton{ display:none !important; }
#MainMenu{ visibility:hidden; }
footer{ visibility:hidden; }

/* แถบหัว */
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

/* แผงนีออน */
.panel{
  border:2px solid #3b82f6; border-radius:8px; background:#0a0f33;
  box-shadow:0 0 12px rgba(59,130,246,.3), inset 0 0 16px rgba(59,130,246,.08);
  padding:14px; height:100%;
}
.panel-title{ font-family:'Press Start 2P'; font-size:.7rem; color:#67e8f9;
  letter-spacing:1px; margin-bottom:14px; text-shadow:0 0 6px rgba(103,232,249,.7); }

/* แถว Agent */
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

.bigstat{ font-family:'Press Start 2P'; color:#a3e635; font-size:1.1rem;
  text-shadow:0 0 8px rgba(163,230,53,.7); }
.minor{ font-family:'VT323'; color:#67e8f9; font-size:1.2rem; }
.flow{ font-family:'Press Start 2P'; color:#22d3ee; font-size:.8rem; letter-spacing:2px; }

.statusbar{ display:flex; gap:10px; margin-top:14px; }
.statusbar .cell{ flex:1; text-align:center; }

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

/* Tab styling */
.stTabs [data-baseweb="tab-list"]{ background:#0a0f33; border-bottom:2px solid #3b82f6; gap:8px; }
.stTabs [data-baseweb="tab"]{
  font-family:'Press Start 2P'; font-size:.65rem; color:#64748b;
  background:#0b1240; border:2px solid #1e3a8a; border-radius:8px 8px 0 0;
  padding:10px 16px;
}
.stTabs [aria-selected="true"]{
  color:#22d3ee !important; border-color:#22d3ee !important;
  background:#0a1140 !important; text-shadow:0 0 6px rgba(34,211,238,.7);
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  ระบบล็อกรหัสผ่าน
# ════════════════════════════════════════════════════════════════════════════
def check_password():
    expected = None
    try:
        expected = st.secrets.get("APP_PASSWORD")
    except Exception:
        pass
    if not expected:
        expected = os.getenv("APP_PASSWORD")
    if not expected:
        return
    if st.session_state.get("authed"):
        return
    pwd = st.text_input("🔒 ใส่รหัสผ่านเพื่อเข้าใช้งาน", type="password")
    if pwd == "":
        st.stop()
    if pwd == expected:
        st.session_state.authed = True
        st.rerun()
    else:
        st.error("❌ รหัสผ่านไม่ถูกต้อง")
        st.stop()

check_password()


# ════════════════════════════════════════════════════════════════════════════
#  SVG ผี Pac-Man
# ════════════════════════════════════════════════════════════════════════════
def ghost(color, size=44):
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 36 34" shape-rendering="crispEdges">
      <path d="M3 17 a15 15 0 0 1 30 0 v15 l-5 -4 l-5 4 l-5 -4 l-5 4 l-5 -4 z"
            fill="{color}" stroke="#0a0f33" stroke-width="1"/>
      <rect x="9" y="11" width="7" height="9" rx="3.5" fill="#fff"/>
      <rect x="20" y="11" width="7" height="9" rx="3.5" fill="#fff"/>
      <rect x="12" y="14" width="4" height="4" fill="#1d4ed8"/>
      <rect x="23" y="14" width="4" height="4" fill="#1d4ed8"/>
    </svg>"""

def agent_row_html(member, status):
    stxt = {"idle": "[ STANDBY ]", "working": "[ WORKING ]", "done": "[ DONE ]"}[status]
    dot  = "on" if status in ("working", "done") else "off"
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
    </div>"""


# ════════════════════════════════════════════════════════════════════════════
#  แถบหัว (แสดงทุก Tab)
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <span class="ttl">▣ MARKETING OPS v2.0</span>
  <span class="clock">TIME {datetime.now(TH).strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  แท็บ
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["🎯  CONTENT MISSION", "📰  NEWS PIPELINE"])


# ────────────────────────────────────────────────────────────────────────────
#  TAB 1 — Content Mission (เดิม)
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    TEAM_CONTENT = [
        {"key": "research", "num": "01", "color": "#ef4444", "role": "RESEARCH", "name": "ฝ่ายวิจัยตลาด"},
        {"key": "content",  "num": "02", "color": "#f472b6", "role": "CONTENT",  "name": "ฝ่ายเขียนคอนเทนต์"},
        {"key": "report",   "num": "03", "color": "#fb923c", "role": "REPORT",   "name": "ฝ่ายเรียบเรียงรายงาน"},
    ]
    c_member = {m["key"]: m for m in TEAM_CONTENT}

    product = st.text_input("🎯 สินค้า/บริการที่อยากทำการตลาด",
                            placeholder="เช่น กาแฟดริปคั่วอ่อนสำหรับคนทำงานออฟฟิศ",
                            key="product_input")
    start_c = st.button("► START MISSION", type="primary", use_container_width=True, key="start_content")

    left_c, right_c = st.columns([1, 1.4])

    with left_c:
        st.markdown('<div class="panel"><div class="panel-title">▸ TEAM STATUS</div>', unsafe_allow_html=True)
        c_slots = {m["key"]: st.empty() for m in TEAM_CONTENT}
        for m in TEAM_CONTENT:
            c_slots[m["key"]].markdown(agent_row_html(m, "idle"), unsafe_allow_html=True)
        st.markdown(f'<div class="minor">AGENTS ONLINE &nbsp; {len(TEAM_CONTENT)}/{len(TEAM_CONTENT)}</div>', unsafe_allow_html=True)
        c_tok_slot = st.empty()
        c_tok_slot.markdown(f'<div class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</div></div>', unsafe_allow_html=True)

    with right_c:
        st.markdown('<div class="panel"><div class="panel-title">▸ OUTPUT CONSOLE</div>', unsafe_allow_html=True)
        c_output = st.container()
        c_output.markdown('<div class="minor">// ระบบพร้อมทำงาน — กด START MISSION เพื่อเริ่ม</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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

    if start_c:
        if not product.strip():
            st.warning("กรอกชื่อสินค้า/บริการก่อนนะคะ 🥰")
            st.stop()

        c_output.markdown('<div class="minor">// กำลังประมวลผล... ⏳</div>', unsafe_allow_html=True)

        c_slots["research"].markdown(agent_row_html(c_member["research"], "working"), unsafe_allow_html=True)
        market_info = research(f"ข้อมูลตลาด เทรนด์ กลุ่มเป้าหมาย และคู่แข่ง ของ: {product}")
        r_tok = research_agent.last_usage["total"]
        c_slots["research"].markdown(agent_row_html(c_member["research"], "done"), unsafe_allow_html=True)

        c_slots["content"].markdown(agent_row_html(c_member["content"], "working"), unsafe_allow_html=True)
        brief = (f'ช่วยเขียนโพสต์โซเชียลมีเดียโปรโมท "{product}" '
                 f'โดยใช้ข้อมูลตลาดนี้เป็นวัตถุดิบ:\n\n{market_info}')
        post = generate_content(brief)
        c_tok = agent.last_usage["total"]
        c_slots["content"].markdown(agent_row_html(c_member["content"], "done"), unsafe_allow_html=True)

        c_slots["report"].markdown(agent_row_html(c_member["report"], "working"), unsafe_allow_html=True)
        report = f"""# 📋 รายงานการตลาด: {product}
_สร้างโดยทีม Agent เมื่อ {datetime.now(TH).strftime('%d/%m/%Y %H:%M')}_

## 1. ข้อมูลตลาด (โดย Research Agent)
{market_info}

---

## 2. โพสต์พร้อมใช้ (โดย Content Agent)
{post}
"""
        c_slots["report"].markdown(agent_row_html(c_member["report"], "done"), unsafe_allow_html=True)

        run_total = r_tok + c_tok
        st.session_state.tok_total += run_total
        c_tok_slot.markdown(
            f'<div class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</div></div>',
            unsafe_allow_html=True)

        c_output.empty()
        with c_output:
            st.markdown('<div class="bigstat">✔ MISSION COMPLETE</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="minor">🔢 TOKENS รอบนี้ &nbsp; '
                f'Research {r_tok:,} + Content {c_tok:,} = <b>{run_total:,}</b> &nbsp;|&nbsp; '
                f'สะสม {st.session_state.tok_total:,}</div>',
                unsafe_allow_html=True)
            st.markdown(report)
            st.download_button(
                "⬇ DOWNLOAD REPORT (.md)",
                data=report,
                file_name=f"report_{datetime.now(TH).strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ────────────────────────────────────────────────────────────────────────────
#  TAB 2 — News Pipeline (ใหม่)
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    TEAM_NEWS = [
        {"key": "scout",   "num": "04", "color": "#38bdf8", "role": "NEWS SCOUT",  "name": "ฝ่ายสกรีนข่าว"},
        {"key": "analyst", "num": "05", "color": "#c084fc", "role": "ANALYST",     "name": "ฝ่ายวิจัยการตลาด"},
    ]
    n_member = {m["key"]: m for m in TEAM_NEWS}

    st.markdown("""
    <div class="panel" style="margin-bottom:14px; border-color:#38bdf8;">
      <div class="panel-title" style="color:#38bdf8;">▸ NEWS PIPELINE — นำเข้า-ส่งออก / Food / Pharma</div>
      <div class="minor">
        Agent 04 ดึงข่าวจาก 11 แหล่ง → กรอง keyword → Agent 05 ให้ Gemini วิเคราะห์
      </div>
    </div>
    """, unsafe_allow_html=True)

    start_n = st.button("► START NEWS PIPELINE", type="primary", use_container_width=True, key="start_news")

    left_n, right_n = st.columns([1, 1.4])

    with left_n:
        st.markdown('<div class="panel"><div class="panel-title" style="color:#38bdf8;">▸ NEWS TEAM</div>', unsafe_allow_html=True)
        n_slots = {m["key"]: st.empty() for m in TEAM_NEWS}
        for m in TEAM_NEWS:
            n_slots[m["key"]].markdown(agent_row_html(m, "idle"), unsafe_allow_html=True)

        slack_status = "🟢 SLACK ON" if os.getenv("SLACK_BOT_TOKEN") else "⚪ SLACK OFF"
        st.markdown(f"""
        <div class="minor" style="margin-top:8px;">{slack_status}</div>
        <div class="minor">SOURCES &nbsp; 11 FEEDS</div>
        </div>
        """, unsafe_allow_html=True)

    with right_n:
        st.markdown('<div class="panel"><div class="panel-title" style="color:#38bdf8;">▸ NEWS CONSOLE</div>', unsafe_allow_html=True)
        n_output = st.container()
        n_output.markdown('<div class="minor">// รอคำสั่ง — กด START NEWS PIPELINE เพื่อเริ่ม</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="panel" style="margin-top:14px; border-color:#38bdf8;">
      <div class="statusbar">
        <div class="cell"><div class="panel-title">SOURCES</div><div class="minor">🇹🇭 TH + 🌐 INT + 🍽️ F&P</div></div>
        <div class="cell"><div class="panel-title">FLOW</div><div class="flow">📡 → 🤖 → 📄</div></div>
        <div class="cell"><div class="panel-title">ENGINE</div><div class="minor">GEMINI 2.5</div></div>
        <div class="cell"><div class="panel-title">OUTPUT</div><div class="minor">REPORT .MD</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if start_n:
        n_output.markdown('<div class="minor">// กำลังดึงข่าว... ⏳</div>', unsafe_allow_html=True)

        # ── Agent 04: News Scout ──────────────────────────────────────────
        n_slots["scout"].markdown(agent_row_html(n_member["scout"], "working"), unsafe_allow_html=True)
        try:
            results_by_group, total_news = news_monitor.main()
        except Exception as e:
            n_output.error(f"❌ Agent 04 error: {e}")
            st.stop()
        n_slots["scout"].markdown(agent_row_html(n_member["scout"], "done"), unsafe_allow_html=True)

        if total_news == 0:
            n_output.empty()
            with n_output:
                st.markdown('<div class="bigstat" style="color:#fbbf24;">⚠ ไม่พบข่าวใหม่</div>', unsafe_allow_html=True)
                st.markdown('<div class="minor">ข่าวทั้งหมดเคยสแกนไปแล้วในรอบก่อน</div>', unsafe_allow_html=True)
        else:
            # ── Agent 05: Market Analyst ──────────────────────────────────
            n_slots["analyst"].markdown(agent_row_html(n_member["analyst"], "working"), unsafe_allow_html=True)
            try:
                user_prompt = build_user_prompt(results_by_group)
                analysis    = analyze_with_gemini(user_prompt)
                n_tok       = marketing_researcher.last_usage["total"]
            except Exception as e:
                n_output.error(f"❌ Agent 05 error: {e}")
                st.stop()
            n_slots["analyst"].markdown(agent_row_html(n_member["analyst"], "done"), unsafe_allow_html=True)

            # ── สร้างรายงาน ───────────────────────────────────────────────
            date_str = datetime.now(TH).strftime("%Y-%m-%d")
            report_md = f"""# รายงานวิจัยการตลาด — {date_str}

> **สร้างโดย:** Agent Pipeline (News Scout → Market Analyst)
> **ข้อมูลจาก:** {total_news} บทความ
> **บริษัท:** Jet8 Freight Forwarder

---

{analysis}

---
*สร้างอัตโนมัติโดย MARKETING OPS v2.0*
"""
            st.session_state.tok_total += n_tok

            n_output.empty()
            with n_output:
                st.markdown('<div class="bigstat">✔ PIPELINE COMPLETE</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="minor">📰 ข่าวใหม่ {total_news} รายการ &nbsp;|&nbsp; '
                    f'🔢 TOKENS {n_tok:,} &nbsp;|&nbsp; สะสม {st.session_state.tok_total:,}</div>',
                    unsafe_allow_html=True)
                st.markdown(report_md)
                st.download_button(
                    "⬇ DOWNLOAD REPORT (.md)",
                    data=report_md,
                    file_name=f"news_report_{date_str}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
