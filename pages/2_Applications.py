"""
pages/2_Applications.py — CareerSync Job Applications
UI: Exact design — clean table with Company/Job Title/Applied Date/Stage/Recruiter Found/Actions
    Click any row → full detail modal popup
    Search bar + Stage filter + Filters button in topbar
    + Add Application button
Data: Supabase applications table (same as Dashboard)
"""

import os, sys, math, json, re, requests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import streamlit as st
import pandas as pd

from auth import get_user_by_id, inject_gmail_env

st.set_page_config(
    page_title="CareerSync — Applications",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
def _restore():
    if st.session_state.get("user"): return True
    uid = st.query_params.get("uid", "")
    if uid:
        user = get_user_by_id(uid)
        if user:
            st.session_state["user"]    = user
            st.session_state["user_id"] = uid
            return True
    return False

def _logout():
    for k in ["user","user_id"]: st.session_state.pop(k, None)
    st.query_params.clear()
    st.switch_page("app.py")

if not _restore():
    st.switch_page("app.py"); st.stop()

user = st.session_state["user"]
st.query_params["uid"] = user["id"]
inject_gmail_env(user)

# ── Imports after auth ────────────────────────────────────────────────────────
from database import (get_all_applications, update_stage, delete_application,
                      upsert_application, update_recruiter_info)
from recruiter_finder import enrich_application

def _get(key, default=""):
    try:
        val = st.secrets.get(key, ""); 
        if val: return val
    except Exception: pass
    return os.getenv(key, default)

GROQ_KEY = _get("GROQ_API_KEY")

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("app2_page", 0), ("app2_search", ""), ("app2_stage", "All Stages"),
             ("app2_selected", None), ("app2_modal_open", False),
             ("app2_add_open", False)]:
    if k not in st.session_state: st.session_state[k] = v

