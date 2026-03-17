"""
pages/1_Dashboard.py — CareerSync Dashboard
UI: Exact match to design — DM Sans, #2563EB, white sidebar,
    sticky topbar with search + Sync Gmail, 4 stat cards with icons,
    2-col layout (table left, credits right), fully responsive.
All original logic preserved exactly.
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
    if st.session_state.get("user"):
        return True
    if st.session_state.get("logged_out"):
        return False
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
    for k in ["user", "user_id"]:
        st.session_state.pop(k, None)
    st.query_params.clear()
    st.switch_page("app.py")

if not _restore():
    st.query_params.clear()
    st.switch_page("app.py")
    st.stop()

user = st.session_state["user"]
st.query_params["uid"] = user["id"]
inject_gmail_env(user)

# ── Imports after auth guard ───────────────────────────────────────────────────
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
# USER INFO
# ══════════════════════════════════════════════════════════════════════════════
name_disp  = user.get("name", "User")
email_disp = user.get("email", "")
avatar_let = name_disp[0].upper() if name_disp else "U"
first_name = name_disp.split()[0] if name_disp else "there"

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — exact design match
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

/* ── RESET ── */
*, *::before, *::after { box-sizing: border-box; }

/* ── APP BACKGROUND ── */
html, body, .stApp,
[data-testid="stAppViewContainer"],
section.main, [data-testid="stMain"] {
    background: #f8fafc !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #0f172a !important;
}

/* ── BLOCK CONTAINER ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1180px !important;
}

/* ══════════════════
   SIDEBAR (Streamlit native)
══════════════════ */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
    min-width: 240px !important;
    max-width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
    display: flex;
    flex-direction: column;
    height: 100%;
}
/* Sidebar nav buttons */
[data-testid="stSidebar"] div.stButton > button {
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #64748b !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    padding: 9px 12px !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: background 0.15s, color 0.15s !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: #f8fafc !important;
    color: #0f172a !important;
}
/* Hide sidebar collapse button */
[data-testid="collapsedControl"] { display: none !important; }

/* ══════════════════
   TOPBAR (injected via markdown)
══════════════════ */
.cs-topbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    margin: -1.5rem -1rem 1.5rem -1rem;
}
.cs-topbar-left {
    flex: 1;
    max-width: 400px;
    position: relative;
}
.cs-topbar-search-icon {
    position: absolute;
    left: 11px;
    top: 50%;
    transform: translateY(-50%);
    font-family: 'Material Symbols Outlined';
    font-size: 17px;
    color: #94a3b8;
    pointer-events: none;
    font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
    line-height: 1;
}
.cs-topbar-search {
    width: 100%;
    padding: 8px 14px 8px 36px;
    background: #f1f5f9;
    border: none;
    border-radius: 10px;
    font-size: 0.875rem;
    font-family: 'DM Sans', sans-serif;
    color: #0f172a;
    outline: none;
    transition: background 0.15s, box-shadow 0.15s;
}
.cs-topbar-search:focus {
    background: #fff;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2);
}
.cs-topbar-search::placeholder { color: #94a3b8; }
.cs-topbar-right {
    display: flex;
    align-items: center;
    gap: 10px;
}
.cs-sync-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #2563EB;
    color: #fff !important;
    padding: 8px 18px;
    border-radius: 10px;
    font-size: 0.875rem;
    font-weight: 700;
    font-family: 'DM Sans', sans-serif;
    border: none;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(37,99,235,0.28);
    transition: background 0.15s;
    text-decoration: none !important;
    white-space: nowrap;
}
.cs-sync-btn:hover { background: #1d4ed8; }
.cs-sync-btn .mi {
    font-family: 'Material Symbols Outlined';
    font-size: 17px;
    line-height: 1;
    font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
}
.cs-notif {
    width: 36px; height: 36px;
    border-radius: 9px;
    border: 1px solid #e2e8f0;
    background: #fff;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; color: #64748b;
    font-family: 'Material Symbols Outlined';
    font-size: 20px; line-height: 1;
    font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
    transition: background 0.15s;
}
.cs-notif:hover { background: #f8fafc; }

/* ══════════════════
   STAT CARDS
══════════════════ */
.cs-stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 18px;
    margin-bottom: 24px;
}
.cs-stat-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 22px 22px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.cs-stat-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 14px;
}
.cs-stat-icon {
    width: 42px; height: 42px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
}
.cs-stat-icon .mi {
    font-family: 'Material Symbols Outlined';
    font-size: 22px; line-height: 1;
    font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
}
.cs-stat-trend { font-size: 0.72rem; font-weight: 600; line-height: 1.3; }
.cs-stat-label { font-size: 0.82rem; color: #64748b; font-weight: 500; margin-bottom: 5px; }
.cs-stat-value { font-size: 2rem; font-weight: 700; color: #0f172a; line-height: 1; letter-spacing: -0.5px; }

/* ══════════════════
   SECTION HEADER
══════════════════ */
.cs-section-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}
.cs-section-title { font-size: 1rem; font-weight: 700; color: #0f172a; }
.cs-view-all {
    font-size: 0.85rem; font-weight: 600; color: #2563EB;
    background: none; border: none; cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    text-decoration: none !important;
}
.cs-view-all:hover { text-decoration: underline !important; }

/* ══════════════════
   TABLE CARD
══════════════════ */
.cs-table-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.cs-tbl {
    width: 100%;
    border-collapse: collapse;
    font-family: 'DM Sans', sans-serif;
}
.cs-tbl th {
    background: #f8fafc;
    padding: 11px 22px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    text-align: left;
    white-space: nowrap;
    border-bottom: 1px solid #e2e8f0;
}
.cs-tbl td {
    padding: 15px 22px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.875rem;
    color: #334155;
    vertical-align: middle;
}
.cs-tbl tr:last-child td { border-bottom: none; }
.cs-tbl tr:hover td { background: #fafbfc; }
.cs-co-cell { display: flex; align-items: center; gap: 11px; }
.cs-co-logo {
    width: 32px; height: 32px;
    border-radius: 8px;
    background: #f1f5f9;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; color: #475569;
    flex-shrink: 0;
}
.cs-co-name  { font-weight: 600; color: #0f172a; font-size: 0.9rem; }
.cs-pos      { color: #64748b; }
.cs-date     { color: #64748b; font-size: 0.82rem; white-space: nowrap; }

/* Badges */
.cs-badge {
    display: inline-flex; align-items: center; justify-content: center;
    padding: 3px 12px; border-radius: 9999px;
    font-size: 0.72rem; font-weight: 700;
}
.cs-b-Applied   { background: #f1f5f9; color: #475569; }
.cs-b-Interview { background: #dbeafe; color: #1d4ed8; }
.cs-b-Offer     { background: #dcfce7; color: #15803d; }
.cs-b-Rejected  { background: #fee2e2; color: #dc2626; }

/* Recruiter cell */
.cs-rec-name  { font-weight: 600; color: #0f172a; font-size: 0.85rem; display: block; }
.cs-rec-title { color: #64748b; font-size: 0.72rem; display: block; margin-top: 1px; }
.cs-li-btn {
    display: inline-flex; align-items: center; gap: 4px;
    background: #fff; color: #2563EB;
    border: 1px solid #bfdbfe; border-radius: 6px;
    padding: 2px 8px; font-size: 0.68rem; font-weight: 700;
    text-decoration: none !important; margin-top: 3px;
}
.cs-no-data   { color: #cbd5e1; font-size: 0.78rem; font-style: italic; }
.cs-email-txt { font-size: 0.8rem; font-weight: 500; color: #334155; word-break: break-all; }

/* Empty state */
.cs-tbl .cs-empty td {
    text-align: center; color: #94a3b8;
    padding: 60px 22px !important; font-size: 0.9rem;
}

/* ══════════════════
   CREDIT CARD
══════════════════ */
.cs-credit-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.cs-credit-hdr {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
}
.cs-credit-hdr-title { font-size: 1rem; font-weight: 700; color: #0f172a; }
.cs-refresh {
    width: 30px; height: 30px;
    border-radius: 8px; border: 1px solid #e2e8f0; background: #fff;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; color: #64748b;
    font-family: 'Material Symbols Outlined'; font-size: 17px; line-height: 1;
    font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
}
.cs-refresh:hover { background: #f8fafc; }
.cs-credit-item { margin-bottom: 18px; }
.cs-credit-item:last-of-type { margin-bottom: 0; }
.cs-credit-row {
    display: flex; justify-content: space-between; align-items: flex-end;
    margin-bottom: 7px;
}
.cs-credit-name  { font-size: 0.875rem; font-weight: 700; color: #0f172a; }
.cs-credit-sub   { font-size: 0.7rem; color: #94a3b8; margin-top: 2px; }
.cs-credit-count { font-size: 0.75rem; font-weight: 700; color: #334155; }
.cs-bar-bg  { height: 8px; background: #f1f5f9; border-radius: 9999px; overflow: hidden; }
.cs-bar-fill{ height: 100%; border-radius: 9999px; }
.cs-credit-divider { height: 1px; background: #f1f5f9; margin: 18px 0; }
.cs-upgrade {
    width: 100%; padding: 11px;
    border-radius: 10px; border: 1px solid #e2e8f0;
    background: #fff; font-size: 0.875rem; font-weight: 700; color: #0f172a;
    cursor: pointer; font-family: 'DM Sans', sans-serif;
    transition: background 0.15s;
}
.cs-upgrade:hover { background: #f8fafc; }

/* PRO TIP */
.cs-pro-tip {
    background: rgba(37,99,235,0.05);
    border: 1px solid rgba(37,99,235,0.15);
    border-radius: 16px; padding: 18px;
    display: flex; gap: 12px; align-items: flex-start;
    margin-top: 14px;
}
.cs-pro-tip-icon  { font-size: 1.4rem; flex-shrink: 0; line-height: 1; }
.cs-pro-tip-title { font-size: 0.9rem; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
.cs-pro-tip-text  { font-size: 0.8rem; color: #475569; line-height: 1.6; }

/* ══════════════════
   STREAMLIT WIDGET OVERRIDES
══════════════════ */
div.stButton > button {
    background: #fff !important;
    color: #475569 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 8px 14px !important;
    transition: all 0.15s !important;
}
div.stButton > button:hover {
    background: #f8fafc !important;
    border-color: #cbd5e1 !important;
}
div.stButton > button[kind="primary"] {
    background: #2563EB !important;
    color: #fff !important;
    border-color: #2563EB !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
}
div.stButton > button[kind="primary"]:hover { background: #1d4ed8 !important; }
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
}
div[data-testid="stDateInput"] input {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #2563EB !important;
    border-bottom-color: #2563EB !important;
}
.stAlert { border-radius: 10px !important; }
hr { border-color: #e2e8f0 !important; }

/* ══════════════════
   RESPONSIVE
══════════════════ */
@media (max-width: 1100px) {
    .cs-stats-row { grid-template-columns: repeat(2, 1fr); gap: 14px; }
}
@media (max-width: 768px) {
    .cs-stats-row { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .cs-topbar { padding: 0 14px; }
    .cs-topbar-left { max-width: 200px; }
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown(f"""
    <div style="padding:20px 16px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f1f5f9;">
      <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;
                  display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <span style="font-family:'Material Symbols Outlined';font-size:17px;color:#fff;
                     font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">
          sync_alt
        </span>
      </div>
      <span style="font-size:1.1rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;
                   font-family:'DM Sans',sans-serif;">CareerSync</span>
    </div>
    """, unsafe_allow_html=True)

    # Active nav item (Dashboard)
    st.markdown("""
    <div style="padding:12px 12px 8px;">
      <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                  border-radius:8px;background:rgba(37,99,235,0.08);
                  color:#2563EB;font-weight:600;font-size:0.9rem;
                  font-family:'DM Sans',sans-serif;">
        <span style="font-family:'Material Symbols Outlined';font-size:20px;
                     font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">
          dashboard
        </span>
        Dashboard
      </div>
    </div>
    <div style="padding:0 12px;display:flex;flex-direction:column;gap:2px;">
    """, unsafe_allow_html=True)

    # Nav items
    nav_pages = [
        ("work",      "Applications",      "pages/2_Applications.py"),
        ("mail",      "Cold Email",         "pages/3_Cold_Email.py"),
        ("plumbing",  "Research Pipeline",  "pages/4_Pipeline.py"),
        ("settings",  "Settings",           "pages/5_Settings.py"),
    ]
    for icon, label, path in nav_pages:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                    border-radius:8px;color:#64748b;font-size:0.9rem;font-weight:500;
                    font-family:'DM Sans',sans-serif;">
          <span style="font-family:'Material Symbols Outlined';font-size:20px;
                       font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">
            {icon}
          </span>
          {label}
        </div>
        """, unsafe_allow_html=True)
        if st.button(label, key=f"nav_{label}"):
            try:
                st.switch_page(path)
            except Exception:
                st.info(f"{label} coming soon!")

    st.markdown("</div>", unsafe_allow_html=True)

    # Spacer + divider
    st.markdown("""
    <div style="flex:1;"></div>
    <div style="height:1px;background:#f1f5f9;margin:12px 0;"></div>
    """, unsafe_allow_html=True)

    # User card
    st.markdown(f"""
    <div style="padding:8px 16px 12px;">
      <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;
                  border-radius:10px;background:#f8fafc;">
        <div style="width:36px;height:36px;border-radius:50%;background:#e0e7ff;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;color:#3730a3;font-size:0.875rem;flex-shrink:0;">
          {avatar_let}
        </div>
        <div style="min-width:0;">
          <div style="font-size:0.85rem;font-weight:600;color:#0f172a;font-family:'DM Sans',sans-serif;
                      overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name_disp}</div>
          <div style="font-size:0.7rem;color:#64748b;font-family:'DM Sans',sans-serif;
                      overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{email_disp}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        _logout()
        st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# STICKY TOPBAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="cs-topbar">
  <div class="cs-topbar-left">
    <span class="cs-topbar-search-icon">search</span>
    <input class="cs-topbar-search" id="cs-search" type="text"
           placeholder="Search applications, companies..." />
  </div>
  <div class="cs-topbar-right">
    <button class="cs-sync-btn" id="cs-sync-btn">
      <span class="mi">mail</span> Sync Gmail
    </button>
    <div class="cs-notif">notifications</div>
  </div>
</div>
<script>
(function(){
  // Wire topbar Sync Gmail button to trigger the hidden Streamlit sync button
  document.getElementById('cs-sync-btn').addEventListener('click', function(){
    var btns = window.parent.document.querySelectorAll('[data-testid="stButton"] button');
    for(var i=0;i<btns.length;i++){
      if(btns[i].innerText.trim().includes('Sync Gmail')){
        btns[i].click(); break;
      }
    }
  });
})();
</script>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HIDDEN ACTION BUTTONS (functional — triggered via topbar JS or direct click)
# ══════════════════════════════════════════════════════════════════════════════
b1, b2, b3 = st.columns([1.2, 1.8, 1.6])
with b1: sync_clicked   = st.button("🔄 Sync Gmail",             use_container_width=True, type="primary")
with b2: enrich_clicked = st.button("🔍 Find Missing Recruiters", use_container_width=True)
with b3: force_enrich   = st.button("⚡ Force Re-Enrich ALL",     use_container_width=True)

# ── Enrich helper ─────────────────────────────────────────────────────────────
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
# DATA LOAD
# ══════════════════════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state.page = 0

apps = get_all_applications()
df   = pd.DataFrame(apps) if apps else pd.DataFrame(columns=[
    "id","company_name","position","stage","applied_date","last_updated",
    "email_subject","recruiter_email","recruiter_name","recruiter_title","linkedin_url"])
for col in ["recruiter_email","recruiter_name","recruiter_title","linkedin_url"]:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].fillna("").astype(str)
if "stage" not in df.columns: df["stage"] = "Applied"

total      = len(df)
applied    = len(df[df.stage=="Applied"])   if not df.empty else 0
interviews = len(df[df.stage=="Interview"]) if not df.empty else 0
offers     = len(df[df.stage=="Offer"])     if not df.empty else 0
rejected   = len(df[df.stage=="Rejected"])  if not df.empty else 0
with_rec   = len(df[df.linkedin_url.str.len()>0]) if not df.empty else 0

# ══════════════════════════════════════════════════════════════════════════════
# STAT CARDS — exact design: icon box + trend label + stat label + big number
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="cs-stats-row">

  <div class="cs-stat-card">
    <div class="cs-stat-top">
      <div class="cs-stat-icon" style="background:rgba(37,99,235,0.1);">
        <span class="mi" style="color:#2563EB;">description</span>
      </div>
      <span class="cs-stat-trend" style="color:#10b981;">+12% vs mo</span>
    </div>
    <div class="cs-stat-label">Total Applications</div>
    <div class="cs-stat-value">{total}</div>
  </div>

  <div class="cs-stat-card">
    <div class="cs-stat-top">
      <div class="cs-stat-icon" style="background:#fef3c7;">
        <span class="mi" style="color:#d97706;">event</span>
      </div>
      <span class="cs-stat-trend" style="color:#d97706;">4 this week</span>
    </div>
    <div class="cs-stat-label">Interviews Scheduled</div>
    <div class="cs-stat-value">{interviews}</div>
  </div>

  <div class="cs-stat-card">
    <div class="cs-stat-top">
      <div class="cs-stat-icon" style="background:#dcfce7;">
        <span class="mi" style="color:#16a34a;">verified</span>
      </div>
      <span class="cs-stat-trend" style="color:#10b981;">Highest ever</span>
    </div>
    <div class="cs-stat-label">Offers Received</div>
    <div class="cs-stat-value">{offers}</div>
  </div>

  <div class="cs-stat-card">
    <div class="cs-stat-top">
      <div class="cs-stat-icon" style="background:#ede9fe;">
        <span class="mi" style="color:#7c3aed;">groups</span>
      </div>
      <span class="cs-stat-trend" style="color:#94a3b8;">Total in CRM</span>
    </div>
    <div class="cs-stat-label">Recruiters Found</div>
    <div class="cs-stat-value">{with_rec}</div>
  </div>

</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SEARCH / FILTER
# ══════════════════════════════════════════════════════════════════════════════
f1, f2, f3 = st.columns([3, 1, 1])
with f1: search  = st.text_input("🔍 Search", placeholder="Company or Job Title...", label_visibility="collapsed")
with f2: stage_f = st.selectbox("Stage",    ["All","Applied","Interview","Offer","Rejected"], label_visibility="collapsed")
with f3: rec_f   = st.selectbox("Recruiter",["All","Found","Not Found"], label_visibility="collapsed")

filtered = df.copy()
if search:
    m = (filtered.company_name.str.contains(search,case=False,na=False) |
         filtered.position.str.contains(search,case=False,na=False))
    filtered = filtered[m]
if stage_f != "All": filtered = filtered[filtered.stage==stage_f]
if rec_f == "Found":     filtered = filtered[filtered.linkedin_url.str.len()>0]
elif rec_f == "Not Found": filtered = filtered[filtered.linkedin_url.str.len()==0]

fkey = f"{search}|{stage_f}|{rec_f}"
if st.session_state.get("_fkey") != fkey:
    st.session_state.page = 0; st.session_state._fkey = fkey

ROWS = 8; total_rows = len(filtered); total_pages = max(1, math.ceil(total_rows/ROWS))
if st.session_state.page >= total_pages: st.session_state.page = total_pages - 1
cur = st.session_state.page; ps = cur*ROWS; pe = min(ps+ROWS, total_rows)
page_df = filtered.iloc[ps:pe]

# ══════════════════════════════════════════════════════════════════════════════
# TABLE + CREDITS — 2-column layout matching design
# ══════════════════════════════════════════════════════════════════════════════
BADGE_CLS = {
    "Applied":   "cs-b-Applied",
    "Interview": "cs-b-Interview",
    "Offer":     "cs-b-Offer",
    "Rejected":  "cs-b-Rejected",
}

def build_table(rows_df):
    head = """
    <div class="cs-table-card">
    <table class="cs-tbl">
    <thead><tr>
      <th>Company</th>
      <th>Position</th>
      <th>Date Applied</th>
      <th>Stage</th>
      <th>Recruiter</th>
      <th>Email</th>
    </tr></thead><tbody>"""

    if rows_df.empty:
        return (head +
                '<tr class="cs-empty"><td colspan="6">'
                '&#128235; No applications yet. Hit <strong>Sync Gmail</strong> to get started!'
                '</td></tr></tbody></table></div>')

    rows = ""
    for _, r in rows_df.iterrows():
        stage  = str(r.get("stage", "Applied"))
        bcls   = BADGE_CLS.get(stage, "cs-b-Applied")
        rec_n  = str(r.get("recruiter_name",  "")).strip()
        rec_t  = str(r.get("recruiter_title", "")).strip()
        li     = str(r.get("linkedin_url",    "")).strip()
        em     = str(r.get("recruiter_email", "")).strip()
        let    = str(r["company_name"])[0].upper() if r["company_name"] else "?"

        if rec_n and li:
            rc = (f'<span class="cs-rec-name">&#128100; {rec_n}</span>'
                  f'<span class="cs-rec-title">{rec_t}</span>'
                  f'<a href="{li}" target="_blank" class="cs-li-btn">&#128279; LinkedIn</a>')
        elif rec_n:
            rc = f'<span class="cs-rec-name">&#128100; {rec_n}</span><span class="cs-rec-title">{rec_t}</span>'
        elif li:
            rc = f'<a href="{li}" target="_blank" class="cs-li-btn">&#128279; LinkedIn</a>'
        else:
            rc = '<span class="cs-no-data">Not found</span>'

        ec = f'<span class="cs-email-txt">{em}</span>' if em else '<span class="cs-no-data">&#8212;</span>'

        rows += f"""<tr>
          <td><div class="cs-co-cell">
            <div class="cs-co-logo">{let}</div>
            <span class="cs-co-name">{r["company_name"]}</span>
          </div></td>
          <td><span class="cs-pos">{r["position"]}</span></td>
          <td><span class="cs-date">{r.get("applied_date","")}</span></td>
          <td><span class="cs-badge {bcls}">{stage}</span></td>
          <td>{rc}</td>
          <td>{ec}</td>
        </tr>"""

    return head + rows + "</tbody></table></div>"


def build_credits():
    if not _CREDITS_OK:
        return '<div class="cs-credit-card"><p style="color:#94a3b8;font-size:0.875rem;">Credits tracker not available.</p></div>'

    state = credits_get_all()
    SHOW = [
        ("google_cse", "Google Custom Search", "Search API calls",       "#2563EB"),
        ("hunter",     "Hunter.io",            "Email finding credits",   "#10b981"),
        ("groq",       "Groq AI",              "AI generation calls",     "#8b5cf6"),
    ]
    items = ""
    for key, name, sub, color in SHOW:
        svc   = CREDIT_SERVICES.get(key, {})
        entry = state.get(key, {})
        tot   = svc.get("total", 100)
        used  = entry.get("used", 0)
        pct   = max(2, int((used/tot)*100)) if tot > 0 else 2
        items += f"""
        <div class="cs-credit-item">
          <div class="cs-credit-row">
            <div>
              <div class="cs-credit-name">{name}</div>
              <div class="cs-credit-sub">{sub}</div>
            </div>
            <span class="cs-credit-count">{used:,} / {tot:,}</span>
          </div>
          <div class="cs-bar-bg">
            <div class="cs-bar-fill" style="background:{color};width:{pct}%;"></div>
          </div>
        </div>"""

    return f"""
    <div class="cs-credit-card">
      <div class="cs-credit-hdr">
        <span class="cs-credit-hdr-title">Credit Usage</span>
        <button class="cs-refresh">refresh</button>
      </div>
      {items}
      <div class="cs-credit-divider"></div>
      <button class="cs-upgrade">Upgrade Plan</button>
    </div>
    <div class="cs-pro-tip">
      <span class="cs-pro-tip-icon">&#128161;</span>
      <div>
        <div class="cs-pro-tip-title">Pro Tip</div>
        <div class="cs-pro-tip-text">
          Syncing your Gmail daily improves response tracking accuracy by up to 45%.
        </div>
      </div>
    </div>"""


# Render 2-col layout
col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    st.markdown(f"""
    <div class="cs-section-hdr">
      <span class="cs-section-title">
        Recent Applications
        <span style="color:#94a3b8;font-weight:400;font-size:0.875rem;">({total_rows})</span>
      </span>
      <button class="cs-view-all">View All</button>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(build_table(page_df), unsafe_allow_html=True)

    # Pagination
    if total_pages > 1:
        st.markdown(f"<p style='font-size:0.78rem;color:#94a3b8;margin:8px 0 6px;'>"
                    f"Showing {ps+1}–{pe} of {total_rows}</p>", unsafe_allow_html=True)
        def slots(c, t):
            if t <= 7: return list(range(t))
            r = [0]; lo, hi = max(1,c-2), min(t-2,c+2)
            if lo > 1: r.append(None)
            r.extend(range(lo, hi+1))
            if hi < t-2: r.append(None)
            r.append(t-1); return r
        sl = slots(cur, total_pages)
        bc = st.columns(2+len(sl))
        with bc[0]:
            if st.button("◀", key="pg_prev", disabled=(cur==0), use_container_width=True):
                st.session_state.page = cur-1; st.rerun()
        for i, s in enumerate(sl):
            with bc[i+1]:
                if s is None:
                    st.markdown("<div style='text-align:center;padding-top:6px;color:#94a3b8;'>…</div>",
                                unsafe_allow_html=True)
                else:
                    if st.button(str(s+1), key=f"pg_{s}",
                                 type="primary" if s==cur else "secondary",
                                 use_container_width=True):
                        st.session_state.page = s; st.rerun()
        with bc[-1]:
            if st.button("▶", key="pg_next", disabled=(cur==total_pages-1), use_container_width=True):
                st.session_state.page = cur+1; st.rerun()

with col_right:
    st.markdown(build_credits(), unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# AI COLD EMAIL GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>"
            "✨ AI Cold Email Generator</h3>", unsafe_allow_html=True)

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
        greet = f"Hi {sel_rec['rec_name'].split()[0]}," if sel_rec["rec_name"] else "Hi,"
        prompt = (f"Write a {tone.lower()} cold follow-up email from a job seeker "
                  f"to a recruiter at {sel_rec['company']} about the {sel_rec['position']} role.\n"
                  f"Opening: {greet}\nRules:\n- Max 130 words\n- First line: Subject: <subject>\n"
                  f"- Blank line then body starting with {greet}\n- No brackets\n"
                  f"- Close: Best regards,\n- Tone: {tone.lower()}")
        with st.spinner("✨ Writing..."):
            try:
                import requests as _req
                from config import GROQ_API_KEY as _gk
                resp = _req.post("https://api.groq.com/openai/v1/chat/completions",
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
                    elif past:
                        body.append(ln)
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
            to = st.session_state.get("ai_email_to","")
            mailto = (f"mailto:{to}?subject={subj_e.replace(' ','%20')}"
                      f"&body={body_e[:500].replace(chr(10),'%0A').replace(' ','%20')}")
            st.link_button("📨 Open in Mail", mailto)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MANAGE APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<h3 style='font-size:1.1rem;font-weight:700;color:#0f172a;margin-bottom:4px;'>"
            "⚙️ Manage Applications</h3>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["✏️ Update Stage", "🔍 Find Recruiter", "➕ Add Manually", "🗑️ Delete"])

with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty:
        st.info("No applications yet. Sync your Gmail to get started!")
    else:
        opts = {f"{r['company_name']} — {r['position']}": r["id"] for _, r in df.iterrows()}
        c1, c2 = st.columns(2)
        with c1: sel = st.selectbox("Application", list(opts.keys()), key="t1_sel")
        with c2: ns  = st.selectbox("New Stage", ["Applied","Interview","Offer","Rejected"], key="t1_ns")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Update Stage", key="t1_btn", type="primary"):
            update_stage(opts[sel], ns)
            st.success(f"Updated to **{ns}**.")
            st.rerun()

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty:
        st.info("No applications yet.")
    else:
        opts2 = {f"{r['company_name']} — {r['position']}": (r["id"], r["company_name"])
                 for _, r in df.iterrows()}
        sel2 = st.selectbox("Application", list(opts2.keys()), key="t2_sel")
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
                    update_recruiter_info(app_id2, me, mn, mt, ml)
                    st.success("Saved!")
                    st.rerun()

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
            st.success(f"Added **{mt2}** at **{mc}**.")
            st.rerun()
        else:
            st.warning("Fill in Company and Job Title.")

with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty:
        st.info("Nothing to delete.")
    else:
        d_opts = {f"{r['company_name']} — {r['position']}": r["id"] for _, r in df.iterrows()}
        d_sel  = st.selectbox("Select to delete", list(d_opts.keys()), key="d_sel")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Delete", type="primary", key="d_btn"):
            delete_application(d_opts[d_sel])
            st.success("Deleted.")
            st.rerun()

st.divider()
st.caption("CareerSync v3.0 · Gmail · Groq AI · Hunter.io · Apollo.io · Supabase · ❤️")