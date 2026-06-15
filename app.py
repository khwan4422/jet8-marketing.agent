# ============================================================
#  app.py — MARKETING OPS v2.0 🎮
#  Tab 1: CONTENT MISSION  — Research + Content Agent
#  Tab 2: NEWS PIPELINE    — News Scout → Analyst → Content Writer
#  วิธีรัน:  streamlit run app.py
# ============================================================

import os
import streamlit as st
from datetime import datetime, timezone, timedelta

TH = timezone(timedelta(hours=7))

st.set_page_config(page_title="MARKETING OPS v2.0", page_icon="👾", layout="wide")

# ── Secrets → Environment Variables (ต้องทำก่อน import agents) ──────────────
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
for key, default in [
    ("tok_total", 0),
    ("news_analysis", ""),   # เก็บ analysis ไว้ใช้ใน Content Bridge
    ("news_total", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ════════════════════════════════════════════════════════════════════════════
#  CSS — ธีมพิกเซลเรโทร
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

.panel{
  border:2px solid #3b82f6; border-radius:8px; background:#0a0f33;
  box-shadow:0 0 12px rgba(59,130,246,.3), inset 0 0 16px rgba(59,130,246,.08);
  padding:14px; height:100%;
}
.panel-title{ font-family:'Press Start 2P'; font-size:.7rem; color:#67e8f9;
  letter-spacing:1px; margin-bottom:14px; text-shadow:0 0 6px rgba(103,232,249,.7); }

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
.bridge-title{ font-family:'Press Start 2P'; font-size:.75rem; color:#a3e635;
  letter-spacing:1px; text-shadow:0 0 6px rgba(163,230,53,.7); }

.statusbar{ display:flex; gap:10px; margin-top:14px; }
.statusbar .cell{ flex:1; text-align:center; }

.stButton>button{
  background:#0a1140; color:#22d3ee; border:2px solid #22d3ee; border-radius:8px;
  font-family:'Press Start 2P'; font-size:.7rem; padding:14px 0; letter-spacing:1px;
  box-shadow:0 0 12px rgba(34,211,238,.4); text-shadow:0 0 6px rgba(34,211,238,.8);
}
.stButton>button:hover{ background:#22d3ee; color:#07122e; }
.stTextInput>div>div>input, .stTextArea textarea{
  background:#0b1240; color:#e0e7ff; border:2px solid #3b82f6; border-radius:8px; font-family:'Kanit';
}
.stTextInput label, .stTextArea label{ color:#67e8f9 !important; font-weight:600; }
.stSelectbox>div>div{ background:#0b1240; color:#e0e7ff; border:2px solid #3b82f6; border-radius:8px; }
.stSelectbox label{ color:#67e8f9 !important; font-weight:600; }
h1,h2,h3,p,.stMarkdown{ color:#dbe4ff; }

.stTabs [data-baseweb="tab-list"]{ background:#0a0f33; border-bottom:2px solid #3b82f6; gap:8px; }
.stTabs [data-baseweb="tab"]{
  font-family:'Press Start 2P'; font-size:.65rem; color:#64748b;
  background:#0b1240; border:2px solid #1e3a8a; border-radius:8px 8px 0 0; padding:10px 16px;
}
.stTabs [aria-selected="true"]{
  color:#22d3ee !important; border-color:#22d3ee !important;
  background:#0a1140 !important; text-shadow:0 0 6px rgba(34,211,238,.7);
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
#  ล็อกรหัสผ่าน
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
#  แถบหัว
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="topbar">
  <span class="ttl">▣ MARKETING OPS v2.0</span>
  <span class="clock">TIME {datetime.now(TH).strftime('%H:%M')}</span>
</div>
""", unsafe_allow_html=True)


tab1, tab2 = st.tabs(["🎯  CONTENT MISSION", "📰  NEWS PIPELINE"])


# ════════════════════════════════════════════════════════════════════════════
#  TAB 1 — Content Mission
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    TEAM_C = [
        {"key": "research", "num": "01", "color": "#ef4444", "role": "RESEARCH", "name": "ฝ่ายวิจัยตลาด"},
        {"key": "content",  "num": "02", "color": "#f472b6", "role": "CONTENT",  "name": "ฝ่ายเขียนคอนเทนต์"},
        {"key": "report",   "num": "03", "color": "#fb923c", "role": "REPORT",   "name": "ฝ่ายเรียบเรียงรายงาน"},
    ]
    cm = {m["key"]: m for m in TEAM_C}

    product = st.text_input("🎯 สินค้า/บริการที่อยากทำการตลาด",
                            placeholder="เช่น กาแฟดริปคั่วอ่อนสำหรับคนทำงานออฟฟิศ",
                            key="product_input")
    start_c = st.button("► START MISSION", type="primary", use_container_width=True, key="start_content")

    lc, rc = st.columns([1, 1.4])

    with lc:
        st.markdown('<div class="panel"><div class="panel-title">▸ TEAM STATUS</div>', unsafe_allow_html=True)
        cs = {m["key"]: st.empty() for m in TEAM_C}
        for m in TEAM_C:
            cs[m["key"]].markdown(agent_row_html(m, "idle"), unsafe_allow_html=True)
        st.markdown(f'<div class="minor">AGENTS ONLINE &nbsp; {len(TEAM_C)}/{len(TEAM_C)}</div>', unsafe_allow_html=True)
        c_tok = st.empty()
        c_tok.markdown(f'<div class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</div></div>', unsafe_allow_html=True)

    with rc:
        st.markdown('<div class="panel"><div class="panel-title">▸ OUTPUT CONSOLE</div>', unsafe_allow_html=True)
        c_out = st.container()
        c_out.markdown('<div class="minor">// ระบบพร้อมทำงาน — กด START MISSION เพื่อเริ่ม</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="panel" style="margin-top:14px;"><div class="statusbar">
      <div class="cell"><div class="panel-title">SYSTEM</div><div class="minor">▮▮▮▮▮▮▮▮ OK</div></div>
      <div class="cell"><div class="panel-title">FLOW</div><div class="flow">✉ → 📄 → 📊</div></div>
      <div class="cell"><div class="panel-title">ENGINE</div><div class="minor">GEMINI 2.5</div></div>
      <div class="cell"><div class="panel-title">SECURE</div><div class="minor">🔒 LOCKED</div></div>
    </div></div>""", unsafe_allow_html=True)

    if start_c:
        if not product.strip():
            st.warning("กรอกชื่อสินค้า/บริการก่อนนะคะ 🥰")
            st.stop()

        c_out.markdown('<div class="minor">// กำลังประมวลผล... ⏳</div>', unsafe_allow_html=True)

        cs["research"].markdown(agent_row_html(cm["research"], "working"), unsafe_allow_html=True)
        market_info = research(f"ข้อมูลตลาด เทรนด์ กลุ่มเป้าหมาย และคู่แข่ง ของ: {product}")
        r_tok = research_agent.last_usage["total"]
        cs["research"].markdown(agent_row_html(cm["research"], "done"), unsafe_allow_html=True)

        cs["content"].markdown(agent_row_html(cm["content"], "working"), unsafe_allow_html=True)
        brief = f'เขียนโพสต์โซเชียลมีเดียโปรโมท "{product}" จากข้อมูลตลาดนี้:\n\n{market_info}'
        post = generate_content(brief)
        ct_tok = agent.last_usage["total"]
        cs["content"].markdown(agent_row_html(cm["content"], "done"), unsafe_allow_html=True)

        cs["report"].markdown(agent_row_html(cm["report"], "working"), unsafe_allow_html=True)
        report = f"""# 📋 รายงานการตลาด: {product}
_สร้างโดยทีม Agent เมื่อ {datetime.now(TH).strftime('%d/%m/%Y %H:%M')}_

## 1. ข้อมูลตลาด (โดย Research Agent)
{market_info}

---

## 2. โพสต์พร้อมใช้ (โดย Content Agent)
{post}
"""
        cs["report"].markdown(agent_row_html(cm["report"], "done"), unsafe_allow_html=True)

        run_total = r_tok + ct_tok
        st.session_state.tok_total += run_total
        c_tok.markdown(f'<div class="minor">TOKENS (SESSION) &nbsp; {st.session_state.tok_total:,}</div></div>', unsafe_allow_html=True)

        c_out.empty()
        with c_out:
            st.markdown('<div class="bigstat">✔ MISSION COMPLETE</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="minor">🔢 Research {r_tok:,} + Content {ct_tok:,} = <b>{run_total:,}</b> &nbsp;|&nbsp; สะสม {st.session_state.tok_total:,}</div>', unsafe_allow_html=True)
            st.markdown(report)
            st.download_button("⬇ DOWNLOAD REPORT (.md)", data=report,
                               file_name=f"report_{datetime.now(TH).strftime('%Y%m%d_%H%M')}.md",
                               mime="text/markdown", use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
#  TAB 2 — News Pipeline + Content Bridge
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    TEAM_N = [
        {"key": "scout",   "num": "04", "color": "#38bdf8", "role": "NEWS SCOUT", "name": "ฝ่ายสกรีนข่าว"},
        {"key": "analyst", "num": "05", "color": "#c084fc", "role": "ANALYST",    "name": "ฝ่ายวิจัยการตลาด"},
        {"key": "writer",  "num": "06", "color": "#f472b6", "role": "CONTENT",    "name": "ฝ่ายเขียนคอนเทนต์"},
    ]
    nm = {m["key"]: m for m in TEAM_N}

    st.markdown("""
    <div class="panel" style="margin-bottom:14px; border-color:#38bdf8;">
      <div class="panel-title" style="color:#38bdf8;">▸ NEWS PIPELINE — นำเข้า-ส่งออก / Food / Pharma</div>
      <div class="minor">Agent 04 ดึงข่าว 11 แหล่ง → Agent 05 วิเคราะห์ด้วย Gemini → Agent 06 เขียน Content</div>
    </div>
    """, unsafe_allow_html=True)

    start_n = st.button("► START NEWS PIPELINE", type="primary", use_container_width=True, key="start_news")

    ln, rn = st.columns([1, 1.4])

    with ln:
        st.markdown('<div class="panel"><div class="panel-title" style="color:#38bdf8;">▸ NEWS TEAM</div>', unsafe_allow_html=True)
        ns = {m["key"]: st.empty() for m in TEAM_N}
        for m in TEAM_N:
            ns[m["key"]].markdown(agent_row_html(m, "idle"), unsafe_allow_html=True)
        slack_txt = "🟢 SLACK ON" if os.getenv("SLACK_BOT_TOKEN") else "⚪ SLACK OFF"
        st.markdown(f'<div class="minor" style="margin-top:8px;">{slack_txt}</div><div class="minor">SOURCES &nbsp; 11 FEEDS</div></div>', unsafe_allow_html=True)

    with rn:
        st.markdown('<div class="panel"><div class="panel-title" style="color:#38bdf8;">▸ NEWS CONSOLE</div>', unsafe_allow_html=True)
        n_out = st.container()
        n_out.markdown('<div class="minor">// รอคำสั่ง — กด START NEWS PIPELINE เพื่อเริ่ม</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="panel" style="margin-top:14px; border-color:#38bdf8;"><div class="statusbar">
      <div class="cell"><div class="panel-title">SOURCES</div><div class="minor">🇹🇭 TH + 🌐 INT + 🍽️ F&P</div></div>
      <div class="cell"><div class="panel-title">FLOW</div><div class="flow">📡 → 🤖 → ✍️</div></div>
      <div class="cell"><div class="panel-title">ENGINE</div><div class="minor">GEMINI 2.5</div></div>
      <div class="cell"><div class="panel-title">OUTPUT</div><div class="minor">REPORT + POST</div></div>
    </div></div>""", unsafe_allow_html=True)

    # ── รัน Pipeline ─────────────────────────────────────────────────────────
    if start_n:
        n_out.markdown('<div class="minor">// กำลังดึงข่าว... ⏳</div>', unsafe_allow_html=True)

        ns["scout"].markdown(agent_row_html(nm["scout"], "working"), unsafe_allow_html=True)
        try:
            results_by_group, total_news = news_monitor.main()
        except Exception as e:
            n_out.error(f"❌ Agent 04 error: {e}")
            st.stop()
        ns["scout"].markdown(agent_row_html(nm["scout"], "done"), unsafe_allow_html=True)

        if total_news == 0:
            n_out.empty()
            with n_out:
                st.markdown('<div class="bigstat" style="color:#fbbf24;">⚠ ไม่พบข่าวใหม่</div>', unsafe_allow_html=True)
                st.markdown('<div class="minor">ข่าวทั้งหมดเคยสแกนไปแล้วในรอบก่อน</div>', unsafe_allow_html=True)
        else:
            ns["analyst"].markdown(agent_row_html(nm["analyst"], "working"), unsafe_allow_html=True)
            try:
                user_prompt = build_user_prompt(results_by_group)
                analysis    = analyze_with_gemini(user_prompt)
                n_tok       = marketing_researcher.last_usage["total"]
            except Exception as e:
                n_out.error(f"❌ Agent 05 error: {e}")
                st.stop()
            ns["analyst"].markdown(agent_row_html(nm["analyst"], "done"), unsafe_allow_html=True)

            # บันทึกไว้ใน session_state เพื่อใช้ใน Content Bridge
            st.session_state.news_analysis = analysis
            st.session_state.news_total    = total_news
            st.session_state.tok_total    += n_tok

            date_str  = datetime.now(TH).strftime("%Y-%m-%d")
            report_md = f"""# รายงานวิจัยการตลาด — {date_str}

> **สร้างโดย:** Agent Pipeline (News Scout → Market Analyst)
> **ข้อมูลจาก:** {total_news} บทความ | **บริษัท:** Jet8 Freight Forwarder

---

{analysis}

---
*สร้างอัตโนมัติโดย MARKETING OPS v2.0*
"""
            n_out.empty()
            with n_out:
                st.markdown('<div class="bigstat">✔ PIPELINE COMPLETE</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="minor">📰 ข่าวใหม่ {total_news} รายการ &nbsp;|&nbsp; 🔢 TOKENS {n_tok:,} &nbsp;|&nbsp; สะสม {st.session_state.tok_total:,}</div>', unsafe_allow_html=True)
                st.markdown(report_md)
                st.download_button("⬇ DOWNLOAD REPORT (.md)", data=report_md,
                                   file_name=f"news_report_{date_str}.md",
                                   mime="text/markdown", use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    #  CONTENT BRIDGE — แสดงเมื่อมี analysis อยู่ใน session_state
    #  (ยังคงอยู่แม้กด START NEWS PIPELINE ใหม่หรือ rerun)
    # ════════════════════════════════════════════════════════════════════════
    if st.session_state.news_analysis:
        st.markdown("""
        <div style="margin-top:24px;">
          <div class="bridge-title">▸ CONTENT BRIDGE — เปลี่ยนข่าวเป็น Content</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="panel" style="border-color:#a3e635; margin-top:10px;">
          <div class="panel-title" style="color:#a3e635;">⚡ ส่งต่อข้อมูลจากข่าวไปให้ Agent 06 เขียน Content</div>
          <div class="minor">เลือก platform + ปรับ brief แล้วกด GENERATE</div>
        </div>
        """, unsafe_allow_html=True)

        # ── เปิดดู Analysis ──────────────────────────────────────────────────
        with st.expander("📊 ดู Analysis จาก Agent 05 (คลิกเพื่อขยาย)"):
            st.markdown(st.session_state.news_analysis)

        # ── ตัวเลือก Platform + Content Type ─────────────────────────────────
        col_p, col_t = st.columns(2)
        with col_p:
            platform = st.selectbox(
                "🌐 Platform",
                ["Facebook", "LinkedIn", "Instagram", "เว็บไซต์ (บทความ)", "Line Official"],
                key="bridge_platform"
            )
        with col_t:
            content_type = st.selectbox(
                "📝 ประเภท Content",
                ["โพสต์สั้น (Caption)", "บทความเต็ม (Long-form)", "Infographic Script",
                 "Newsletter", "ประชาสัมพันธ์บริษัท"],
                key="bridge_type"
            )

        # ── Brief ที่ปรับได้ ──────────────────────────────────────────────────
        # ดึง ~400 ตัวอักษรแรกของ analysis มาเป็นตัวอย่างให้แก้
        analysis_preview = st.session_state.news_analysis[:400].rsplit("\n", 1)[0]
        default_brief = (
            f"บริษัท Jet8 — Freight Forwarder นำเข้า-ส่งออกอาหารและยาในไทย\n\n"
            f"ประเด็นจากข่าวสัปดาห์นี้ที่อยากสื่อสาร:\n{analysis_preview}...\n\n"
            f"โจทย์: เขียน{content_type} สำหรับ {platform} ให้ตรงกลุ่มเป้าหมาย "
            f"(ผู้นำเข้า-ส่งออก, เจ้าของธุรกิจ Food & Pharma) ภาษาไทย สุภาพ น่าเชื่อถือ"
        )

        brief_text = st.text_area(
            "✏️ ปรับ Brief ได้ตามต้องการ",
            value=default_brief,
            height=200,
            key="bridge_brief"
        )

        # ── ปุ่ม Generate ─────────────────────────────────────────────────────
        gen_btn = st.button("► GENERATE CONTENT (Agent 06)", type="primary",
                            use_container_width=True, key="gen_content")

        writer_slot  = st.empty()
        content_area = st.container()

        if gen_btn:
            writer_slot.markdown(agent_row_html(nm["writer"], "working"), unsafe_allow_html=True)

            # รวม brief + analysis เต็มให้ Gemini มีบริบทครบ
            full_brief = (
                f"เขียน{content_type} สำหรับ {platform} ให้บริษัท Jet8\n\n"
                f"=== Brief จากทีมการตลาด ===\n{brief_text}\n\n"
                f"=== ข้อมูลวิเคราะห์ตลาดเพิ่มเติม (จาก Agent 05) ===\n"
                f"{st.session_state.news_analysis}"
            )

            try:
                content_post = generate_content(full_brief)
                w_tok = agent.last_usage["total"]
                st.session_state.tok_total += w_tok
            except Exception as e:
                content_area.error(f"❌ Agent 06 error: {e}")
                st.stop()

            writer_slot.markdown(agent_row_html(nm["writer"], "done"), unsafe_allow_html=True)

            date_str = datetime.now(TH).strftime("%Y-%m-%d %H:%M")
            content_md = f"""# {content_type} — {platform}
_สร้างโดย Agent 06 เมื่อ {date_str}_

---

{content_post}

---
*ข้อมูลอ้างอิงจาก: {st.session_state.news_total} บทความข่าวสัปดาห์นี้*
"""
            with content_area:
                st.markdown(f'<div class="bigstat">✔ CONTENT READY</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="minor">🔢 TOKENS {w_tok:,} &nbsp;|&nbsp; สะสม {st.session_state.tok_total:,}</div>', unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(content_post)
                st.download_button(
                    f"⬇ DOWNLOAD {content_type} (.md)",
                    data=content_md,
                    file_name=f"content_{platform}_{datetime.now(TH).strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