user_id    = user["id"]
name_disp  = user.get("name","User")
email_disp = user.get("email","")
avatar_let = name_disp[0].upper() if name_disp else "U"

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — exact same design as Dashboard
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');
    [data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important;min-width:240px!important;max-width:240px!important;}
    [data-testid="stSidebar"] .stButton>button{
      text-align:left!important;justify-content:flex-start!important;
      background:transparent!important;color:#475569!important;
      border:none!important;box-shadow:none!important;font-size:0.9rem!important;
      font-weight:500!important;padding:9px 12px!important;border-radius:8px!important;
      width:100%!important;font-family:'DM Sans',sans-serif!important;}
    [data-testid="stSidebar"] .stButton>button:hover{background:#f8fafc!important;color:#0f172a!important;}
    [data-testid="collapsedControl"]{display:none!important;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:20px 16px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f1f5f9;">
      <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <span style="font-family:'Material Symbols Outlined';font-size:17px;color:#fff;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">sync_alt</span>
      </div>
      <div>
        <div style="font-size:1rem;font-weight:700;color:#0f172a;font-family:'DM Sans',sans-serif;line-height:1.2;">CareerSync</div>
        <div style="font-size:0.7rem;color:#94a3b8;font-family:'DM Sans',sans-serif;">Manage your career</div>
      </div>
    </div>
    <div style="padding:12px 12px 8px;">
    """, unsafe_allow_html=True)

    nav_pages = [
        ("dashboard", "Dashboard",        "pages/1_Dashboard.py"),
        ("work",      "Applications",     "pages/2_Applications.py"),
        ("business",  "Companies",        "pages/4_Pipeline.py"),
        ("event",     "Interviews",       "pages/4_Pipeline.py"),
        ("settings",  "Settings",         "pages/5_Settings.py"),
    ]

    for icon, label, path in nav_pages:
        is_active = (label == "Applications")
        if is_active:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
                        background:rgba(37,99,235,0.08);color:#2563EB;font-weight:600;font-size:0.9rem;
                        font-family:'DM Sans',sans-serif;margin-bottom:2px;">
              <span style="font-family:'Material Symbols Outlined';font-size:20px;
                           font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">{icon}</span>
              {label}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
                        color:#64748b;font-size:0.9rem;font-weight:500;font-family:'DM Sans',sans-serif;margin-bottom:2px;">
              <span style="font-family:'Material Symbols Outlined';font-size:20px;
                           font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">{icon}</span>
              {label}
            </div>""", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{label}"):
                try: st.switch_page(path)
                except: st.info(f"{label} coming soon!")

    # System section
    st.markdown("""
    <div style="padding:16px 12px 4px;font-size:0.65rem;font-weight:700;color:#94a3b8;
                text-transform:uppercase;letter-spacing:0.8px;font-family:'DM Sans',sans-serif;">System</div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
                color:#64748b;font-size:0.9rem;font-weight:500;font-family:'DM Sans',sans-serif;">
      <span style="font-family:'Material Symbols Outlined';font-size:20px;
                   font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">settings</span>
      Settings
    </div>""", unsafe_allow_html=True)
    if st.button("Settings ", key="nav_set2"):
        try: st.switch_page("pages/5_Settings.py")
        except: pass

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:#f1f5f9;margin:8px 0;'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:8px 16px 12px;">
      <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:#f8fafc;">
        <div style="width:36px;height:36px;border-radius:50%;background:#e0e7ff;display:flex;align-items:center;
                    justify-content:center;font-weight:700;color:#3730a3;font-size:0.875rem;flex-shrink:0;">{avatar_let}</div>
        <div style="min-width:0;">
          <div style="font-size:0.85rem;font-weight:600;color:#0f172a;font-family:'DM Sans',sans-serif;
                      overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name_disp}</div>
          <div style="font-size:0.7rem;color:#64748b;font-family:'DM Sans',sans-serif;">Pro Account</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪  Logout", key="sb_logout", use_container_width=True):
        _logout()

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
  background:#f8fafc!important;font-family:'DM Sans',sans-serif!important;color:#0f172a!important;}
.block-container{padding-top:0!important;padding-bottom:2rem!important;max-width:100%!important;padding-left:0!important;padding-right:0!important;}
[data-testid="stVerticalBlock"]{gap:0!important;}

/* ── TOPBAR ── */
.app-topbar{
  height:60px;background:#fff;border-bottom:1px solid #e2e8f0;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 28px;position:sticky;top:0;z-index:50;
}
.topbar-left{display:flex;align-items:center;gap:14px;}
.topbar-title{font-size:1.25rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;}
.topbar-count{font-size:0.82rem;font-weight:500;color:#64748b;
  background:#f1f5f9;padding:3px 10px;border-radius:9999px;}
.topbar-right{display:flex;align-items:center;gap:10px;}
.notif-btn{width:36px;height:36px;border-radius:9px;border:1px solid #e2e8f0;
  background:#fff;display:flex;align-items:center;justify-content:center;
  cursor:pointer;color:#64748b;font-family:'Material Symbols Outlined';
  font-size:20px;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  transition:background 0.15s;}
.notif-btn:hover{background:#f8fafc;}
.add-btn{display:inline-flex;align-items:center;gap:6px;background:#2563EB;color:#fff;
  padding:9px 18px;border-radius:10px;font-size:0.875rem;font-weight:700;
  font-family:'DM Sans',sans-serif;border:none;cursor:pointer;
  box-shadow:0 2px 8px rgba(37,99,235,0.28);transition:background 0.15s;}
.add-btn:hover{background:#1d4ed8;}
.add-btn .mi{font-family:'Material Symbols Outlined';font-size:17px;line-height:1;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}

/* ── CONTENT AREA ── */
.app-content{padding:24px 28px;}

/* ── SEARCH & FILTER BAR ── */
.filter-row{display:flex;align-items:center;gap:12px;margin-bottom:20px;}
.search-wrap{position:relative;flex:1;max-width:500px;}
.search-icon{position:absolute;left:12px;top:50%;transform:translateY(-50%);
  font-family:'Material Symbols Outlined';font-size:17px;color:#94a3b8;
  pointer-events:none;font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;}
.search-input{width:100%;padding:9px 14px 9px 38px;background:#fff;
  border:1px solid #e2e8f0;border-radius:10px;font-size:0.875rem;
  font-family:'DM Sans',sans-serif;color:#0f172a;outline:none;
  transition:border-color 0.15s,box-shadow 0.15s;}
.search-input:focus{border-color:#2563EB;box-shadow:0 0 0 3px rgba(37,99,235,0.1);}
.search-input::placeholder{color:#94a3b8;}
.stage-select{padding:9px 14px;background:#fff;border:1px solid #e2e8f0;
  border-radius:10px;font-size:0.875rem;font-family:'DM Sans',sans-serif;
  color:#0f172a;outline:none;cursor:pointer;min-width:140px;
  appearance:none;-webkit-appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;
  padding-right:32px;}
.filters-btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;
  background:#fff;border:1px solid #e2e8f0;border-radius:10px;
  font-size:0.875rem;font-weight:600;color:#475569;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:all 0.15s;white-space:nowrap;}
.filters-btn .mi{font-family:'Material Symbols Outlined';font-size:16px;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;}
.filters-btn:hover{background:#f8fafc;border-color:#cbd5e1;}

/* ── TABLE CARD ── */
.tbl-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.tbl-table{width:100%;border-collapse:collapse;}
.tbl-table th{
  padding:13px 20px;font-size:0.7rem;font-weight:700;color:#94a3b8;
  text-transform:uppercase;letter-spacing:0.7px;text-align:left;
  white-space:nowrap;border-bottom:1px solid #f1f5f9;background:#fff;}
.tbl-table td{
  padding:16px 20px;border-bottom:1px solid #f1f5f9;font-size:0.875rem;
  color:#334155;vertical-align:middle;}
.tbl-table tr:last-child td{border-bottom:none;}
.tbl-table tbody tr{cursor:pointer;transition:background 0.12s;}
.tbl-table tbody tr:hover td{background:#f8fafc;}

/* Company cell */
.co-cell{display:flex;align-items:center;gap:12px;}
.co-avatar{width:36px;height:36px;border-radius:9px;background:#f1f5f9;
  display:flex;align-items:center;justify-content:center;
  font-size:0.8rem;font-weight:700;color:#475569;flex-shrink:0;
  border:1px solid #e8edf2;}
.co-name{font-weight:600;color:#0f172a;font-size:0.9rem;}

/* Stage badges */
.stage-badge{display:inline-flex;align-items:center;gap:5px;
  padding:4px 12px;border-radius:7px;font-size:0.78rem;font-weight:600;}
.stage-Applied    {background:#f1f5f9;color:#475569;}
.stage-Interview  {background:#dbeafe;color:#1d4ed8;}
.stage-Interviewing{background:#dbeafe;color:#1d4ed8;}
.stage-Offer      {background:#dcfce7;color:#15803d;}
.stage-Rejected   {background:#fee2e2;color:#dc2626;}
.stage-Wishlist   {background:#fce7f3;color:#be185d;}

/* Recruiter dot */
.rec-dot-yes{width:22px;height:22px;border-radius:50%;background:#22c55e;
  display:inline-flex;align-items:center;justify-content:center;}
.rec-dot-yes::after{content:'✓';color:#fff;font-size:12px;font-weight:700;}
.rec-dot-no{width:22px;height:22px;border-radius:50%;background:#e2e8f0;display:inline-block;}

/* View Details link */
.view-details{color:#2563EB;font-weight:600;font-size:0.875rem;text-decoration:none!important;
  cursor:pointer;border:none;background:none;font-family:'DM Sans',sans-serif;
  padding:0;transition:color 0.15s;}
.view-details:hover{color:#1d4ed8;text-decoration:underline!important;}

/* ── PAGINATION ── */
.pagination-row{
  display:flex;align-items:center;justify-content:space-between;
  padding:14px 20px;border-top:1px solid #f1f5f9;
}
.pg-info{font-size:0.82rem;color:#64748b;}
.pg-btns{display:flex;align-items:center;gap:4px;}
.pg-btn{width:32px;height:32px;border-radius:7px;border:1px solid #e2e8f0;
  background:#fff;font-size:0.82rem;font-weight:600;color:#475569;
  cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
  font-family:'DM Sans',sans-serif;transition:all 0.12s;}
.pg-btn:hover:not([disabled]){background:#f8fafc;border-color:#cbd5e1;}
.pg-btn.active{background:#2563EB;color:#fff;border-color:#2563EB;}
.pg-btn[disabled]{opacity:0.4;cursor:not-allowed;}
.pg-btn-nav{width:30px;height:32px;border-radius:7px;border:1px solid #e2e8f0;
  background:#fff;cursor:pointer;display:inline-flex;align-items:center;
  justify-content:center;color:#64748b;font-size:13px;transition:all 0.12s;}
.pg-btn-nav:hover:not([disabled]){background:#f8fafc;}
.pg-btn-nav[disabled]{opacity:0.35;cursor:not-allowed;}

/* ══ MODAL OVERLAY ══ */
.modal-overlay{
  position:fixed;inset:0;background:rgba(15,23,42,0.45);
  z-index:9998;display:flex;align-items:center;justify-content:center;
  padding:20px;backdrop-filter:blur(2px);
}
.modal-box{
  background:#fff;border-radius:20px;width:100%;max-width:680px;
  max-height:88vh;overflow-y:auto;
  box-shadow:0 24px 60px rgba(0,0,0,0.18);
  position:relative;
}
.modal-box::-webkit-scrollbar{width:6px;}
.modal-box::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:3px;}
.modal-header{
  padding:24px 28px 20px;border-bottom:1px solid #f1f5f9;
  display:flex;align-items:flex-start;justify-content:space-between;
  position:sticky;top:0;background:#fff;z-index:1;border-radius:20px 20px 0 0;
}
.modal-co{font-size:0.72rem;font-weight:700;color:#2563EB;text-transform:uppercase;
  letter-spacing:0.8px;margin-bottom:5px;}
.modal-title{font-size:1.2rem;font-weight:700;color:#0f172a;line-height:1.3;}
.modal-close{width:32px;height:32px;border-radius:8px;border:1px solid #e2e8f0;
  background:#fff;display:flex;align-items:center;justify-content:center;
  cursor:pointer;color:#64748b;font-size:18px;flex-shrink:0;
  transition:background 0.15s;font-family:'Material Symbols Outlined';
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;}
.modal-close:hover{background:#f8fafc;color:#0f172a;}
.modal-body{padding:24px 28px;}
.modal-pills{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px;}
.modal-pill{display:inline-flex;align-items:center;gap:5px;padding:5px 12px;
  border-radius:9999px;font-size:0.78rem;font-weight:600;}
.mp-stage-Applied   {background:#f1f5f9;color:#475569;}
.mp-stage-Interview {background:#dbeafe;color:#1d4ed8;}
.mp-stage-Offer     {background:#dcfce7;color:#15803d;}
.mp-stage-Rejected  {background:#fee2e2;color:#dc2626;}
.mp-loc  {background:#f0f9ff;color:#0369a1;}
.mp-sal  {background:#fef9c3;color:#854d0e;}
.mp-type {background:#f1f5f9;color:#475569;}
.mp-rec  {background:#dcfce7;color:#15803d;}
.modal-section-title{
  font-size:0.7rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.8px;margin:18px 0 8px;
}
.modal-text{font-size:0.875rem;color:#475569;line-height:1.75;}
.modal-reqs{
  font-size:0.875rem;color:#334155;line-height:1.8;
  padding:14px 16px;background:#f8fafc;border-radius:10px;
  border-left:3px solid #2563EB;
}
.modal-info-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:4px;}
.modal-info-item{background:#f8fafc;border-radius:10px;padding:12px 14px;}
.modal-info-lbl{font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.6px;margin-bottom:4px;}
.modal-info-val{font-size:0.875rem;font-weight:600;color:#0f172a;}
.modal-actions{
  display:flex;gap:10px;padding:20px 28px;border-top:1px solid #f1f5f9;
  position:sticky;bottom:0;background:#fff;border-radius:0 0 20px 20px;
}
.modal-btn-primary{flex:1;padding:11px;border-radius:10px;background:#2563EB;
  color:#fff;font-size:0.9rem;font-weight:700;border:none;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:background 0.15s;
  box-shadow:0 2px 8px rgba(37,99,235,0.25);}
.modal-btn-primary:hover{background:#1d4ed8;}
.modal-btn-secondary{flex:1;padding:11px;border-radius:10px;background:#fff;
  color:#475569;font-size:0.9rem;font-weight:700;border:1px solid #e2e8f0;
  cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.15s;}
.modal-btn-secondary:hover{background:#f8fafc;border-color:#cbd5e1;}
.modal-li-btn{display:inline-flex;align-items:center;gap:5px;color:#2563EB;
  font-size:0.875rem;font-weight:700;text-decoration:none!important;
  background:#eff6ff;padding:6px 14px;border-radius:8px;transition:background 0.15s;}
.modal-li-btn:hover{background:#dbeafe;}

/* ── ADD APP FORM ── */
.add-form-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,0.04);}

/* ── STREAMLIT OVERRIDES ── */
div.stButton>button{background:#fff!important;color:#475569!important;
  border:1px solid #e2e8f0!important;border-radius:8px!important;font-weight:600!important;
  font-size:0.85rem!important;font-family:'DM Sans',sans-serif!important;
  padding:8px 14px!important;transition:all 0.15s!important;}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{background:#2563EB!important;color:#fff!important;
  border-color:#2563EB!important;box-shadow:0 2px 8px rgba(37,99,235,0.25)!important;}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}
div[data-testid="stTextInput"] input{background:#fff!important;
  border:1px solid #e2e8f0!important;border-radius:8px!important;font-family:'DM Sans',sans-serif!important;}
div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;
  box-shadow:0 0 0 3px rgba(37,99,235,0.1)!important;}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:#fff!important;
  border:1px solid #e2e8f0!important;border-radius:8px!important;}
div[data-testid="stDateInput"] input{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
.stAlert{border-radius:10px!important;}
hr{border-color:#e2e8f0!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD
# ══════════════════════════════════════════════════════════════════════════════
apps = get_all_applications()
df = pd.DataFrame(apps) if apps else pd.DataFrame(columns=[
    "id","company_name","position","stage","applied_date","last_updated",
    "email_subject","recruiter_email","recruiter_name","recruiter_title",
    "linkedin_url","salary_range","interview_date","interview_type","location","notes"])
for col in ["recruiter_email","recruiter_name","recruiter_title","linkedin_url",
            "salary_range","interview_date","interview_type","location","notes"]:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].fillna("").astype(str)
if "stage" not in df.columns: df["stage"] = "Applied"

total_count = len(df)

# ── Filter ────────────────────────────────────────────────────────────────────
filtered = df.copy()
_search  = st.session_state.app2_search
_stage   = st.session_state.app2_stage

if _search:
    m = (filtered.company_name.str.contains(_search,case=False,na=False) |
         filtered.position.str.contains(_search,case=False,na=False))
    filtered = filtered[m]
if _stage != "All Stages":
    filtered = filtered[filtered.stage == _stage]

ROWS = 8
total_rows  = len(filtered)
total_pages = max(1, math.ceil(total_rows / ROWS))
if st.session_state.app2_page >= total_pages:
    st.session_state.app2_page = total_pages - 1
cur = st.session_state.app2_page
ps  = cur * ROWS
pe  = min(ps + ROWS, total_rows)
page_df = filtered.iloc[ps:pe]

# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="app-topbar">
  <div class="topbar-left">
    <span class="topbar-title">Job Applications</span>
    <span class="topbar-count">{total_count} Total</span>
  </div>
  <div class="topbar-right">
    <div class="notif-btn">notifications</div>
    <button class="add-btn" id="add-app-btn">
      <span class="mi">add</span> Add Application
    </button>
  </div>
</div>
<script>
document.getElementById('add-app-btn').onclick = function() {{
  var btns = window.parent.document.querySelectorAll('[data-testid="stButton"] button');
  for(var i=0;i<btns.length;i++){{
    if(btns[i].innerText.trim().includes('ADD_APP')){{btns[i].click();break;}}
  }}
}};
</script>
""", unsafe_allow_html=True)

# ── Hidden Add Application trigger ───────────────────────────────────────────
_add_col, _ = st.columns([1, 10])
with _add_col:
    if st.button("ADD_APP", key="add_app_trigger"):
        st.session_state.app2_add_open = not st.session_state.app2_add_open
        st.rerun()
st.markdown("""<style>
[data-testid="stHorizontalBlock"]:first-of-type{position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ADD APPLICATION FORM (collapsible)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app2_add_open:
    st.markdown('<div class="app-content" style="padding-bottom:0;">', unsafe_allow_html=True)
    with st.expander("➕ Add New Application", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            add_co  = st.text_input("Company Name", placeholder="e.g. Google", key="add_co")
            add_pos = st.text_input("Job Title",    placeholder="e.g. Software Engineer", key="add_pos")
        with c2:
            add_date= st.date_input("Applied Date", key="add_date")
            add_stage = st.selectbox("Stage", ["Applied","Interview","Offer","Rejected"], key="add_stg")
        if st.button("➕ Add Application", type="primary", key="add_submit"):
            if add_co and add_pos:
                with st.spinner("🔍 Looking up recruiter..."):
                    info = enrich_application(add_co)
                upsert_application(add_co, add_pos, str(add_date), "Manually added",
                    info.get("recruiter_email",""), info.get("recruiter_name",""),
                    info.get("recruiter_title",""), info.get("linkedin_url",""))
                st.success(f"✅ Added **{add_pos}** at **{add_co}**")
                st.session_state.app2_add_open = False
                st.rerun()
            else:
                st.warning("Please fill in Company Name and Job Title.")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="app-content">', unsafe_allow_html=True)

# ── Search & Filter row ───────────────────────────────────────────────────────
stage_opts = ["All Stages","Applied","Interview","Offer","Rejected"]
_stage_sel_html = "".join(
    f'<option value="{s}" {"selected" if s==_stage else ""}>{s}</option>'
    for s in stage_opts)

st.markdown(f"""
<div class="filter-row">
  <div class="search-wrap">
    <span class="search-icon">search</span>
    <input class="search-input" id="app-search" type="text"
           placeholder="Search by company or job title..."
           value="{_search}"
           oninput="window._appSearch(this.value)" />
  </div>
  <select class="stage-select" id="app-stage" onchange="window._appStage(this.value)">
    {_stage_sel_html}
  </select>
  <button class="filters-btn">
    <span class="mi">tune</span> Filters
  </button>
</div>
<script>
window._appSearch = function(v) {{
  var inps = window.parent.document.querySelectorAll('[data-testid="stTextInput"] input');
  if(inps.length) {{
    var setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
    setter.call(inps[0], v);
    inps[0].dispatchEvent(new Event('input', {{bubbles:true}}));
  }}
}};
window._appStage = function(v) {{
  /* stage filter handled via Streamlit selectbox below */
}};
</script>
""", unsafe_allow_html=True)

# Hidden Streamlit filter widgets
_filt_cols = st.columns([3, 1, 1])
with _filt_cols[0]:
    sv = st.text_input("S", value=_search, key="app2_s_inp",
                       placeholder="Search...", label_visibility="collapsed")
with _filt_cols[1]:
    stv = st.selectbox("St", stage_opts, key="app2_st_inp",
                       label_visibility="collapsed")
if sv != _search: st.session_state.app2_search=sv; st.rerun()
if stv != _stage: st.session_state.app2_stage=stv; st.rerun()
st.markdown("""<style>
[data-testid="stHorizontalBlock"]:nth-of-type(2){position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BUILD TABLE HTML
# ══════════════════════════════════════════════════════════════════════════════
STAGE_CLS = {
    "Applied":     "stage-Applied",
    "Interview":   "stage-Interview",
    "Interviewing":"stage-Interviewing",
    "Offer":       "stage-Offer",
    "Rejected":    "stage-Rejected",
    "Wishlist":    "stage-Wishlist",
}

def _stage_badge(stage):
    cls = STAGE_CLS.get(stage, "stage-Applied")
    return f'<span class="stage-badge {cls}">{stage}</span>'

def _rec_dot(has_rec):
    if has_rec:
        return '<span class="rec-dot-yes"></span>'
    return '<span class="rec-dot-no"></span>'

# Build table rows with data-idx for JS click
rows_html = ""
if page_df.empty:
    rows_html = (
        '<tr><td colspan="6" style="text-align:center;color:#94a3b8;'
        'padding:60px;font-size:0.9rem;">'
        '&#128235; No applications yet. Add one above or sync Gmail from the Dashboard.'
        '</td></tr>'
    )
else:
    for i, (_, r) in enumerate(page_df.iterrows()):
        stage   = str(r.get("stage","Applied"))
        rec_n   = str(r.get("recruiter_name","")).strip()
        li      = str(r.get("linkedin_url","")).strip()
        has_rec = bool(rec_n or li)
        let     = str(r["company_name"])[0].upper() if r["company_name"] else "?"
        abs_idx = ps + i  # absolute index in filtered df

        rows_html += f"""
        <tr onclick="window._openModal({abs_idx})" data-idx="{abs_idx}">
          <td>
            <div class="co-cell">
              <div class="co-avatar">{let}</div>
              <span class="co-name">{r['company_name']}</span>
            </div>
          </td>
          <td style="color:#475569;">{r['position']}</td>
          <td class="date-txt" style="color:#64748b;white-space:nowrap;">{r.get('applied_date','')}</td>
          <td>{_stage_badge(stage)}</td>
          <td style="text-align:center;">{_rec_dot(has_rec)}</td>
          <td>
            <button class="view-details" onclick="event.stopPropagation();window._openModal({abs_idx})">
              View Details
            </button>
          </td>
        </tr>"""

# Pagination controls HTML
pg_inner = ""
if total_pages > 1:
    p_dis = "disabled" if cur==0 else ""
    n_dis = "disabled" if cur==total_pages-1 else ""
    pg_inner += f'<button class="pg-btn-nav" onclick="window._pgPrev()" {p_dis}>&#8249;</button>'
    for p in range(min(total_pages, 5)):
        ac = "active" if p==cur else ""
        pg_inner += f'<button class="pg-btn {ac}" onclick="window._pgGo({p})">{p+1}</button>'
    if total_pages > 5:
        pg_inner += '<span style="color:#94a3b8;padding:0 4px;">…</span>'
        pg_inner += f'<button class="pg-btn {"active" if cur==total_pages-1 else ""}" onclick="window._pgGo({total_pages-1})">{total_pages}</button>'
    pg_inner += f'<button class="pg-btn-nav" onclick="window._pgNext()" {n_dis}>&#8250;</button>'

st.markdown(f"""
<div class="tbl-card">
  <table class="tbl-table">
    <thead>
      <tr>
        <th>Company Name</th>
        <th>Job Title</th>
        <th>Applied Date</th>
        <th>Stage</th>
        <th style="text-align:center;">Recruiter Found</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="pagination-row">
    <span class="pg-info">Showing {ps+1} to {pe} of {total_rows} applications</span>
    <div class="pg-btns">{pg_inner}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hidden Streamlit pagination buttons ───────────────────────────────────────
if total_pages > 1:
    def _pslots(c,t):
        if t<=7: return list(range(t))
        r=[0]; lo,hi=max(1,c-2),min(t-2,c+2)
        if lo>1: r.append(None)
        r.extend(range(lo,hi+1))
        if hi<t-2: r.append(None)
        r.append(t-1); return r
    sl=_pslots(cur,total_pages)
    bc=st.columns(2+len(sl))
    with bc[0]:
        if st.button("&#9664;",key="pg2_prev",disabled=(cur==0),use_container_width=True):
            st.session_state.app2_page=cur-1; st.rerun()
    for i,s in enumerate(sl):
        with bc[i+1]:
            if s is None:
                st.markdown("<div style='text-align:center;color:#94a3b8;'>…</div>",unsafe_allow_html=True)
            else:
                if st.button(str(s+1),key=f"pg2_{s}",type="primary" if s==cur else "secondary",use_container_width=True):
                    st.session_state.app2_page=s; st.rerun()
    with bc[-1]:
        if st.button("&#9654;",key="pg2_next",disabled=(cur==total_pages-1),use_container_width=True):
            st.session_state.app2_page=cur+1; st.rerun()
    st.markdown("""<style>
[data-testid="stHorizontalBlock"]:nth-of-type(3){position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
</style>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # /app-content

# ══════════════════════════════════════════════════════════════════════════════
# ROW CLICK → store selected index via JS → session state
# ══════════════════════════════════════════════════════════════════════════════
# Build JSON of all filtered rows for the modal
rows_json = []
for _, r in filtered.iterrows():
    rows_json.append({
        "id":             str(r.get("id","")),
        "company":        str(r.get("company_name","")),
        "title":          str(r.get("position","")),
        "stage":          str(r.get("stage","Applied")),
        "applied_date":   str(r.get("applied_date","")),
        "last_updated":   str(r.get("last_updated","")),
        "location":       str(r.get("location","")),
        "salary":         str(r.get("salary_range","")),
        "interview_date": str(r.get("interview_date","")),
        "interview_type": str(r.get("interview_type","")),
        "recruiter_name": str(r.get("recruiter_name","")),
        "recruiter_title":str(r.get("recruiter_title","")),
        "recruiter_email":str(r.get("recruiter_email","")),
        "linkedin_url":   str(r.get("linkedin_url","")),
        "email_subject":  str(r.get("email_subject","")),
        "notes":          str(r.get("notes","")),
    })

rows_json_str = json.dumps(rows_json)

# ══════════════════════════════════════════════════════════════════════════════
# MODAL — rendered via pure HTML/JS (no Streamlit re-render needed)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div id="job-modal" style="display:none;" class="modal-overlay" onclick="window._closeModal(event)">
  <div class="modal-box" id="modal-box" onclick="event.stopPropagation()">
    <div class="modal-header">
      <div>
        <div class="modal-co" id="m-company"></div>
        <div class="modal-title" id="m-title"></div>
      </div>
      <button class="modal-close" onclick="window._closeModal()">close</button>
    </div>
    <div class="modal-body">
      <div class="modal-pills" id="m-pills"></div>

      <!-- Info grid -->
      <div class="modal-info-grid" id="m-info-grid"></div>

      <!-- AI Summary / Email Subject -->
      <div id="m-subject-wrap" style="display:none;">
        <div class="modal-section-title">Source Email</div>
        <div class="modal-text" id="m-subject" style="background:#f8fafc;padding:10px 14px;border-radius:8px;font-size:0.82rem;"></div>
      </div>

      <!-- Recruiter -->
      <div id="m-rec-wrap" style="display:none;">
        <div class="modal-section-title">Recruiter</div>
        <div id="m-rec-content" class="modal-text"></div>
      </div>

      <!-- Notes -->
      <div id="m-notes-wrap" style="display:none;">
        <div class="modal-section-title">Notes</div>
        <div class="modal-text" id="m-notes" style="background:#f8fafc;padding:10px 14px;border-radius:8px;"></div>
      </div>
    </div>
    <div class="modal-actions">
      <a id="m-li-btn" href="#" target="_blank" class="modal-li-btn" style="display:none;">
        &#128279; View on LinkedIn
      </a>
      <button class="modal-btn-secondary" onclick="window._closeModal()">Close</button>
    </div>
  </div>
</div>

<script>
var _ROWS = {rows_json_str};

function _badge(stage) {{
  var map = {{
    'Applied':    'mp-stage-Applied',
    'Interview':  'mp-stage-Interview',
    'Offer':      'mp-stage-Offer',
    'Rejected':   'mp-stage-Rejected',
  }};
  var cls = map[stage] || 'mp-stage-Applied';
  return '<span class="modal-pill ' + cls + '">' + stage + '</span>';
}}

window._openModal = function(idx) {{
  var r = _ROWS[idx];
  if (!r) return;

  document.getElementById('m-company').textContent  = r.company.toUpperCase();
  document.getElementById('m-title').textContent    = r.title;

  // Pills
  var pills = _badge(r.stage);
  if(r.location) pills += '<span class="modal-pill mp-loc">&#128205; ' + r.location + '</span>';
  if(r.salary)   pills += '<span class="modal-pill mp-sal">&#128176; ' + r.salary + '</span>';
  if(r.interview_type) pills += '<span class="modal-pill mp-type">' + r.interview_type + '</span>';
  if(r.recruiter_name) pills += '<span class="modal-pill mp-rec">&#128100; Recruiter Found</span>';
  document.getElementById('m-pills').innerHTML = pills;

  // Info grid
  var grid = '';
  grid += '<div class="modal-info-item"><div class="modal-info-lbl">Applied Date</div><div class="modal-info-val">' + (r.applied_date||'—') + '</div></div>';
  grid += '<div class="modal-info-item"><div class="modal-info-lbl">Last Updated</div><div class="modal-info-val">' + (r.last_updated||'—') + '</div></div>';
  grid += '<div class="modal-info-item"><div class="modal-info-lbl">Stage</div><div class="modal-info-val">' + r.stage + '</div></div>';
  if(r.interview_date) grid += '<div class="modal-info-item"><div class="modal-info-lbl">Interview Date</div><div class="modal-info-val">' + r.interview_date + '</div></div>';
  if(r.salary) grid += '<div class="modal-info-item"><div class="modal-info-lbl">Salary Range</div><div class="modal-info-val">' + r.salary + '</div></div>';
  document.getElementById('m-info-grid').innerHTML = grid;

  // Source email
  var subWrap = document.getElementById('m-subject-wrap');
  if(r.email_subject && r.email_subject !== 'Manually added') {{
    document.getElementById('m-subject').textContent = r.email_subject;
    subWrap.style.display = '';
  }} else {{ subWrap.style.display = 'none'; }}

  // Recruiter
  var recWrap = document.getElementById('m-rec-wrap');
  if(r.recruiter_name || r.recruiter_email || r.linkedin_url) {{
    var rc = '';
    if(r.recruiter_name)  rc += '<div style="font-weight:700;color:#0f172a;font-size:0.9rem;margin-bottom:3px;">&#128100; ' + r.recruiter_name + '</div>';
    if(r.recruiter_title) rc += '<div style="color:#64748b;font-size:0.8rem;margin-bottom:5px;">' + r.recruiter_title + '</div>';
    if(r.recruiter_email) rc += '<div style="font-size:0.82rem;color:#334155;">&#9993; ' + r.recruiter_email + '</div>';
    document.getElementById('m-rec-content').innerHTML = rc;
    recWrap.style.display = '';
  }} else {{ recWrap.style.display = 'none'; }}

  // LinkedIn button
  var liBtn = document.getElementById('m-li-btn');
  if(r.linkedin_url) {{
    liBtn.href = r.linkedin_url;
    liBtn.style.display = 'inline-flex';
  }} else {{ liBtn.style.display = 'none'; }}

  // Notes
  var notesWrap = document.getElementById('m-notes-wrap');
  if(r.notes) {{
    document.getElementById('m-notes').textContent = r.notes;
    notesWrap.style.display = '';
  }} else {{ notesWrap.style.display = 'none'; }}

  document.getElementById('job-modal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
}};

window._closeModal = function(e) {{
  if(e && e.target !== document.getElementById('job-modal')) return;
  document.getElementById('job-modal').style.display = 'none';
  document.body.style.overflow = '';
}};

// Pagination bridge
window._pgPrev = function() {{
  var btns = window.parent.document.querySelectorAll('[data-testid="stButton"] button');
  for(var i=0;i<btns.length;i++){{if(btns[i].textContent.includes('◄')){{btns[i].click();break;}}}}
}};
window._pgNext = function() {{
  var btns = window.parent.document.querySelectorAll('[data-testid="stButton"] button');
  for(var i=0;i<btns.length;i++){{if(btns[i].textContent.includes('►')){{btns[i].click();break;}}}}
}};
window._pgGo = function(n) {{
  var btns = window.parent.document.querySelectorAll('[data-testid="stButton"] button');
  for(var i=0;i<btns.length;i++){{if(btns[i].textContent.trim()===String(n+1)){{btns[i].click();break;}}}}
}};

// ESC key to close modal
document.addEventListener('keydown', function(e) {{
  if(e.key==='Escape') window._closeModal();
}});
</script>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.caption("CareerSync v3.0 · Applications · ❤️")