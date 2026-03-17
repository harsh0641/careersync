"""
pages/1_Dashboard.py — CareerSync Dashboard
Matches reference UI design exactly.
All features preserved. Server-side rendering via st.markdown.
"""

import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import streamlit as st
import pandas as pd

from auth import get_user_by_id, inject_gmail_env, gmail_configured

st.set_page_config(
    page_title="CareerSync — Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

def _restore():
    if st.session_state.get("user"): return True
    if st.session_state.get("logged_out"): return False
    uid = st.query_params.get("uid", "")
    if uid:
        user = get_user_by_id(uid)
        if user:
            st.session_state["user"] = user
            st.session_state["user_id"] = uid
            return True
    return False

def _logout():
    st.session_state["logged_out"] = True
    for k in ["user","user_id"]: st.session_state.pop(k,None)
    st.query_params.clear()
    st.switch_page("app.py")

if not _restore():
    st.query_params.clear()
    st.switch_page("app.py")
    st.stop()

user = st.session_state["user"]
st.query_params["uid"] = user["id"]
inject_gmail_env(user)

from database import get_all_applications, update_stage, delete_application, upsert_application, update_recruiter_info
from email_service import fetch_application_emails
from ai_service import parse_emails_concurrent
from recruiter_finder import enrich_all, enrich_application

try:
    from credits_tracker import get_all as credits_get_all, SERVICES as CREDIT_SERVICES
    _CREDITS_OK = True
except ImportError:
    _CREDITS_OK = False

if "page" not in st.session_state:
    st.session_state.page = 0


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;}
html,body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
  background:#f8fafc!important;font-family:'DM Sans',sans-serif!important;color:#0f172a!important;}
.block-container{padding:0!important;max-width:100%!important;margin:0!important;}
[data-testid="stVerticalBlock"]{gap:0!important;}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],[data-testid="stHeader"]{display:none!important;}

