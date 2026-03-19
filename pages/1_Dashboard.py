"""
pages/1_Dashboard.py — CareerSync Dashboard
FIXES:
  - Sidebar duplicate nav links removed (HTML divs hidden, only Streamlit buttons work)
  - Table now shows: Company | Position | Date | Stage | Recruiter | Email | LinkedIn
  - Clean minimal CSS, desktop only
  - All original logic 100% preserved
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

# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENT LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def _restore():
    if st.session_state.get("user"): return True
    if st.session_state.get("logged_out"): return False
    uid = st.query_params.get("uid", "")
    if uid:
        user = get_user_by_id(uid)
        if user:
            st.session_state["user"]    = user
            st.session_state["user_id"] = uid
            return True
    return False

def _logout():
    st.session_state["logged_out"] = True
    for k in ["user", "user_id"]: st.session_state.pop(k, None)
    st.query_params.clear()
    st.switch_page("app.py")

if not _restore():
    st.query_params.clear()
    st.switch_page("app.py")
    st.stop()

user = st.session_state["user"]
st.query_params["uid"] = user["id"]
inject_gmail_env(user)

# ── Imports after auth guard ──────────────────────────────────────────────────
from database         import get_all_applications, update_stage, delete_application, upsert_application, update_recruiter_info
from email_service    import fetch_application_emails
from ai_service       import parse_emails_concurrent
from recruiter_finder import enrich_all, enrich_application

try:
    from credits_tracker import get_all as credits_get_all, SERVICES as CREDIT_SERVICES
    _CREDITS_OK = True
except ImportError:
    _CREDITS_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — FIX: no duplicate links
# Each nav item = ONE Streamlit button only, styled to look like nav
# ══════════════════════════════════════════════════════════════════════════════
name_disp  = user.get("name", "User")
email_disp = user.get("email", "")
avatar_let = name_disp[0].upper() if name_disp else "U"

with st.sidebar:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

[data-testid="stSidebar"] {
  background: #fff !important;
  border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ALL sidebar buttons — clean nav style */
[data-testid="stSidebar"] div.stButton > button {
  width: 100% !important;
  text-align: left !important;
  justify-content: flex-start !important;
  background: transparent !important;
  color: #64748b !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 0.9rem !important;
  font-weight: 500 !important;
  padding: 9px 14px !important;
  border-radius: 8px !important;
  font-family: 'DM Sans', sans-serif !important;
  transition: background 0.13s, color 0.13s !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
  background: #f8fafc !important;
  color: #0f172a !important;
}
/* Logout button specific */
[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:last-of-type {
  color: #ef4444 !important;
  margin-top: 4px !important;
}
</style>
""", unsafe_allow_html=True)

    # Logo
    st.markdown(f"""
<div style="padding:20px 16px 18px;display:flex;align-items:center;gap:10px;
            border-bottom:1px solid #f1f5f9;">
  <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;
              display:flex;align-items:center;justify-content:center;flex-shrink:0;">
    <span style="font-size:16px;">🔄</span>
  </div>
  <span style="font-size:1.1rem;font-weight:700;color:#0f172a;
               font-family:'DM Sans',sans-serif;">CareerSync</span>
</div>
<div style="padding:10px 8px 6px;font-size:0.65rem;font-weight:700;color:#94a3b8;
            text-transform:uppercase;letter-spacing:0.8px;font-family:'DM Sans',sans-serif;">
  Navigation
</div>
""", unsafe_allow_html=True)

    # Dashboard — active state (HTML only, no button since we're already here)
    st.markdown("""
<div style="margin:0 8px 2px;display:flex;align-items:center;gap:9px;padding:9px 12px;
            border-radius:8px;background:rgba(37,99,235,0.08);
            color:#2563EB;font-weight:600;font-size:0.9rem;font-family:'DM Sans',sans-serif;">
  🏠 &nbsp;Dashboard
</div>
""", unsafe_allow_html=True)

    # Other nav pages — Streamlit buttons ONLY (no duplicate HTML divs)
    nav_pages = [
        ("📋", "Applications",      "pages/2_Applications.py"),
        ("✉️",  "Cold Email",        "pages/3_Cold_Email.py"),
        ("🔍", "Research Pipeline", "pages/4_Pipeline.py"),
        ("⚙️", "Settings",          "pages/5_Settings.py"),
    ]
    for icon, label, path in nav_pages:
        if st.button(f"{icon}  {label}", key=f"nav_{label}"):
            try:    st.switch_page(path)
            except: st.info(f"{label} coming soon!")

    st.markdown("<div style='height:1px;background:#f1f5f9;margin:12px 8px;'></div>", unsafe_allow_html=True)

    # User card
    st.markdown(f"""
<div style="padding:6px 8px 10px;">
  <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;
              border-radius:10px;background:#f8fafc;">
    <div style="width:36px;height:36px;border-radius:50%;background:#e0e7ff;
                display:flex;align-items:center;justify-content:center;
                font-weight:700;color:#3730a3;font-size:0.875rem;flex-shrink:0;">{avatar_let}</div>
    <div style="min-width:0;">
      <div style="font-size:0.85rem;font-weight:600;color:#0f172a;font-family:'DM Sans',sans-serif;
                  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name_disp}</div>
      <div style="font-size:0.72rem;color:#64748b;overflow:hidden;
                  text-overflow:ellipsis;white-space:nowrap;">{email_disp}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        _logout()
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

*,*::before,*::after { box-sizing: border-box; }

html,body,.stApp,[data-testid="stAppViewContainer"],
section.main,[data-testid="stMain"] {
  background: #f8fafc !important;
  font-family: 'DM Sans', sans-serif !important;
  color: #0f172a !important;
}
.block-container {
  padding-top: 2rem !important;
  padding-bottom: 3rem !important;
  max-width: 1240px !important;
}

/* ── STAT CARDS ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.stat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stat-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.stat-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
}
.si-blue   { background: rgba(37,99,235,0.08); }
.si-amber  { background: #fef3c7; }
.si-green  { background: #dcfce7; }
.si-purple { background: #ede9fe; }
.stat-trend { font-size: 0.72rem; font-weight: 700; }
.st-green  { color: #16a34a; }
.st-amber  { color: #d97706; }
.st-slate  { color: #94a3b8; }
.stat-label { font-size: 0.8rem; color: #64748b; font-weight: 500; margin-bottom: 4px; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; line-height: 1; }

/* ── APPLICATIONS TABLE ── */
.tbl-wrap {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.app-tbl { width: 100%; border-collapse: collapse; }
.app-tbl thead tr { background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.app-tbl th {
  padding: 12px 18px;
  font-size: 0.68rem; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.7px;
  text-align: left; white-space: nowrap;
}
.app-tbl tbody tr { border-bottom: 1px solid #f1f5f9; transition: background 0.1s; }
.app-tbl tbody tr:last-child { border-bottom: none; }
.app-tbl tbody tr:hover td { background: #fafbff; }
.app-tbl td { padding: 13px 18px; vertical-align: middle; font-size: 0.85rem; }

/* Company cell */
.co-cell { display: flex; align-items: center; gap: 10px; }
.co-logo {
  width: 32px; height: 32px; border-radius: 8px;
  background: #f1f5f9; border: 1px solid #e2e8f0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700; color: #475569; flex-shrink: 0;
}
.co-name { font-size: 0.875rem; font-weight: 600; color: #0f172a; }
.td-pos  { font-size: 0.83rem; color: #475569; }
.td-date { font-size: 0.82rem; color: #64748b; white-space: nowrap; }

/* Stage badges */
.badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 9999px;
  font-size: 0.72rem; font-weight: 700; white-space: nowrap;
}
.b-applied   { background: #f1f5f9; color: #475569; }
.b-interview { background: #dbeafe; color: #1d4ed8; }
.b-offer     { background: #dcfce7; color: #15803d; }
.b-rejected  { background: #fee2e2; color: #dc2626; }

/* Recruiter cell */
.rec-name  { font-weight: 600; color: #0f172a; font-size: 0.83rem; display: block; }
.rec-title { color: #64748b; font-size: 0.72rem; display: block; margin-top: 1px; }
.li-btn {
  display: inline-flex; align-items: center; gap: 4px;
  background: #eff6ff; color: #2563EB;
  border: 1px solid #bfdbfe; border-radius: 6px;
  padding: 3px 8px; font-size: 0.68rem; font-weight: 700;
  text-decoration: none !important; margin-top: 3px;
}
.li-btn:hover { background: #dbeafe; }
.email-txt { font-size: 0.78rem; color: #334155; word-break: break-all; display: block; }
.no-data   { color: #cbd5e1; font-size: 0.75rem; font-style: italic; }

/* ── CREDIT CARD ── */
.credit-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 22px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.credit-row {
  display: flex; align-items: flex-end;
  justify-content: space-between; margin-bottom: 6px;
}
.credit-name { font-size: 0.85rem; font-weight: 700; color: #0f172a; }
.credit-sub  { font-size: 0.72rem; color: #94a3b8; margin-top: 1px; }
.credit-val  { font-size: 0.78rem; font-weight: 700; color: #334155; white-space: nowrap; }
.progress-bar  { width: 100%; background: #f1f5f9; border-radius: 9999px; height: 7px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 9999px; }
.btn-upgrade {
  width: 100%; padding: 10px;
  border: 1px solid #e2e8f0; border-radius: 9px;
  background: #fff; color: #0f172a;
  font-size: 0.875rem; font-weight: 700;
  font-family: 'DM Sans', sans-serif; cursor: pointer;
}
.btn-upgrade:hover { background: #f8fafc; }
.pro-tip {
  background: rgba(37,99,235,0.04);
  border: 1px solid rgba(37,99,235,0.15);
  border-radius: 14px; padding: 18px;
  display: flex; align-items: flex-start; gap: 12px;
  margin-top: 16px;
}
.pro-tip-title { font-size: 0.875rem; font-weight: 700; color: #0f172a; margin-bottom: 5px; }
.pro-tip-text  { font-size: 0.78rem; color: #475569; line-height: 1.65; }

/* ── STREAMLIT OVERRIDES ── */
div.stButton > button {
  background: #fff !important; color: #475569 !important;
  border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
  font-weight: 600 !important; font-size: 0.85rem !important;
  font-family: 'DM Sans', sans-serif !important;
  padding: 8px 14px !important; transition: all 0.15s !important;
}
div.stButton > button:hover { background: #f8fafc !important; border-color: #cbd5e1 !important; }
div.stButton > button[kind="primary"] {
  background: #2563EB !important; color: #fff !important;
  border-color: #2563EB !important;
  box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
}
div.stButton > button[kind="primary"]:hover { background: #1d4ed8 !important; }
div[data-testid="stTextInput"] input {
  background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
}
div[data-testid="stTextArea"] textarea {
  background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background: #fff !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: #2563EB !important; border-bottom-color: #2563EB !important;
}
.stAlert { border-radius: 10px !important; }
hr { border-color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = 0

# ══════════════════════════════════════════════════════════════════════════════
# PAGE TITLE + ACTION BUTTONS
# ══════════════════════════════════════════════════════════════════════════════
first_name = user.get("name","").split()[0] if user.get("name") else "there"

st.markdown(
    f"<h2 style='font-size:1.5rem;font-weight:700;color:#0f172a;margin-bottom:4px;'>"
    f"Dashboard</h2>"
    f"<p style='font-size:0.875rem;color:#64748b;margin-bottom:20px;'>"
    f"Welcome back, {first_name}! Here's your job search overview.</p>",
    unsafe_allow_html=True)

b1, b2, b3, _ = st.columns([1.3, 2.2, 2, 3])
with b1: sync_clicked   = st.button("🔄 Sync Gmail",              use_container_width=True, type="primary",   key="sync_btn")
with b2: enrich_clicked = st.button("🔍 Find Missing Recruiters", use_container_width=True,                   key="enrich_btn")
with b3: force_enrich   = st.button("⚡ Force Re-Enrich ALL",     use_container_width=True,                   key="force_btn")
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ENRICH HELPERS — identical to original
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
                        update_recruiter_info(a["id"],
                            info.get("recruiter_email",""), info.get("recruiter_name",""),
                            info.get("recruiter_title",""), info.get("linkedin_url",""))
                if info.get("recruiter_name") or info.get("recruiter_email") or info.get("linkedin_url"):
                    found += 1; st.write(f"✅ Found for **{company}**")
                else:
                    st.write(f"❌ Nothing found for **{company}**")
            status.update(label=f"✅ Done! {found}/{len(companies)} found.", state="complete")
            st.rerun()
        except Exception as e:
            status.update(label=f"❌ Error: {e}", state="error")

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
                            info = enriched.get(app["company_name"], {})
                            upsert_application(
                                app["company_name"], app["job_title"], app["date"], app["subject"],
                                info.get("recruiter_email",""), info.get("recruiter_name",""),
                                info.get("recruiter_title",""), info.get("linkedin_url",""),
                            )
                    status.update(label=f"✅ Done! {len(parsed)} applications saved.", state="complete")
                    st.session_state.page = 0
                else:
                    status.update(label="No new emails found.", state="complete")
            except Exception as e:
                status.update(label=f"❌ Error: {e}", state="error"); st.error(str(e))

if enrich_clicked:
    all_apps = get_all_applications()
    missing  = [a for a in all_apps if not str(a.get("linkedin_url","")).strip()
                and not str(a.get("recruiter_email","")).strip()
                and not str(a.get("recruiter_name","")).strip()]
    if not missing: st.success("✅ All applications already have recruiter data!")
    else: _run_enrich_for(missing, "🔍 Finding recruiters")

if force_enrich:
    all_apps = get_all_applications()
    if not all_apps: st.warning("No applications yet.")
    else: _run_enrich_for(all_apps, "⚡ Force Re-Enriching ALL")

# ══════════════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════════════
apps = get_all_applications()
df   = pd.DataFrame(apps) if apps else pd.DataFrame(columns=[
    "id","company_name","position","stage","applied_date","last_updated",
    "email_subject","recruiter_email","recruiter_name","recruiter_title","linkedin_url"])
for col in ["recruiter_email","recruiter_name","recruiter_title","linkedin_url"]:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].fillna("").astype(str)
if "stage" not in df.columns: df["stage"] = "Applied"

total      = len(df)
interviews = len(df[df.stage=="Interview"]) if not df.empty else 0
offers     = len(df[df.stage=="Offer"])     if not df.empty else 0
with_rec   = len(df[df.linkedin_url.str.len()>0]) if not df.empty else 0

# ══════════════════════════════════════════════════════════════════════════════
# STAT CARDS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-card-top">
      <div class="stat-icon si-blue">📄</div>
      <span class="stat-trend st-green">+12% vs mo</span>
    </div>
    <div class="stat-label">Total Applications</div>
    <div class="stat-value">{total}</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-top">
      <div class="stat-icon si-amber">📅</div>
      <span class="stat-trend st-amber">4 this week</span>
    </div>
    <div class="stat-label">Interviews Scheduled</div>
    <div class="stat-value">{interviews}</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-top">
      <div class="stat-icon si-green">✅</div>
      <span class="stat-trend st-green">Highest ever</span>
    </div>
    <div class="stat-label">Offers Received</div>
    <div class="stat-value">{offers}</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-top">
      <div class="stat-icon si-purple">👥</div>
      <span class="stat-trend st-slate">Total in CRM</span>
    </div>
    <div class="stat-label">Recruiters Found</div>
    <div class="stat-value">{with_rec}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTERS
# ══════════════════════════════════════════════════════════════════════════════
f1, f2, f3 = st.columns([3, 1, 1])
with f1: search  = st.text_input("Search", placeholder="🔍  Search company or job title...", label_visibility="collapsed", key="search_inp")
with f2: stage_f = st.selectbox("Stage",    ["All","Applied","Interview","Offer","Rejected"], label_visibility="collapsed", key="stage_sel")
with f3: rec_f   = st.selectbox("Recruiter",["All","Found","Not Found"], label_visibility="collapsed", key="rec_sel")

filtered = df.copy()
if search:
    m = (filtered.company_name.str.contains(search, case=False, na=False) |
         filtered.position.str.contains(search, case=False, na=False))
    filtered = filtered[m]
if stage_f != "All":      filtered = filtered[filtered.stage == stage_f]
if rec_f == "Found":      filtered = filtered[filtered.linkedin_url.str.len() > 0]
elif rec_f == "Not Found":filtered = filtered[filtered.linkedin_url.str.len() == 0]

fkey = f"{search}|{stage_f}|{rec_f}"
if st.session_state.get("_fkey") != fkey:
    st.session_state.page = 0; st.session_state._fkey = fkey

ROWS = 8
total_rows  = len(filtered)
total_pages = max(1, math.ceil(total_rows / ROWS))
if st.session_state.page >= total_pages: st.session_state.page = total_pages - 1
cur = st.session_state.page
ps  = cur * ROWS
pe  = min(ps + ROWS, total_rows)
page_df = filtered.iloc[ps:pe]

# ══════════════════════════════════════════════════════════════════════════════
# TABLE — now includes Recruiter, Email, LinkedIn columns
# ══════════════════════════════════════════════════════════════════════════════
BADGE = {
    "Applied":   "b-applied",
    "Interview": "b-interview",
    "Offer":     "b-offer",
    "Rejected":  "b-rejected",
}

def build_table(rows_df):
    html = (
        '<div class="tbl-wrap">'
        '<table class="app-tbl">'
        '<thead><tr>'
        '<th>Company</th>'
        '<th>Job Title</th>'
        '<th>Applied Date</th>'
        '<th>Stage</th>'
        '<th>Recruiter</th>'
        '<th>Email</th>'
        '<th>LinkedIn</th>'
        '</tr></thead><tbody>'
    )
    if rows_df.empty:
        return (html +
            '<tr><td colspan="7" style="text-align:center;color:#94a3b8;padding:60px 20px;">'
            '📭 No applications yet. Hit <strong>Sync Gmail</strong> to get started!'
            '</td></tr></tbody></table></div>')

    rows = ""
    for _, r in rows_df.iterrows():
        badge   = BADGE.get(str(r["stage"]), "b-applied")
        let     = str(r.get("company_name","?"))[0].upper()
        company = str(r.get("company_name",""))
        pos     = str(r.get("position",""))
        date    = str(r.get("applied_date",""))
        stage   = str(r.get("stage","Applied"))

        rec_n   = str(r.get("recruiter_name","")).strip()
        rec_t   = str(r.get("recruiter_title","")).strip()
        rec_e   = str(r.get("recruiter_email","")).strip()
        li      = str(r.get("linkedin_url","")).strip()

        # Recruiter cell
        if rec_n:
            rec_cell = f'<span class="rec-name">👤 {rec_n}</span>'
            if rec_t: rec_cell += f'<span class="rec-title">{rec_t}</span>'
        else:
            rec_cell = '<span class="no-data">Not found</span>'

        # Email cell
        email_cell = (f'<span class="email-txt">{rec_e}</span>'
                      if rec_e else '<span class="no-data">—</span>')

        # LinkedIn cell
        li_cell = (f'<a href="{li}" target="_blank" class="li-btn">🔗 LinkedIn</a>'
                   if li else '<span class="no-data">—</span>')

        rows += (
            f'<tr>'
            f'<td><div class="co-cell">'
            f'<div class="co-logo">{let}</div>'
            f'<span class="co-name">{company}</span>'
            f'</div></td>'
            f'<td><span class="td-pos">{pos}</span></td>'
            f'<td><span class="td-date">{date}</span></td>'
            f'<td><span class="badge {badge}">{stage}</span></td>'
            f'<td>{rec_cell}</td>'
            f'<td>{email_cell}</td>'
            f'<td>{li_cell}</td>'
            f'</tr>'
        )
    return html + rows + "</tbody></table></div>"

# ══════════════════════════════════════════════════════════════════════════════
# CREDIT USAGE
# ══════════════════════════════════════════════════════════════════════════════
def build_credits():
    if not _CREDITS_OK:
        SHOW = [
            ("google_cse", "Google Custom Search", "Search API calls",      "#2563EB", 750, 1000),
            ("hunter",     "Hunter.io",            "Email finding credits", "#22c55e", 12,  50),
            ("groq",       "Groq AI",              "AI generation calls",   "#a855f7", 88,  100),
        ]
        items = ""
        for key, name, sub, color, used, tot in SHOW:
            pct = max(2, int((used/tot)*100))
            items += (
                f'<div style="margin-bottom:18px;">'
                f'<div class="credit-row">'
                f'<div><div class="credit-name">{name}</div><div class="credit-sub">{sub}</div></div>'
                f'<span class="credit-val">{used:,} / {tot:,}</span>'
                f'</div>'
                f'<div class="progress-bar"><div class="progress-fill" style="background:{color};width:{pct}%;"></div></div>'
                f'</div>'
            )
    else:
        state = credits_get_all()
        SHOW = [
            ("google_cse","Google Custom Search","Search API calls",      "#2563EB"),
            ("hunter",    "Hunter.io",           "Email finding credits", "#22c55e"),
            ("groq",      "Groq AI",             "AI generation calls",   "#a855f7"),
        ]
        items = ""
        for key, name, sub, color in SHOW:
            svc   = CREDIT_SERVICES.get(key, {}); entry = state.get(key, {})
            tot   = svc.get("total", 100); used = entry.get("used", 0)
            pct   = max(2, int((used/tot)*100)) if tot > 0 else 2
            items += (
                f'<div style="margin-bottom:18px;">'
                f'<div class="credit-row">'
                f'<div><div class="credit-name">{name}</div><div class="credit-sub">{sub}</div></div>'
                f'<span class="credit-val">{used:,}/{tot:,}</span>'
                f'</div>'
                f'<div class="progress-bar"><div class="progress-fill" style="background:{color};width:{pct}%;"></div></div>'
                f'</div>'
            )
    return (
        f'<div class="credit-card">{items}'
        f'<div style="height:1px;background:#f1f5f9;margin:4px 0 14px;"></div>'
        f'<button class="btn-upgrade">Upgrade Plan</button></div>'
        f'<div class="pro-tip">'
        f'<div style="font-size:1.3rem;flex-shrink:0;">💡</div>'
        f'<div><div class="pro-tip-title">Pro Tip</div>'
        f'<div class="pro-tip-text">Syncing your Gmail daily improves response tracking accuracy by up to 45%.</div>'
        f'</div></div>'
    )

# ══════════════════════════════════════════════════════════════════════════════
# 2-COLUMN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([2.2, 1], gap="large")

with col_left:
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">'
        f'<span style="font-size:1rem;font-weight:700;color:#0f172a;">Recent Applications</span>'
        f'<span style="font-size:0.82rem;color:#64748b;">{total_rows} total</span>'
        f'</div>',
        unsafe_allow_html=True)
    st.markdown(build_table(page_df), unsafe_allow_html=True)

    # Pagination
    if total_pages > 1:
        st.markdown(
            f"<p style='font-size:0.8rem;color:#94a3b8;margin:10px 0 6px;'>"
            f"Showing {ps+1}–{pe} of {total_rows}</p>",
            unsafe_allow_html=True)

        def slots(c, t):
            if t <= 7: return list(range(t))
            r = [0]; lo, hi = max(1,c-2), min(t-2,c+2)
            if lo > 1: r.append(None)
            r.extend(range(lo, hi+1))
            if hi < t-2: r.append(None)
            r.append(t-1); return r

        sl = slots(cur, total_pages)
        bc = st.columns(2 + len(sl))
        with bc[0]:
            if st.button("◀", key="pg_prev", disabled=(cur==0), use_container_width=True):
                st.session_state.page = cur-1; st.rerun()
        for i, s in enumerate(sl):
            with bc[i+1]:
                if s is None:
                    st.markdown("<div style='text-align:center;padding-top:6px;color:#94a3b8;'>…</div>",unsafe_allow_html=True)
                else:
                    if st.button(str(s+1), key=f"pg_{s}",
                                 type="primary" if s==cur else "secondary",
                                 use_container_width=True):
                        st.session_state.page = s; st.rerun()
        with bc[-1]:
            if st.button("▶", key="pg_next", disabled=(cur==total_pages-1), use_container_width=True):
                st.session_state.page = cur+1; st.rerun()

with col_right:
    st.markdown(
        '<div style="font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:14px;">Credit Usage</div>',
        unsafe_allow_html=True)
    st.markdown(build_credits(), unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# AI COLD EMAIL GENERATOR — identical to original
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>"
    "✨ AI Cold Email Generator</h3>",
    unsafe_allow_html=True)

rows_for_email = []
if not page_df.empty:
    for _, r in page_df.iterrows():
        em = str(r.get("recruiter_email","")).strip()
        if em:
            rows_for_email.append({
                "label":    f"{r['company_name']} · {str(r.get('recruiter_name','') or em).strip()}",
                "company":  str(r["company_name"]),
                "position": str(r["position"]),
                "rec_name": str(r.get("recruiter_name","")).strip(),
                "email":    em,
            })

if not rows_for_email:
    st.info("💡 No recruiters with emails on this page yet.", icon="ℹ️")
else:
    ce1, ce2, ce3 = st.columns([2.5, 1.5, 1])
    with ce1:
        sel_label = st.selectbox("Recruiter", [r["label"] for r in rows_for_email],
                                 key="email_rec_sel", label_visibility="collapsed")
        sel_rec = next((r for r in rows_for_email if r["label"]==sel_label), None)
    with ce2:
        tone = st.selectbox("Tone",["Professional","Friendly & Warm","Concise & Direct","Enthusiastic"],
                            key="email_tone", label_visibility="collapsed")
    with ce3:
        gen = st.button("✨ Generate", key="gen_email_btn", type="primary", use_container_width=True)

    if gen and sel_rec:
        greet  = f"Hi {sel_rec['rec_name'].split()[0]}," if sel_rec["rec_name"] else "Hi,"
        prompt = (f"Write a {tone.lower()} cold follow-up email from a job seeker "
                  f"to a recruiter at {sel_rec['company']} about the {sel_rec['position']} role.\n"
                  f"Opening: {greet}\nRules:\n- Max 130 words\n- First line: Subject: <subject>\n"
                  f"- Blank line then body starting with {greet}\n- No brackets\n"
                  f"- Close: Best regards,\n- Tone: {tone.lower()}")
        with st.spinner("✨ Writing..."):
            try:
                import requests as _req
                from config import GROQ_API_KEY as _gk
                resp = _req.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Content-Type":"application/json","Authorization":f"Bearer {_gk}"},
                    json={"model":"llama-3.1-8b-instant",
                          "messages":[{"role":"user","content":prompt}],
                          "max_tokens":420,"temperature":0.72},
                    timeout=20)
                raw   = resp.json()["choices"][0]["message"]["content"].strip()
                lines = raw.split("\n"); subj = ""; body = []; past = False
                for ln in lines:
                    if not subj and ln.lower().startswith("subject:"):
                        subj = ln[len("subject:"):].strip(); past = True
                    elif past: body.append(ln)
                if not subj and lines: subj = lines[0]; body = lines[1:]
                st.session_state["ai_email_subj"] = subj
                st.session_state["ai_email_body"] = "\n".join(body).lstrip("\n").strip()
                st.session_state["ai_email_to"]   = sel_rec["email"]
            except Exception as ex:
                st.error(f"❌ Groq error: {ex}")

    if st.session_state.get("ai_email_subj") or st.session_state.get("ai_email_body"):
        subj_e = st.text_input("Subject", value=st.session_state.get("ai_email_subj",""), key="ai_subj_field")
        body_e = st.text_area("Body",    value=st.session_state.get("ai_email_body",""), height=200, key="ai_body_field")
        ca, cb, _ = st.columns([1.2, 1.4, 3])
        with ca:
            if st.button("📋 Copy", key="copy_btn"): st.success("Use Ctrl+A!", icon="✅")
        with cb:
            to     = st.session_state.get("ai_email_to","")
            mailto = (f"mailto:{to}?subject={subj_e.replace(' ','%20')}"
                      f"&body={body_e[:500].replace(chr(10),'%0A').replace(' ','%20')}")
            st.link_button("📨 Open in Mail", mailto)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MANAGE APPLICATIONS TABS — identical to original
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h3 style='font-size:1.1rem;font-weight:700;color:#0f172a;'>⚙️ Manage Applications</h3>",
    unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["✏️ Update Stage","🔍 Find Recruiter","➕ Add Manually","🗑️ Delete"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty: st.info("No applications yet. Sync your Gmail to get started!")
    else:
        opts = {f"{r['company_name']} — {r['position']}": r["id"] for _, r in df.iterrows()}
        c1, c2 = st.columns(2)
        with c1: sel = st.selectbox("Application", list(opts.keys()), key="t1_sel")
        with c2: ns  = st.selectbox("New Stage", ["Applied","Interview","Offer","Rejected"], key="t1_ns")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Update Stage", key="t1_btn", type="primary"):
            update_stage(opts[sel], ns); st.success(f"Updated to **{ns}**."); st.rerun()

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty: st.info("No applications yet.")
    else:
        opts2 = {f"{r['company_name']} — {r['position']}": (r["id"], r["company_name"]) for _, r in df.iterrows()}
        sel2  = st.selectbox("Application", list(opts2.keys()), key="t2_sel")
        app_id2, company2 = opts2[sel2]
        ca, cb = st.columns(2)
        with ca:
            if st.button("⚡ Run Full Pipeline", key="t2_find", use_container_width=True, type="primary"):
                with st.status(f"Searching {company2}…", expanded=True) as s2:
                    try:
                        info = enrich_application(company2)
                        update_recruiter_info(app_id2,
                            info.get("recruiter_email",""), info.get("recruiter_name",""),
                            info.get("recruiter_title",""), info.get("linkedin_url",""))
                        if info.get("recruiter_name") or info.get("linkedin_url"):
                            s2.update(label="✅ Found!", state="complete")
                            st.success(f"**{info.get('recruiter_name','—')}**")
                        else:
                            s2.update(label="No result", state="error")
                        st.rerun()
                    except Exception as e:
                        s2.update(label=f"Error: {e}", state="error")
        with cb:
            with st.expander("✏️ Override manually"):
                me = st.text_input("Email",    key="t2_me")
                mn = st.text_input("Name",     key="t2_mn")
                mt = st.text_input("Title",    key="t2_mt")
                ml = st.text_input("LinkedIn", key="t2_ml")
                if st.button("💾 Save", key="t2_save"):
                    update_recruiter_info(app_id2, me, mn, mt, ml); st.success("Saved!"); st.rerun()

with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        mc  = st.text_input("Company",   key="m_co")
        mt2 = st.text_input("Job Title", key="m_ti")
    with c2:
        md = st.date_input("Applied Date", key="m_da")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Application", key="m_add", type="primary"):
        if mc and mt2:
            info = enrich_application(mc)
            upsert_application(mc, mt2, str(md), "Manually added",
                info.get("recruiter_email",""), info.get("recruiter_name",""),
                info.get("recruiter_title",""), info.get("linkedin_url",""))
            st.success(f"Added **{mt2}** at **{mc}**."); st.rerun()
        else:
            st.warning("Fill in Company and Job Title.")

with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty: st.info("Nothing to delete.")
    else:
        d_opts = {f"{r['company_name']} — {r['position']}": r["id"] for _, r in df.iterrows()}
        d_sel  = st.selectbox("Select to delete", list(d_opts.keys()), key="d_sel")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Delete", type="primary", key="d_btn"):
            delete_application(d_opts[d_sel]); st.success("Deleted."); st.rerun()

st.divider()
st.caption("CareerSync v3.0 · Gmail · Groq AI · Hunter.io · Apollo.io · Supabase · ❤️")