"""
pages/1_Dashboard.py — CareerSync Dashboard
Persistent login via ?uid= query param.
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
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

    [data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important;}
    [data-testid="stSidebar"]>div:first-child{padding:0!important;}
    [data-testid="collapsedControl"]{display:none!important;}

    /* ALL sidebar buttons — clean nav style */
    [data-testid="stSidebar"] .stButton>button{
      display:flex!important;align-items:center!important;
      width:100%!important;text-align:left!important;justify-content:flex-start!important;
      background:transparent!important;color:#64748b!important;
      border:none!important;box-shadow:none!important;
      font-size:0.875rem!important;font-weight:500!important;
      padding:9px 12px!important;border-radius:9px!important;
      font-family:'DM Sans',sans-serif!important;
      transition:background 0.13s,color 0.13s!important;
    }
    [data-testid="stSidebar"] .stButton>button:hover{
      background:#f8fafc!important;color:#0f172a!important;
    }
    /* Active page button */
    [data-testid="stSidebar"] .stButton>button[data-active="true"]{
      background:rgba(37,99,235,0.08)!important;
      color:#2563EB!important;font-weight:700!important;
    }
    /* Logout button override */
    [data-testid="stSidebar"] .stButton>button.logout{
      color:#94a3b8!important;font-size:0.82rem!important;
      border-top:1px solid #f1f5f9!important;border-radius:0!important;
      padding:10px 16px!important;margin-top:4px!important;
    }
    [data-testid="stSidebar"] .stButton>button.logout:hover{
      background:#fff5f5!important;color:#ef4444!important;
    }
    </style>
    """, unsafe_allow_html=True)

    name_disp  = user.get("name", "User")
    email_disp = user.get("email", "")
    avatar_let = name_disp[0].upper() if name_disp else "U"

    # ── Logo ──
    st.markdown(f"""
    <div style="padding:20px 16px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f1f5f9;">
      <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;display:flex;
                  align-items:center;justify-content:center;flex-shrink:0;">
        <span style="font-family:'Material Symbols Outlined';font-size:17px;color:#fff;
          font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">sync_alt</span>
      </div>
      <span style="font-size:1.1rem;font-weight:800;color:#0f172a;font-family:'DM Sans',sans-serif;">CareerSync</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Nav: pure Streamlit buttons, styled via CSS ──
    # Active page highlighted via inline style injected per-button
    nav_items = [
        ("🏠", "Dashboard",         "pages/1_Dashboard.py",     True),
        ("📋", "Applications",      "pages/2_Applications.py",  False),
        ("✉️",  "Cold Email",        "pages/3_Cold_Email.py",    False),
        ("🔍", "Research Pipeline", "pages/4_Pipeline.py",      False),
        ("⚙️", "Settings",          "pages/5_Settings.py",      False),
    ]

    st.markdown("<div style='padding:10px 6px 8px;'>", unsafe_allow_html=True)
    for icon, label, path, is_active in nav_items:
        btn_label = f"{icon}  {label}"
        if is_active:
            # Wrap in a div that re-styles this specific button blue
            st.markdown(f"""
            <style>
            div[data-testid="stSidebar"] div:has(> div > button[kind="secondary"]:nth-of-type(1)) {{}}
            </style>
            <div style="background:rgba(37,99,235,0.08);border-radius:9px;margin-bottom:2px;">
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <p style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                      font-size:0.875rem;font-weight:700;color:#2563EB;
                      font-family:'DM Sans',sans-serif;margin:0;cursor:default;"
            >{icon}&nbsp;&nbsp;{label}</p>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(btn_label, key=f"nav_{label}", use_container_width=True):
                try:    st.switch_page(path)
                except: st.info(f"{label} coming soon!")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── User footer ──
    st.markdown("<div style='height:1px;background:#f1f5f9;margin:4px 0;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:10px 14px 8px;display:flex;align-items:center;gap:10px;">
      <div style="width:36px;height:36px;border-radius:50%;background:#e0e7ff;display:flex;align-items:center;
                  justify-content:center;font-weight:800;color:#3730a3;font-size:0.875rem;flex-shrink:0;">{avatar_let}</div>
      <div style="min-width:0;">
        <div style="font-size:0.85rem;font-weight:700;color:#0f172a;font-family:'DM Sans',sans-serif;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name_disp}</div>
        <div style="font-size:0.72rem;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{email_disp}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        _logout(); st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

*,*::before,*::after{box-sizing:border-box;}
html,body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
  background:#f8fafc!important;font-family:'DM Sans',sans-serif!important;color:#0f172a!important;}
.block-container{
  padding-top:0!important;padding-left:0!important;padding-right:0!important;
  padding-bottom:3rem!important;max-width:100%!important;}

/* ══ STICKY TOP BAR ══ */
.cs-topbar{
  position:sticky;top:0;z-index:9999;
  height:64px;background:#fff;border-bottom:1px solid #e2e8f0;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 32px;margin-bottom:32px;
}
.cs-topbar-search{position:relative;width:340px;}
.cs-topbar-search .mi{
  position:absolute;left:11px;top:50%;transform:translateY(-50%);
  font-size:17px;color:#94a3b8;pointer-events:none;}
.cs-topbar-search input{
  width:100%;background:#f1f5f9;border:none;border-radius:9px;
  padding:9px 14px 9px 36px;font-size:0.85rem;color:#334155;
  font-family:'DM Sans',sans-serif;outline:none;}
.cs-topbar-search input::placeholder{color:#94a3b8;}
.cs-topbar-right{display:flex;align-items:center;gap:10px;}
.cs-sync-btn{
  display:inline-flex;align-items:center;gap:7px;
  background:#2563EB;color:#fff;border:none;border-radius:9px;
  padding:9px 20px;font-size:0.875rem;font-weight:700;
  font-family:'DM Sans',sans-serif;cursor:pointer;
  box-shadow:0 2px 8px rgba(37,99,235,0.28);transition:background 0.15s;}
.cs-sync-btn:hover{background:#1d4ed8;}
.cs-sync-btn .mi{font-size:17px;}
.cs-notif-btn{
  width:38px;height:38px;border-radius:9px;background:transparent;
  border:none;display:inline-flex;align-items:center;justify-content:center;
  cursor:pointer;color:#64748b;transition:background 0.13s;}
.cs-notif-btn:hover{background:#f1f5f9;}
.cs-notif-btn .mi{font-size:22px;}

/* ══ INNER PADDING WRAPPER ══ */
.inner{padding:0 32px;}

/* ══ STAT CARDS ══ */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-bottom:28px;}
.stat-card{
  background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:20px 22px;box-shadow:0 1px 3px rgba(0,0,0,0.04);
  transition:box-shadow 0.15s,transform 0.12s;}
.stat-card:hover{box-shadow:0 6px 20px rgba(0,0,0,0.07);transform:translateY(-1px);}
.stat-card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.stat-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;}
.stat-icon .mi{font-size:20px;}
.si-blue  {background:rgba(37,99,235,0.08);color:#2563EB;}
.si-amber {background:#fef3c7;color:#d97706;}
.si-green {background:#dcfce7;color:#16a34a;}
.si-purple{background:#ede9fe;color:#7c3aed;}
.stat-badge{font-size:0.7rem;font-weight:700;}
.sb-green{color:#16a34a;} .sb-amber{color:#d97706;} .sb-slate{color:#94a3b8;}
.stat-label{font-size:0.8rem;font-weight:500;color:#64748b;margin-bottom:4px;}
.stat-value{font-size:1.75rem;font-weight:800;color:#0f172a;line-height:1;}

/* ══ SECTION HEADER ══ */
.section-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.section-title{font-size:1rem;font-weight:700;color:#0f172a;}
.section-link{font-size:0.82rem;font-weight:700;color:#2563EB;text-decoration:none;cursor:pointer;}
.section-link:hover{text-decoration:underline;}

/* ══ TABLE ══ */
.table-card{
  background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.app-table{width:100%;border-collapse:collapse;}
.app-table thead tr{background:#f8fafc;border-bottom:1px solid #e2e8f0;}
.app-table th{
  padding:13px 16px;font-size:0.67rem;font-weight:700;color:#94a3b8;
  text-transform:uppercase;letter-spacing:0.7px;
  text-align:left;white-space:nowrap;}
.app-table tbody tr{border-bottom:1px solid #f1f5f9;transition:background 0.1s;}
.app-table tbody tr:last-child{border-bottom:none;}
.app-table tbody tr:hover td{background:#fafbff;}
.app-table td{padding:13px 16px;vertical-align:middle;}

/* Company */
.co-cell{display:flex;align-items:center;gap:10px;}
.co-logo{
  width:32px;height:32px;border-radius:8px;background:#f1f5f9;
  border:1px solid #e2e8f0;display:flex;align-items:center;
  justify-content:center;font-size:0.75rem;font-weight:800;
  color:#475569;flex-shrink:0;}
.co-name{font-size:0.875rem;font-weight:600;color:#0f172a;white-space:nowrap;}
.td-pos{font-size:0.82rem;color:#475569;}
.td-date{font-size:0.8rem;color:#64748b;white-space:nowrap;}

/* Recruiter */
.rec-name {font-size:0.83rem;font-weight:700;color:#0f172a;display:block;}
.rec-title{font-size:0.7rem;color:#94a3b8;display:block;margin-top:1px;}

/* Email chip */
.email-chip{
  display:inline-flex;align-items:center;gap:5px;
  font-size:0.74rem;color:#334155;font-weight:500;
  background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;
  padding:4px 9px;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.email-chip .mi{font-size:13px;color:#94a3b8;flex-shrink:0;}
.email-chip:hover{background:#f1f5f9;}

/* LinkedIn chip */
.li-chip{
  display:inline-flex;align-items:center;gap:5px;
  background:#eff6ff;color:#2563EB;border:1px solid #bfdbfe;
  border-radius:7px;padding:4px 11px;font-size:0.74rem;font-weight:700;
  text-decoration:none;white-space:nowrap;transition:background 0.13s;}
.li-chip:hover{background:#dbeafe;}
.li-chip .mi{font-size:14px;}

/* No data */
.nd{color:#cbd5e1;font-size:0.75rem;font-style:italic;}

/* Badges */
.badge{display:inline-flex;align-items:center;padding:4px 11px;border-radius:9999px;font-size:0.7rem;font-weight:700;white-space:nowrap;}
.b-interview{background:#dbeafe;color:#1d4ed8;}
.b-applied  {background:#f1f5f9;color:#475569;}
.b-offer    {background:#dcfce7;color:#15803d;}
.b-rejected {background:#fee2e2;color:#dc2626;}

/* ══ CREDIT CARD ══ */
.credit-card{
  background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:22px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.credit-row{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:6px;}
.credit-name{font-size:0.85rem;font-weight:700;color:#0f172a;}
.credit-sub {font-size:0.72rem;color:#94a3b8;margin-top:1px;}
.credit-val {font-size:0.78rem;font-weight:700;color:#334155;white-space:nowrap;}
.prog-bar{width:100%;background:#f1f5f9;border-radius:9999px;height:6px;overflow:hidden;}
.prog-fill{height:100%;border-radius:9999px;}
.btn-upgrade{
  width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:9px;
  background:#fff;color:#0f172a;font-size:0.875rem;font-weight:700;
  font-family:'DM Sans',sans-serif;cursor:pointer;transition:background 0.13s;}
.btn-upgrade:hover{background:#f8fafc;}
.pro-tip-card{
  background:rgba(37,99,235,0.04);border:1px solid rgba(37,99,235,0.15);
  border-radius:16px;padding:18px;display:flex;align-items:flex-start;gap:12px;margin-top:16px;}
.pro-tip-icon .mi{font-size:22px;color:#2563EB;}
.pro-tip-title{font-size:0.875rem;font-weight:700;color:#0f172a;margin-bottom:4px;}
.pro-tip-text{font-size:0.78rem;color:#475569;line-height:1.65;}

/* ══ STREAMLIT WIDGET OVERRIDES ══ */
div.stButton>button{
  background:#fff!important;color:#475569!important;border:1px solid #e2e8f0!important;
  border-radius:8px!important;font-weight:600!important;font-size:0.85rem!important;
  font-family:'DM Sans',sans-serif!important;padding:8px 14px!important;transition:all 0.15s!important;}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{
  background:#2563EB!important;color:#fff!important;border-color:#2563EB!important;
  box-shadow:0 2px 8px rgba(37,99,235,0.25)!important;}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}
div[data-testid="stTextInput"] input{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
div[data-testid="stTextArea"] textarea{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
[data-testid="stTabs"] button[aria-selected="true"]{color:#2563EB!important;border-bottom-color:#2563EB!important;}
.stAlert{border-radius:10px!important;}
a.stLinkButton{background:#fff!important;color:#2563EB!important;border:1px solid #bfdbfe!important;border-radius:8px!important;font-weight:600!important;text-decoration:none!important;}
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = 0

first_name = user.get("name","").split()[0] if user.get("name") else "there"

# ══════════════════════════════════════════════════════════════════════════════
# STICKY TOP BAR — HTML (always visible at top)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="cs-topbar">
  <div class="cs-topbar-search">
    <span class="mi">search</span>
    <input type="text" placeholder="Search applications, companies..."/>
  </div>
  <div class="cs-topbar-right">
    <button class="cs-sync-btn">
      <span class="mi">mail</span>&nbsp;Sync Gmail
    </button>
    <button class="cs-notif-btn"><span class="mi">notifications</span></button>
  </div>
</div>
<div style="padding:0 32px;">
  <h2 style="font-size:1.45rem;font-weight:800;color:#0f172a;margin-bottom:4px;
             font-family:'DM Sans',sans-serif;">Dashboard</h2>
  <p style="font-size:0.875rem;color:#64748b;margin-bottom:20px;">
    Welcome back, <strong>{first_name}</strong>! Here's your job search overview.
  </p>
</div>
""", unsafe_allow_html=True)

# ─ Real action buttons (functional)
st.markdown('<div style="padding:0 32px;">', unsafe_allow_html=True)
b1, b2, b3, _ = st.columns([1.2, 1.9, 1.7, 3])
with b1: sync_clicked   = st.button("🔄  Sync Gmail",              use_container_width=True, type="primary",   key="sync_btn")
with b2: enrich_clicked = st.button("🔍  Find Missing Recruiters", use_container_width=True, type="secondary", key="enrich_btn")
with b3: force_enrich   = st.button("⚡  Force Re-Enrich ALL",     use_container_width=True, type="secondary", key="force_btn")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ENRICH HELPERS
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
interviews = len(df[df.stage=="Interview"])  if not df.empty else 0
offers     = len(df[df.stage=="Offer"])      if not df.empty else 0
with_rec   = len(df[df.linkedin_url.str.len()>0]) if not df.empty else 0

# ══════════════════════════════════════════════════════════════════════════════
# STAT CARDS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown((
    '<div style="padding:0 32px;">'
    '<div class="stats-grid">'

    '<div class="stat-card"><div class="stat-card-top">'
    '<div class="stat-icon si-blue"><span class="mi">description</span></div>'
    '<span class="stat-badge sb-green">+12% vs mo</span>'
    '</div><div class="stat-label">Total Applications</div>'
    f'<div class="stat-value">{total}</div></div>'

    '<div class="stat-card"><div class="stat-card-top">'
    '<div class="stat-icon si-amber"><span class="mi">event</span></div>'
    f'<span class="stat-badge sb-amber">{interviews} this week</span>'
    '</div><div class="stat-label">Interviews Scheduled</div>'
    f'<div class="stat-value">{interviews}</div></div>'

    '<div class="stat-card"><div class="stat-card-top">'
    '<div class="stat-icon si-green"><span class="mi">verified</span></div>'
    '<span class="stat-badge sb-green">Highest ever</span>'
    '</div><div class="stat-label">Offers Received</div>'
    f'<div class="stat-value">{offers}</div></div>'

    '<div class="stat-card"><div class="stat-card-top">'
    '<div class="stat-icon si-purple"><span class="mi">groups</span></div>'
    '<span class="stat-badge sb-slate">Total in CRM</span>'
    '</div><div class="stat-label">Recruiters Found</div>'
    f'<div class="stat-value">{with_rec}</div></div>'

    '</div></div>'
), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTER ROW
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="padding:0 32px;">', unsafe_allow_html=True)
f1, f2, f3 = st.columns([3.5, 1, 1])
with f1: search  = st.text_input("Search", placeholder="Company or Job Title...",
                                  label_visibility="collapsed", key="search_inp")
with f2: stage_f = st.selectbox("Stage", ["All","Applied","Interview","Offer","Rejected"],
                                  label_visibility="collapsed", key="stage_sel")
with f3: rec_f   = st.selectbox("Recruiter", ["All","Found","Not Found"],
                                  label_visibility="collapsed", key="rec_sel")
st.markdown("</div>", unsafe_allow_html=True)

filtered = df.copy()
if search:
    m = (filtered.company_name.str.contains(search, case=False, na=False) |
         filtered.position.str.contains(search, case=False, na=False))
    filtered = filtered[m]
if stage_f != "All": filtered = filtered[filtered.stage == stage_f]
if rec_f == "Found":       filtered = filtered[filtered.linkedin_url.str.len() > 0]
elif rec_f == "Not Found": filtered = filtered[filtered.linkedin_url.str.len() == 0]

fkey = f"{search}|{stage_f}|{rec_f}"
if st.session_state.get("_fkey") != fkey:
    st.session_state.page = 0; st.session_state._fkey = fkey

ROWS = 8
total_rows  = len(filtered)
total_pages = max(1, math.ceil(total_rows / ROWS))
if st.session_state.page >= total_pages: st.session_state.page = total_pages - 1
cur     = st.session_state.page
ps      = cur * ROWS
pe      = min(ps + ROWS, total_rows)
page_df = filtered.iloc[ps:pe]

BADGE = {"Applied":"b-applied","Interview":"b-interview","Offer":"b-offer","Rejected":"b-rejected"}

# ══════════════════════════════════════════════════════════════════════════════
# TABLE — Company | Position | Date Applied | Recruiter | Email | LinkedIn | Stage
# ══════════════════════════════════════════════════════════════════════════════
def build_table(rows_df):
    header = (
        '<div class="table-card">'
        '<table class="app-table">'
        '<thead><tr>'
        '<th style="width:16%">Company</th>'
        '<th style="width:18%">Position</th>'
        '<th style="width:11%">Date Applied</th>'
        '<th style="width:15%">Recruiter</th>'
        '<th style="width:20%">Email</th>'
        '<th style="width:9%">LinkedIn</th>'
        '<th style="width:11%;text-align:right">Stage</th>'
        '</tr></thead><tbody>'
    )
    if rows_df.empty:
        return (header +
            '<tr><td colspan="7" style="text-align:center;color:#94a3b8;padding:64px 20px;">'
            '📭 No applications yet. Hit <strong>Sync Gmail</strong> to get started!'
            '</td></tr></tbody></table></div>')
    rows = ""
    for _, r in rows_df.iterrows():
        badge    = BADGE.get(str(r["stage"]), "b-applied")
        let      = str(r.get("company_name","?"))[0].upper()
        company  = str(r.get("company_name",""))
        pos      = str(r.get("position",""))
        date     = str(r.get("applied_date",""))
        stage    = str(r.get("stage","Applied"))
        rec_name = str(r.get("recruiter_name","")).strip()
        rec_ttl  = str(r.get("recruiter_title","")).strip()
        rec_mail = str(r.get("recruiter_email","")).strip()
        li_url   = str(r.get("linkedin_url","")).strip()

        # Recruiter cell
        if rec_name:
            rec_html = (
                f'<span class="rec-name">{rec_name}</span>'
                + (f'<span class="rec-title">{rec_ttl}</span>' if rec_ttl else "")
            )
        else:
            rec_html = '<span class="nd">Not found</span>'

        # Email cell — clickable mailto chip
        if rec_mail:
            email_html = (
                f'<a href="mailto:{rec_mail}" class="email-chip" title="{rec_mail}">'
                f'<span class="mi">mail</span>{rec_mail}</a>'
            )
        else:
            email_html = '<span class="nd">—</span>'

        # LinkedIn cell
        if li_url:
            linkedin_html = (
                f'<a class="li-chip" href="{li_url}" target="_blank" rel="noopener">'
                f'<span class="mi">link</span>Profile</a>'
            )
        else:
            linkedin_html = '<span class="nd">—</span>'

        rows += (
            f'<tr>'
            f'<td><div class="co-cell">'
            f'<div class="co-logo">{let}</div>'
            f'<span class="co-name">{company}</span>'
            f'</div></td>'
            f'<td><span class="td-pos">{pos}</span></td>'
            f'<td><span class="td-date">{date}</span></td>'
            f'<td>{rec_html}</td>'
            f'<td>{email_html}</td>'
            f'<td>{linkedin_html}</td>'
            f'<td style="text-align:right"><span class="badge {badge}">{stage}</span></td>'
            f'</tr>'
        )
    return header + rows + "</tbody></table></div>"

# ══════════════════════════════════════════════════════════════════════════════
# CREDIT USAGE
# ══════════════════════════════════════════════════════════════════════════════
def _credit_item(name, sub, color, pct, val):
    return (
        f'<div style="margin-bottom:18px;">'
        f'<div class="credit-row">'
        f'<div><div class="credit-name">{name}</div>'
        f'<div class="credit-sub">{sub}</div></div>'
        f'<span class="credit-val">{val}</span>'
        f'</div>'
        f'<div class="prog-bar">'
        f'<div class="prog-fill" style="background:{color};width:{pct}%;"></div>'
        f'</div></div>'
    )

def build_credits():
    DEMO = [
        ("google_cse","Google Custom Search","Search API calls",       "#2563EB", 750, 1000),
        ("hunter",    "Hunter.io",            "Email finding credits", "#22c55e", 12,  50),
        ("groq",      "Groq AI",              "Cover letter generation","#a855f7", 88,  100),
    ]
    items = ""
    if _CREDITS_OK:
        state = credits_get_all()
        for key, name, sub, color, _, _ in DEMO:
            svc   = CREDIT_SERVICES.get(key, {})
            entry = state.get(key, {})
            tot   = svc.get("total", 100); used = entry.get("used", 0)
            pct   = max(2, int((used/tot)*100)) if tot > 0 else 2
            items += _credit_item(name, sub, color, pct, f"{used:,} / {tot:,}")
    else:
        for key, name, sub, color, used_d, tot_d in DEMO:
            pct = max(2, int((used_d/tot_d)*100))
            val = f"{used_d:,} / {tot_d:,}" if tot_d != 100 else f"{used_d}%"
            items += _credit_item(name, sub, color, pct, val)
    return (
        '<div class="credit-card">' + items +
        '<div style="height:1px;background:#f1f5f9;margin:8px 0 14px;"></div>'
        '<button class="btn-upgrade">Upgrade Plan</button>'
        '</div>'
        '<div class="pro-tip-card">'
        '<div class="pro-tip-icon"><span class="mi">lightbulb</span></div>'
        '<div><div class="pro-tip-title">Pro Tip</div>'
        '<div class="pro-tip-text">Syncing your Gmail daily improves response tracking accuracy by up to 45%.</div>'
        '</div></div>'
    )

# ══════════════════════════════════════════════════════════════════════════════
# MAIN 2-COLUMN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="padding:0 32px;">', unsafe_allow_html=True)
col_left, col_right = st.columns([2.4, 1], gap="large")

with col_left:
    st.markdown(
        '<div class="section-hdr">'
        '<span class="section-title">Recent Applications</span>'
        '<a class="section-link" href="#">View All</a>'
        '</div>',
        unsafe_allow_html=True)
    st.markdown(build_table(page_df), unsafe_allow_html=True)

    if total_pages > 1:
        st.markdown(
            f"<p style='font-size:0.78rem;color:#64748b;margin:10px 0 6px;'>"
            f"Showing {ps+1}–{pe} of {total_rows} applications</p>",
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
                    st.markdown("<div style='text-align:center;padding-top:6px;color:#94a3b8;'>…</div>", unsafe_allow_html=True)
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
        '<div class="section-hdr">'
        '<span class="section-title">Credit Usage</span>'
        '<span style="font-size:1.15rem;color:#94a3b8;cursor:pointer;line-height:1;" title="Refresh">↻</span>'
        '</div>',
        unsafe_allow_html=True)
    st.markdown(build_credits(), unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# AI COLD EMAIL GENERATOR
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
        tone = st.selectbox("Tone", ["Professional","Friendly & Warm","Concise & Direct","Enthusiastic"],
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
# MANAGE APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:8px;'>"
    "⚙️ Manage Applications</h3>",
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