/* SIDEBAR */
[data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important;width:240px!important;min-width:240px!important;}
[data-testid="stSidebar"]>div:first-child{padding:0!important;}
[data-testid="stSidebarContent"]{padding:0!important;}
[data-testid="stSidebar"] .stButton>button{
  text-align:left!important;justify-content:flex-start!important;
  background:transparent!important;color:#64748b!important;border:none!important;
  box-shadow:none!important;font-size:0.875rem!important;font-weight:500!important;
  padding:10px 12px!important;border-radius:8px!important;width:100%!important;
  font-family:'DM Sans',sans-serif!important;transition:all 0.15s!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:#f8fafc!important;color:#0f172a!important;}

/* HEADER */
.dash-header{height:64px;background:#fff;border-bottom:1px solid #e2e8f0;
  display:flex;align-items:center;justify-content:space-between;padding:0 2rem;
  position:sticky;top:0;z-index:100;}
.search-wrap{position:relative;flex:1;max-width:420px;}
.search-icon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#94a3b8;font-size:0.9rem;}
.search-input{width:100%;background:#f1f5f9;border:none;border-radius:8px;
  padding:9px 14px 9px 36px;font-size:0.875rem;font-family:'DM Sans',sans-serif;
  color:#0f172a;outline:none;}
.search-input::placeholder{color:#94a3b8;}
.search-input:focus{background:#e8edf2;}

/* STAT CARDS */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:2rem;}
@media(max-width:900px){.stats-row{grid-template-columns:repeat(2,1fr);}}
@media(max-width:500px){.stats-row{grid-template-columns:1fr;}}
.stat-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.stat-card-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px;}
.stat-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;}
.stat-badge{font-size:0.7rem;font-weight:600;}
.stat-label{font-size:0.82rem;font-weight:500;color:#64748b;margin-bottom:4px;}
.stat-num{font-size:1.75rem;font-weight:700;color:#0f172a;line-height:1;}

/* MAIN GRID */
.main-grid{display:grid;grid-template-columns:1fr 300px;gap:24px;align-items:start;}
@media(max-width:1100px){.main-grid{grid-template-columns:1fr;}}

/* TABLE */
.table-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.table-card-header{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid #f1f5f9;}
.table-card-title{font-size:1rem;font-weight:700;color:#0f172a;}
.cs-table{width:100%;border-collapse:collapse;}
.cs-table th{background:#f8fafc;color:#64748b;font-weight:700;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.7px;padding:12px 20px;border-bottom:1px solid #e2e8f0;text-align:left;}
.cs-table th:last-child{text-align:right;}
.cs-table td{padding:14px 20px;border-bottom:1px solid #f8fafc;color:#334155;font-size:0.84rem;vertical-align:middle;}
.cs-table tr:last-child td{border-bottom:none;}
.cs-table tr:hover td{background:#f8fafc;}
.co-cell{display:flex;align-items:center;gap:12px;}
.co-logo{width:32px;height:32px;border-radius:8px;background:#f1f5f9;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;color:#475569;flex-shrink:0;}
.co-name{font-weight:600;color:#0f172a;font-size:0.875rem;}
.badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;font-size:0.7rem;font-weight:700;white-space:nowrap;}
.b-applied{background:#f1f5f9;color:#475569;}
.b-interview{background:#dbeafe;color:#1d4ed8;}
.b-offer{background:#dcfce7;color:#15803d;}
.b-rejected{background:#fee2e2;color:#dc2626;}
.rec-name{font-weight:600;color:#0f172a;font-size:0.82rem;display:block;}
.rec-title-txt{color:#94a3b8;font-size:0.7rem;display:block;margin-top:1px;}
.li-btn{display:inline-flex;align-items:center;gap:3px;background:#eff6ff;color:#2563EB;border:1px solid #bfdbfe;border-radius:5px;padding:2px 7px;font-size:0.65rem;font-weight:700;text-decoration:none;margin-top:3px;}
.no-data{color:#cbd5e1;font-size:0.78rem;font-style:italic;}
.email-txt{font-size:0.78rem;color:#334155;word-break:break-all;}

/* CREDITS */
.credit-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.credit-card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;}
.credit-item{margin-bottom:16px;}
.credit-item-top{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:5px;}
.credit-item-name{font-size:0.875rem;font-weight:700;color:#0f172a;}
.credit-item-sub{font-size:0.7rem;color:#94a3b8;margin-top:1px;}
.credit-item-count{font-size:0.75rem;font-weight:700;color:#0f172a;}
.credit-bar-bg{height:7px;background:#f1f5f9;border-radius:9999px;overflow:hidden;}
.credit-bar-fill{height:100%;border-radius:9999px;}
.tip-card{background:rgba(37,99,235,0.04);border:1px solid rgba(37,99,235,0.15);border-radius:14px;padding:18px;display:flex;align-items:flex-start;gap:12px;}
.tip-icon{font-size:1.2rem;flex-shrink:0;margin-top:1px;}
.tip-title{font-size:0.875rem;font-weight:700;color:#0f172a;margin-bottom:4px;}
.tip-text{font-size:0.78rem;color:#64748b;line-height:1.55;}

/* SECTION CARDS */
.section-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:22px;margin-top:24px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.section-title{font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:16px;}

/* STREAMLIT OVERRIDES */
div.stButton>button{background:#fff!important;color:#475569!important;border:1px solid #e2e8f0!important;border-radius:8px!important;font-weight:600!important;font-size:0.85rem!important;font-family:'DM Sans',sans-serif!important;padding:8px 16px!important;transition:all 0.15s!important;}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{background:#2563EB!important;color:#fff!important;border-color:#2563EB!important;}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;font-family:'DM Sans',sans-serif!important;}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
[data-testid="stTabs"] button[aria-selected="true"]{color:#2563EB!important;border-bottom-color:#2563EB!important;}
hr{border:none;border-top:1px solid #f1f5f9!important;margin:0!important;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    name_disp  = user.get("name","User")
    email_disp = user.get("email","")
    initials   = name_disp[0].upper() if name_disp else "U"

    st.markdown(f"""
<div style="padding:24px 16px 16px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:32px;">
    <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;display:flex;align-items:center;justify-content:center;">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M7 16V4m0 0L3 8m4-4l4 4"/><path d="M17 8v12m0 0l4-4m-4 4l-4-4"/>
      </svg>
    </div>
    <span style="font-size:1.1rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;">CareerSync</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;background:#eff6ff;color:#2563EB;font-weight:600;font-size:0.875rem;margin-bottom:4px;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
    Dashboard
  </div>
</div>
""", unsafe_allow_html=True)

    nav_pages = [("📋","Applications","pages/2_Applications.py"),("✉️","Cold Email","pages/3_Cold_Email.py"),("🔍","Research Pipeline","pages/4_Pipeline.py"),("⚙️","Settings","pages/5_Settings.py")]
    for icon,label,path in nav_pages:
        if st.button(f"{icon}  {label}", key=f"nav_{label}"):
            try: st.switch_page(path)
            except: st.info(f"{label} coming soon!")

    st.markdown(f"""
<div style="position:absolute;bottom:0;left:0;right:0;padding:16px;border-top:1px solid #e2e8f0;background:#fff;">
  <div style="display:flex;align-items:center;gap:10px;padding:8px;border-radius:10px;background:#f8fafc;">
    <div style="width:36px;height:36px;border-radius:50%;background:#dbeafe;display:flex;align-items:center;justify-content:center;font-weight:700;color:#1d4ed8;font-size:0.875rem;flex-shrink:0;">{initials}</div>
    <div style="min-width:0;flex:1;">
      <div style="font-weight:700;font-size:0.82rem;color:#0f172a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name_disp}</div>
      <div style="font-size:0.68rem;color:#64748b;">Pro Plan</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        _logout(); st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _run_enrich_for(apps_list, label):
    companies = list({a["company_name"] for a in apps_list})
    with st.status(f"{label} ({len(companies)} companies)…", expanded=True) as status:
        try:
            found = 0
            for company in companies:
                st.write(f"🔎 Searching **{company}**…")
                info = enrich_application(company)
                for a in apps_list:
                    if a["company_name"] == company:
                        update_recruiter_info(a["id"],info.get("recruiter_email",""),info.get("recruiter_name",""),info.get("recruiter_title",""),info.get("linkedin_url",""))
                if info.get("recruiter_name") or info.get("recruiter_email") or info.get("linkedin_url"):
                    found += 1; st.write(f"✅ Found for **{company}**")
                else: st.write(f"❌ Nothing for **{company}**")
            status.update(label=f"✅ Done! {found}/{len(companies)} found.", state="complete"); st.rerun()
        except Exception as e: status.update(label=f"❌ Error: {e}", state="error")


# ══════════════════════════════════════════════════════════════════════════════
# HEADER + ACTION BUTTONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="dash-header">
  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input class="search-input" type="text" placeholder="Search applications, companies..."/>
  </div>
</div>
""", unsafe_allow_html=True)

# Action buttons sit just below header
st.markdown("<div style='padding:12px 2rem 0;display:flex;gap:10px;'>", unsafe_allow_html=True)
hc1,hc2,hc3,_ = st.columns([1.3,1.9,1.7,4])
with hc1: sync_clicked   = st.button("📧 Sync Gmail",              key="sync_btn",    type="primary", use_container_width=True)
with hc2: enrich_clicked = st.button("🔍 Find Missing Recruiters", key="enrich_btn",  use_container_width=True)
with hc3: force_enrich   = st.button("⚡ Force Re-Enrich ALL",     key="fenrich_btn", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SYNC / ENRICH ACTIONS
# ══════════════════════════════════════════════════════════════════════════════
if sync_clicked:
    if not gmail_configured(user):
        st.warning("⚠️ Please add your Gmail credentials in Settings first.")
    else:
        with st.status("Syncing your emails...", expanded=True) as status:
            try:
                st.write("📬 Connecting to Gmail...")
                emails = fetch_application_emails()
                st.write(f"✅ Found **{len(emails)}** candidate emails.")
                if emails:
                    st.write("🤖 AI is classifying emails...")
                    parsed = parse_emails_concurrent(emails)
                    st.write(f"✅ Identified **{len(parsed)}** real applications.")
                    if parsed:
                        st.write("🔍 Looking up recruiter contacts...")
                        enriched = enrich_all(list({p["company_name"] for p in parsed}))
                        st.write("💾 Saving to database...")
                        for app in parsed:
                            info = enriched.get(app["company_name"],{})
                            upsert_application(app["company_name"],app["job_title"],app["date"],app["subject"],info.get("recruiter_email",""),info.get("recruiter_name",""),info.get("recruiter_title",""),info.get("linkedin_url",""))
                    status.update(label=f"✅ Done! {len(parsed)} applications saved.", state="complete")
                    st.session_state.page = 0
                else: status.update(label="No new emails found.", state="complete")
            except Exception as e: status.update(label=f"❌ Error: {e}", state="error"); st.error(str(e))

if enrich_clicked:
    all_apps = get_all_applications()
    missing = [a for a in all_apps if not str(a.get("linkedin_url","")).strip() and not str(a.get("recruiter_email","")).strip() and not str(a.get("recruiter_name","")).strip()]
    if not missing: st.success("✅ All applications already have recruiter data!")
    else: _run_enrich_for(missing,"🔍 Finding recruiters")

if force_enrich:
    all_apps = get_all_applications()
    if not all_apps: st.warning("No applications yet.")
    else: _run_enrich_for(all_apps,"⚡ Force Re-Enriching ALL")

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD
# ══════════════════════════════════════════════════════════════════════════════
apps = get_all_applications()
df   = pd.DataFrame(apps) if apps else pd.DataFrame(columns=["id","company_name","position","stage","applied_date","last_updated","email_subject","recruiter_email","recruiter_name","recruiter_title","linkedin_url"])
for col in ["recruiter_email","recruiter_name","recruiter_title","linkedin_url"]:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].fillna("").astype(str)
if "stage" not in df.columns: df["stage"] = "Applied"

total      = len(df)
interviews = len(df[df.stage=="Interview"]) if not df.empty else 0
offers     = len(df[df.stage=="Offer"])     if not df.empty else 0
rejected   = len(df[df.stage=="Rejected"])  if not df.empty else 0
with_rec   = len(df[df.linkedin_url.str.len()>0]) if not df.empty else 0

# ══════════════════════════════════════════════════════════════════════════════
# STAT CARDS
# ══════════════════════════════════════════════════════════════════════════════
first_name = user.get("name","").split()[0] if user.get("name") else "there"
st.markdown(f"""
<div style="padding:1.5rem 2rem 0;">
  <h2 style="font-size:1.3rem;font-weight:700;color:#0f172a;margin-bottom:3px;">Dashboard</h2>
  <p style="font-size:0.875rem;color:#64748b;margin-bottom:1.5rem;">Welcome back, {first_name}! Here's your job search overview.</p>
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-card-top">
        <div class="stat-icon" style="background:#eff6ff;">📄</div>
        <span class="stat-badge" style="color:#22c55e;">+12% vs mo</span>
      </div>
      <div class="stat-label">Total Applications</div>
      <div class="stat-num">{total}</div>
    </div>
    <div class="stat-card">
      <div class="stat-card-top">
        <div class="stat-icon" style="background:#fef3c7;">📅</div>
        <span class="stat-badge" style="color:#f59e0b;">{interviews} scheduled</span>
      </div>
      <div class="stat-label">Interviews Scheduled</div>
      <div class="stat-num">{interviews}</div>
    </div>
    <div class="stat-card">
      <div class="stat-card-top">
        <div class="stat-icon" style="background:#dcfce7;">✅</div>
        <span class="stat-badge" style="color:#22c55e;">Highest ever</span>
      </div>
      <div class="stat-label">Offers Received</div>
      <div class="stat-num">{offers}</div>
    </div>
    <div class="stat-card">
      <div class="stat-card-top">
        <div class="stat-icon" style="background:#f3e8ff;">👥</div>
        <span class="stat-badge" style="color:#94a3b8;">Total in CRM</span>
      </div>
      <div class="stat-label">Recruiters Found</div>
      <div class="stat-num">{with_rec}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILTERS + TABLE DATA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="padding:1rem 2rem 0;">', unsafe_allow_html=True)
fc1,fc2,fc3 = st.columns([3,1,1])
with fc1: search  = st.text_input("Search",    placeholder="🔍  Search company or job title...", label_visibility="collapsed")
with fc2: stage_f = st.selectbox("Stage",      ["All","Applied","Interview","Offer","Rejected"],  label_visibility="collapsed")
with fc3: rec_f   = st.selectbox("Recruiter",  ["All","Found","Not Found"],                       label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

filtered = df.copy()
if search:
    m = (filtered.company_name.str.contains(search,case=False,na=False)|filtered.position.str.contains(search,case=False,na=False))
    filtered = filtered[m]
if stage_f!="All": filtered=filtered[filtered.stage==stage_f]
if rec_f=="Found": filtered=filtered[filtered.linkedin_url.str.len()>0]
elif rec_f=="Not Found": filtered=filtered[filtered.linkedin_url.str.len()==0]

fkey=f"{search}|{stage_f}|{rec_f}"
if st.session_state.get("_fkey")!=fkey:
    st.session_state.page=0; st.session_state._fkey=fkey

ROWS=8; total_rows=len(filtered); total_pages=max(1,math.ceil(total_rows/ROWS))
if st.session_state.page>=total_pages: st.session_state.page=total_pages-1
cur=st.session_state.page; ps=cur*ROWS; pe=min(ps+ROWS,total_rows)
page_df=filtered.iloc[ps:pe]
BADGE={"Applied":"b-applied","Interview":"b-interview","Offer":"b-offer","Rejected":"b-rejected"}

# ══════════════════════════════════════════════════════════════════════════════
# BUILD TABLE + CREDITS HTML
# ══════════════════════════════════════════════════════════════════════════════
def build_table(rows_df):
    rows=""
    if rows_df.empty:
        rows='<tr><td colspan="6"><div style="text-align:center;padding:56px 20px;color:#94a3b8;"><div style="font-size:2rem;margin-bottom:10px;">📭</div><div style="font-size:0.875rem;">No applications yet. Hit <strong>Sync Gmail</strong> to get started!</div></div></td></tr>'
    else:
        for _,r in rows_df.iterrows():
            badge=BADGE.get(str(r["stage"]),"b-applied")
            rec_n=str(r.get("recruiter_name","")).strip(); rec_t=str(r.get("recruiter_title","")).strip()
            li=str(r.get("linkedin_url","")).strip(); em=str(r.get("recruiter_email","")).strip()
            let=str(r["company_name"])[0].upper() if r["company_name"] else "?"
            date=str(r.get("applied_date","—"))
            if rec_n and li: rc=f'<span class="rec-name">👤 {rec_n}</span><span class="rec-title-txt">{rec_t}</span><a href="{li}" target="_blank" class="li-btn">🔗 LinkedIn</a>'
            elif rec_n: rc=f'<span class="rec-name">👤 {rec_n}</span><span class="rec-title-txt">{rec_t}</span>'
            elif li: rc=f'<a href="{li}" target="_blank" class="li-btn">🔗 LinkedIn</a>'
            else: rc='<span class="no-data">Not found</span>'
            ec=f'<span class="email-txt">{em}</span>' if em else '<span class="no-data">—</span>'
            rows+=f'<tr><td><div class="co-cell"><div class="co-logo">{let}</div><span class="co-name">{r["company_name"]}</span></div></td><td style="color:#64748b;font-size:0.84rem;">{r["position"]}</td><td style="color:#64748b;font-size:0.82rem;">{date}</td><td>{rc}</td><td>{ec}</td><td style="text-align:right;"><span class="badge {badge}">{r["stage"]}</span></td></tr>'
    return f'<div class="table-card"><div class="table-card-header"><span class="table-card-title">Recent Applications <span style="color:#94a3b8;font-weight:400;font-size:0.85rem;">({len(rows_df)})</span></span></div><div style="overflow-x:auto;"><table class="cs-table"><thead><tr><th>Company</th><th>Position</th><th>Date Applied</th><th>Recruiter</th><th>Email</th><th style="text-align:right;">Stage</th></tr></thead><tbody>{rows}</tbody></table></div></div>'

def build_credits():
    if not _CREDITS_OK:
        return '<div class="credit-card"><p style="color:#94a3b8;font-size:0.875rem;">Credits tracker not available.</p></div>'
    state=credits_get_all()
    SHOW=[("google_cse","Google Custom Search","Search API calls","#2563EB"),("hunter","Hunter.io","Email finding credits","#22c55e"),("groq","Groq AI","AI generation calls","#8b5cf6")]
    items=""
    for key,name,sub,color in SHOW:
        svc=CREDIT_SERVICES.get(key,{}); entry=state.get(key,{})
        tot=svc.get("total",100); used=entry.get("used",0)
        pct=max(2,int((used/tot)*100)) if tot>0 else 2
        items+=f'<div class="credit-item"><div class="credit-item-top"><div><div class="credit-item-name">{name}</div><div class="credit-item-sub">{sub}</div></div><span class="credit-item-count">{used:,}/{tot:,}</span></div><div class="credit-bar-bg"><div class="credit-bar-fill" style="background:{color};width:{pct}%;"></div></div></div>'
    return f'<div style="display:flex;flex-direction:column;gap:20px;"><div class="credit-card"><div class="credit-card-header"><span style="font-size:1rem;font-weight:700;color:#0f172a;">Credit Usage</span><span style="font-size:1rem;color:#64748b;cursor:pointer;">↻</span></div>{items}<div style="padding-top:14px;border-top:1px solid #f1f5f9;margin-top:4px;"><button style="width:100%;padding:11px;border-radius:10px;border:1px solid #e2e8f0;background:#fff;font-size:0.875rem;font-weight:700;color:#0f172a;cursor:pointer;font-family:DM Sans,sans-serif;">Upgrade Plan</button></div></div><div class="tip-card"><div class="tip-icon">💡</div><div><div class="tip-title">Pro Tip</div><div class="tip-text">Syncing your Gmail daily improves response tracking accuracy by up to 45%.</div></div></div></div>'

# Render the 2-col grid
st.markdown(f"""
<div style="padding:1rem 2rem 0;">
  <div class="main-grid">
    <div>{build_table(page_df)}</div>
    <div>{build_credits()}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Pagination
if total_pages>1:
    st.markdown(f'<p style="font-size:0.78rem;color:#64748b;padding:8px 2rem 0;">Showing {ps+1}–{pe} of {total_rows}</p>',unsafe_allow_html=True)
    def slots(c,t):
        if t<=7: return list(range(t))
        r=[0]; lo,hi=max(1,c-2),min(t-2,c+2)
        if lo>1: r.append(None)
        r.extend(range(lo,hi+1))
        if hi<t-2: r.append(None)
        r.append(t-1); return r
    sl=slots(cur,total_pages); bc=st.columns(2+len(sl))
    with bc[0]:
        if st.button("◀",key="pg_prev",disabled=(cur==0),use_container_width=True): st.session_state.page=cur-1; st.rerun()
    for i,s in enumerate(sl):
        with bc[i+1]:
            if s is None: st.markdown("<div style='text-align:center;padding-top:6px;color:#94a3b8;'>…</div>",unsafe_allow_html=True)
            else:
                if st.button(str(s+1),key=f"pg_{s}",type="primary" if s==cur else "secondary",use_container_width=True): st.session_state.page=s; st.rerun()
    with bc[-1]:
        if st.button("▶",key="pg_next",disabled=(cur==total_pages-1),use_container_width=True): st.session_state.page=cur+1; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# AI COLD EMAIL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="padding:0 2rem;"><div class="section-card"><div class="section-title">✨ AI Cold Email Generator</div>', unsafe_allow_html=True)
rows_for_email=[]
if not page_df.empty:
    for _,r in page_df.iterrows():
        em=str(r.get("recruiter_email","")).strip()
        if em: rows_for_email.append({"label":f"{r['company_name']} · {str(r.get('recruiter_name','') or em).strip()}","company":str(r["company_name"]),"position":str(r["position"]),"rec_name":str(r.get("recruiter_name","")).strip(),"email":em})
if not rows_for_email:
    st.info("💡 No recruiters with emails on this page yet. Sync Gmail and enrich recruiters first.",icon="ℹ️")
else:
    ce1,ce2,ce3=st.columns([2.5,1.5,1])
    with ce1:
        sel_label=st.selectbox("Recruiter",[r["label"] for r in rows_for_email],key="email_rec_sel",label_visibility="collapsed")
        sel_rec=next((r for r in rows_for_email if r["label"]==sel_label),None)
    with ce2: tone=st.selectbox("Tone",["Professional","Friendly & Warm","Concise & Direct","Enthusiastic"],key="email_tone",label_visibility="collapsed")
    with ce3: gen=st.button("✨ Generate",key="gen_email_btn",type="primary",use_container_width=True)
    if gen and sel_rec:
        greet=f"Hi {sel_rec['rec_name'].split()[0]}," if sel_rec["rec_name"] else "Hi,"
        prompt=(f"Write a {tone.lower()} cold follow-up email from a job seeker to a recruiter at {sel_rec['company']} about the {sel_rec['position']} role.\nOpening: {greet}\nRules:\n- Max 130 words\n- First line: Subject: <subject>\n- Blank line then body starting with {greet}\n- No brackets\n- Close: Best regards,\n- Tone: {tone.lower()}")
        with st.spinner("✨ Writing..."):
            try:
                import requests as _req
                from config import GROQ_API_KEY as _gk
                resp=_req.post("https://api.groq.com/openai/v1/chat/completions",headers={"Content-Type":"application/json","Authorization":f"Bearer {_gk}"},json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":prompt}],"max_tokens":420,"temperature":0.72},timeout=20)
                raw=resp.json()["choices"][0]["message"]["content"].strip()
                lines=raw.split("\n"); subj=""; body=[]; past=False
                for ln in lines:
                    if not subj and ln.lower().startswith("subject:"): subj=ln[len("subject:"):].strip(); past=True
                    elif past: body.append(ln)
                if not subj and lines: subj=lines[0]; body=lines[1:]
                st.session_state["ai_email_subj"]=subj; st.session_state["ai_email_body"]="\n".join(body).lstrip("\n").strip(); st.session_state["ai_email_to"]=sel_rec["email"]
            except Exception as ex: st.error(f"❌ Groq error: {ex}")
    if st.session_state.get("ai_email_subj") or st.session_state.get("ai_email_body"):
        subj_e=st.text_input("Subject",value=st.session_state.get("ai_email_subj",""),key="ai_subj_field")
        body_e=st.text_area("Body",value=st.session_state.get("ai_email_body",""),height=200,key="ai_body_field")
        ca,cb,_=st.columns([1.2,1.4,3])
        with ca:
            if st.button("📋 Copy",key="copy_btn"): st.success("Use Ctrl+A to select!",icon="✅")
        with cb:
            to=st.session_state.get("ai_email_to","")
            mailto=(f"mailto:{to}?subject={subj_e.replace(' ','%20')}&body={body_e[:500].replace(chr(10),'%0A').replace(' ','%20')}")
            st.link_button("📨 Open in Mail",mailto)
st.markdown('</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MANAGE APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="padding:0 2rem;"><div class="section-card"><div class="section-title">⚙️ Manage Applications</div>', unsafe_allow_html=True)
tab1,tab2,tab3,tab4=st.tabs(["✏️ Update Stage","🔍 Find Recruiter","➕ Add Manually","🗑️ Delete"])

with tab1:
    st.markdown("<br>",unsafe_allow_html=True)
    if df.empty: st.info("No applications yet. Sync your Gmail to get started!")
    else:
        opts={f"{r['company_name']} — {r['position']}":r["id"] for _,r in df.iterrows()}
        c1,c2=st.columns(2)
        with c1: sel=st.selectbox("Application",list(opts.keys()),key="t1_sel")
        with c2: ns=st.selectbox("New Stage",["Applied","Interview","Offer","Rejected"],key="t1_ns")
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("Update Stage",key="t1_btn",type="primary"):
            update_stage(opts[sel],ns); st.success(f"Updated to **{ns}**."); st.rerun()

with tab2:
    st.markdown("<br>",unsafe_allow_html=True)
    if df.empty: st.info("No applications yet.")
    else:
        opts2={f"{r['company_name']} — {r['position']}":(r["id"],r["company_name"]) for _,r in df.iterrows()}
        sel2=st.selectbox("Application",list(opts2.keys()),key="t2_sel")
        app_id2,company2=opts2[sel2]
        ca,cb=st.columns(2)
        with ca:
            if st.button("⚡ Run Full Pipeline",key="t2_find",use_container_width=True,type="primary"):
                with st.status(f"Searching {company2}…",expanded=True) as s2:
                    try:
                        info=enrich_application(company2)
                        update_recruiter_info(app_id2,info.get("recruiter_email",""),info.get("recruiter_name",""),info.get("recruiter_title",""),info.get("linkedin_url",""))
                        if info.get("recruiter_name") or info.get("linkedin_url"): s2.update(label="✅ Found!",state="complete"); st.success(f"**{info.get('recruiter_name','—')}**")
                        else: s2.update(label="No result.",state="error")
                        st.rerun()
                    except Exception as e: s2.update(label=f"Error: {e}",state="error")
        with cb:
            with st.expander("✏️ Override manually"):
                me=st.text_input("Email",key="t2_me"); mn=st.text_input("Name",key="t2_mn")
                mt=st.text_input("Title",key="t2_mt"); ml=st.text_input("LinkedIn",key="t2_ml")
                if st.button("💾 Save",key="t2_save"): update_recruiter_info(app_id2,me,mn,mt,ml); st.success("Saved!"); st.rerun()

with tab3:
    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: mc=st.text_input("Company",key="m_co"); mt2=st.text_input("Job Title",key="m_ti")
    with c2: md=st.date_input("Applied Date",key="m_da")
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("➕ Add Application",key="m_add",type="primary"):
        if mc and mt2:
            info=enrich_application(mc)
            upsert_application(mc,mt2,str(md),"Manually added",info.get("recruiter_email",""),info.get("recruiter_name",""),info.get("recruiter_title",""),info.get("linkedin_url",""))
            st.success(f"Added **{mt2}** at **{mc}**."); st.rerun()
        else: st.warning("Fill in Company and Job Title.")

with tab4:
    st.markdown("<br>",unsafe_allow_html=True)
    if df.empty: st.info("Nothing to delete.")
    else:
        d_opts={f"{r['company_name']} — {r['position']}":r["id"] for _,r in df.iterrows()}
        d_sel=st.selectbox("Select to delete",list(d_opts.keys()),key="d_sel")
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("🗑️ Delete",type="primary",key="d_btn"): delete_application(d_opts[d_sel]); st.success("Deleted."); st.rerun()

st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown("""
<div style="padding:20px 2rem;text-align:center;">
  <p style="font-size:0.72rem;color:#94a3b8;">CareerSync v3.0 · Gmail · Groq AI · Hunter.io · Apollo.io · Supabase · ❤️</p>
</div>
""", unsafe_allow_html=True)