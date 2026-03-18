"""
pages/2_Applications.py — CareerSync Job Application Portal
TWO TABS:
  1. My Applications  — clean minimal table (exact design), row click → modal popup
  2. Browse Jobs      — search LinkedIn via Apify + Groq AI, Apply Now saves to DB

UI: Exact design match — Company / Job Title / Applied Date / Stage / Recruiter Found / Actions
    Click any row OR "View Details" → full detail modal
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
        val = st.secrets.get(key, "")
        if val: return val
    except Exception: pass
    return os.getenv(key, default)

GROQ_KEY  = _get("GROQ_API_KEY")
APIFY_KEY = _get("APIFY_API_KEY")
SUP_URL   = _get("SUPABASE_URL")
SUP_KEY   = _get("SUPABASE_KEY")

try:
    from supabase import create_client
    _sb = create_client(SUP_URL, SUP_KEY) if SUP_URL and SUP_KEY else None
except Exception:
    _sb = None

user_id    = user["id"]
name_disp  = user.get("name", "User")
email_disp = user.get("email", "")
avatar_let = name_disp[0].upper() if name_disp else "U"

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [
    ("app2_tab",       "my"),        # "my" | "browse"
    ("app2_page",      0),
    ("app2_search",    ""),
    ("app2_stage",     "All Stages"),
    ("app2_add_open",  False),
    ("job_results",    []),
    ("applied_jobs",   {}),
    ("ai_data",        {}),
]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');
    [data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important;
      min-width:240px!important;max-width:240px!important;}
    [data-testid="stSidebar"] .stButton>button{
      text-align:left!important;justify-content:flex-start!important;
      background:transparent!important;color:#475569!important;border:none!important;
      box-shadow:none!important;font-size:0.9rem!important;font-weight:500!important;
      padding:9px 12px!important;border-radius:8px!important;width:100%!important;
      font-family:'DM Sans',sans-serif!important;}
    [data-testid="stSidebar"] .stButton>button:hover{background:#f8fafc!important;color:#0f172a!important;}
    [data-testid="collapsedControl"]{display:none!important;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:20px 16px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f1f5f9;">
      <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;display:flex;
                  align-items:center;justify-content:center;flex-shrink:0;">
        <span style="font-family:'Material Symbols Outlined';font-size:17px;color:#fff;
                     font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">sync_alt</span>
      </div>
      <div>
        <div style="font-size:1rem;font-weight:700;color:#0f172a;font-family:'DM Sans',sans-serif;">CareerSync</div>
        <div style="font-size:0.7rem;color:#94a3b8;font-family:'DM Sans',sans-serif;">Manage your career</div>
      </div>
    </div>
    <div style="padding:12px 12px 8px;">
    """, unsafe_allow_html=True)

    nav_pages = [
        ("dashboard", "Dashboard",        "pages/1_Dashboard.py"),
        ("work",      "Applications",     "pages/2_Applications.py"),
        ("mail",      "Cold Email",       "pages/3_Cold_Email.py"),
        ("plumbing",  "Research Pipeline","pages/4_Pipeline.py"),
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
              {label}</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
                        color:#64748b;font-size:0.9rem;font-weight:500;font-family:'DM Sans',sans-serif;">
              <span style="font-family:'Material Symbols Outlined';font-size:20px;
                           font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">{icon}</span>
              {label}</div>""", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{label}"):
                try: st.switch_page(path)
                except: st.info(f"{label} coming soon!")

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
          <div style="font-size:0.7rem;color:#64748b;">Pro Account</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

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
.block-container{padding-top:0!important;padding-bottom:2rem!important;
  max-width:100%!important;padding-left:0!important;padding-right:0!important;}
[data-testid="stVerticalBlock"]{gap:0!important;}

/* ══ TOPBAR ══ */
.app-topbar{height:60px;background:#fff;border-bottom:1px solid #e2e8f0;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 28px;position:sticky;top:0;z-index:50;}
.topbar-left{display:flex;align-items:center;gap:12px;}
.topbar-title{font-size:1.2rem;font-weight:700;color:#0f172a;letter-spacing:-0.3px;}
.topbar-count{font-size:0.78rem;font-weight:600;color:#64748b;
  background:#f1f5f9;padding:3px 10px;border-radius:9999px;}
.topbar-right{display:flex;align-items:center;gap:10px;}
.notif-btn{width:36px;height:36px;border-radius:9px;border:1px solid #e2e8f0;background:#fff;
  display:flex;align-items:center;justify-content:center;cursor:pointer;color:#64748b;
  font-family:'Material Symbols Outlined';font-size:20px;line-height:1;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}
.add-btn{display:inline-flex;align-items:center;gap:6px;background:#2563EB;color:#fff;
  padding:9px 18px;border-radius:10px;font-size:0.875rem;font-weight:700;
  font-family:'DM Sans',sans-serif;border:none;cursor:pointer;
  box-shadow:0 2px 8px rgba(37,99,235,0.28);transition:background 0.15s;}
.add-btn:hover{background:#1d4ed8;}
.add-btn-icon{font-family:'Material Symbols Outlined';font-size:17px;line-height:1;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;}

/* ══ PAGE CONTENT ══ */
.app-content{padding:24px 28px;}

/* ══ TAB PILLS ══ */
.tab-pills{display:flex;background:#f1f5f9;border-radius:12px;padding:4px;gap:4px;
  width:fit-content;margin-bottom:22px;}
.tab-pill{padding:8px 22px;border-radius:8px;font-size:0.875rem;font-weight:600;
  cursor:pointer;border:none;font-family:'DM Sans',sans-serif;transition:all 0.15s;}
.tab-pill-active{background:#fff;color:#2563EB;box-shadow:0 1px 4px rgba(0,0,0,0.10);}
.tab-pill-inactive{background:transparent;color:#64748b;}
.tab-pill-inactive:hover{color:#0f172a;}

/* ══ FILTER ROW ══ */
.filter-row{display:flex;align-items:center;gap:12px;margin-bottom:20px;}
.search-wrap{position:relative;flex:1;max-width:500px;}
.search-icon{position:absolute;left:12px;top:50%;transform:translateY(-50%);
  font-family:'Material Symbols Outlined';font-size:17px;color:#94a3b8;pointer-events:none;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;}
.search-input{width:100%;padding:9px 14px 9px 38px;background:#fff;border:1px solid #e2e8f0;
  border-radius:10px;font-size:0.875rem;font-family:'DM Sans',sans-serif;color:#0f172a;
  outline:none;transition:border-color 0.15s,box-shadow 0.15s;}
.search-input:focus{border-color:#2563EB;box-shadow:0 0 0 3px rgba(37,99,235,0.1);}
.search-input::placeholder{color:#94a3b8;}
.stage-sel{padding:9px 32px 9px 14px;background:#fff;border:1px solid #e2e8f0;
  border-radius:10px;font-size:0.875rem;font-family:'DM Sans',sans-serif;color:#0f172a;
  outline:none;cursor:pointer;min-width:140px;appearance:none;-webkit-appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 10px center;}
.filters-btn{display:inline-flex;align-items:center;gap:5px;padding:9px 16px;background:#fff;
  border:1px solid #e2e8f0;border-radius:10px;font-size:0.875rem;font-weight:600;
  color:#475569;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.15s;white-space:nowrap;}
.filters-btn:hover{background:#f8fafc;border-color:#cbd5e1;}

/* ══ MY APPLICATIONS TABLE ══ */
.tbl-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.tbl-table{width:100%;border-collapse:collapse;}
.tbl-table th{padding:13px 20px;font-size:0.7rem;font-weight:700;color:#94a3b8;
  text-transform:uppercase;letter-spacing:0.7px;text-align:left;
  white-space:nowrap;border-bottom:1px solid #f1f5f9;}
.tbl-table td{padding:16px 20px;border-bottom:1px solid #f1f5f9;
  font-size:0.875rem;color:#334155;vertical-align:middle;}
.tbl-table tr:last-child td{border-bottom:none;}
.tbl-table tbody tr{cursor:pointer;transition:background 0.1s;}
.tbl-table tbody tr:hover td{background:#f8fafc;}
.co-cell{display:flex;align-items:center;gap:12px;}
.co-av{width:36px;height:36px;border-radius:9px;background:#f1f5f9;
  display:flex;align-items:center;justify-content:center;
  font-size:0.8rem;font-weight:700;color:#475569;flex-shrink:0;border:1px solid #e8edf2;}
.co-name{font-weight:600;color:#0f172a;font-size:0.9rem;}
.s-badge{display:inline-flex;align-items:center;padding:4px 12px;
  border-radius:7px;font-size:0.78rem;font-weight:600;}
.s-Applied    {background:#f1f5f9;color:#475569;}
.s-Interview  {background:#dbeafe;color:#1d4ed8;}
.s-Offer      {background:#dcfce7;color:#15803d;}
.s-Rejected   {background:#fee2e2;color:#dc2626;}
.s-Wishlist   {background:#fce7f3;color:#be185d;}
.rec-yes{width:22px;height:22px;border-radius:50%;background:#22c55e;
  display:inline-flex;align-items:center;justify-content:center;
  font-size:11px;color:#fff;font-weight:700;}
.rec-no{width:22px;height:22px;border-radius:50%;background:#e2e8f0;display:inline-block;}
.view-det{color:#2563EB;font-weight:600;font-size:0.875rem;cursor:pointer;
  border:none;background:none;font-family:'DM Sans',sans-serif;padding:0;}
.view-det:hover{text-decoration:underline;}

/* ══ PAGINATION ══ */
.pg-row{display:flex;align-items:center;justify-content:space-between;
  padding:14px 20px;border-top:1px solid #f1f5f9;}
.pg-info{font-size:0.82rem;color:#64748b;}
.pg-btns{display:flex;align-items:center;gap:4px;}
.pg-b{width:32px;height:32px;border-radius:7px;border:1px solid #e2e8f0;background:#fff;
  font-size:0.82rem;font-weight:600;color:#475569;cursor:pointer;
  display:inline-flex;align-items:center;justify-content:center;
  font-family:'DM Sans',sans-serif;transition:all 0.12s;}
.pg-b:hover:not([disabled]){background:#f8fafc;}
.pg-b.active{background:#2563EB;color:#fff;border-color:#2563EB;}
.pg-b[disabled]{opacity:0.35;cursor:not-allowed;}
.pg-nav{width:30px;height:32px;border-radius:7px;border:1px solid #e2e8f0;background:#fff;
  cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
  color:#64748b;font-size:13px;transition:all 0.12s;}
.pg-nav:hover:not([disabled]){background:#f8fafc;}
.pg-nav[disabled]{opacity:0.35;cursor:not-allowed;}

/* ══ MODAL ══ */
.mod-overlay{position:fixed;inset:0;background:rgba(15,23,42,0.45);z-index:9998;
  display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(3px);}
.mod-box{background:#fff;border-radius:20px;width:100%;max-width:660px;max-height:88vh;
  overflow-y:auto;box-shadow:0 24px 60px rgba(0,0,0,0.18);position:relative;}
.mod-box::-webkit-scrollbar{width:5px;}
.mod-box::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:3px;}
.mod-hdr{padding:24px 28px 18px;border-bottom:1px solid #f1f5f9;
  display:flex;align-items:flex-start;justify-content:space-between;
  position:sticky;top:0;background:#fff;z-index:1;border-radius:20px 20px 0 0;}
.mod-co{font-size:0.7rem;font-weight:700;color:#2563EB;text-transform:uppercase;
  letter-spacing:0.8px;margin-bottom:5px;}
.mod-title{font-size:1.15rem;font-weight:700;color:#0f172a;line-height:1.3;}
.mod-close{width:30px;height:30px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;
  display:flex;align-items:center;justify-content:center;cursor:pointer;color:#64748b;
  font-family:'Material Symbols Outlined';font-size:18px;flex-shrink:0;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;
  transition:background 0.15s;}
.mod-close:hover{background:#f8fafc;}
.mod-body{padding:22px 28px;}
.mod-pills{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:18px;}
.mpill{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;
  border-radius:9999px;font-size:0.75rem;font-weight:600;}
.mp-Applied  {background:#f1f5f9;color:#475569;}
.mp-Interview{background:#dbeafe;color:#1d4ed8;}
.mp-Offer    {background:#dcfce7;color:#15803d;}
.mp-Rejected {background:#fee2e2;color:#dc2626;}
.mp-loc{background:#f0f9ff;color:#0369a1;}
.mp-sal{background:#fef9c3;color:#854d0e;}
.mp-rec{background:#dcfce7;color:#15803d;}
.mod-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;}
.mod-cell{background:#f8fafc;border-radius:10px;padding:12px 14px;}
.mod-cell-lbl{font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.6px;margin-bottom:3px;}
.mod-cell-val{font-size:0.875rem;font-weight:600;color:#0f172a;}
.mod-sec-lbl{font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.7px;margin:16px 0 6px;}
.mod-text{font-size:0.875rem;color:#475569;line-height:1.7;
  background:#f8fafc;padding:12px 14px;border-radius:10px;}
.mod-rec{background:#f8fafc;border-radius:10px;padding:12px 14px;}
.mod-foot{display:flex;gap:10px;padding:18px 28px;border-top:1px solid #f1f5f9;
  position:sticky;bottom:0;background:#fff;border-radius:0 0 20px 20px;}
.mod-btn-p{flex:1;padding:10px;border-radius:10px;background:#2563EB;color:#fff;
  font-size:0.875rem;font-weight:700;border:none;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:background 0.15s;}
.mod-btn-p:hover{background:#1d4ed8;}
.mod-btn-s{flex:1;padding:10px;border-radius:10px;background:#fff;color:#475569;
  font-size:0.875rem;font-weight:700;border:1px solid #e2e8f0;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:all 0.15s;}
.mod-btn-s:hover{background:#f8fafc;}

/* ══ BROWSE JOBS ══ */
.search-panel{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:22px 24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.search-panel-lbl{font-size:0.68rem;font-weight:700;color:#0f172a;
  text-transform:uppercase;letter-spacing:0.8px;margin-bottom:12px;}
.job-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;
  padding:22px 26px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
  transition:box-shadow 0.15s;}
.job-card:hover{box-shadow:0 4px 16px rgba(0,0,0,0.08);}
.jc-co{font-size:0.7rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;}
.jc-title{font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:8px;}
.jc-meta{font-size:0.8rem;color:#64748b;margin-bottom:10px;}
.pill{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:9999px;
  font-size:0.72rem;font-weight:700;margin-right:5px;margin-bottom:5px;}
.p-applied{background:#dcfce7;color:#15803d;}
.p-salary {background:#fef9c3;color:#854d0e;}
.p-views  {background:#ede9fe;color:#6d28d9;}
.p-posted {background:#f0f9ff;color:#0369a1;}
.p-type   {background:#f1f5f9;color:#475569;}
.sec-lbl{font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.7px;margin:12px 0 5px;}
.sec-txt{font-size:0.875rem;color:#475569;line-height:1.7;}
.sec-req{font-size:0.82rem;color:#334155;line-height:1.7;
  padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #2563EB;margin-top:4px;}
.card-div{height:1px;background:#f1f5f9;margin:12px 0;}

/* Applied jobs table (Browse → Applied) */
.cs-wrap{background:#fff;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;
  box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.cs-table{width:100%;border-collapse:collapse;}
.cs-table th{background:#f8fafc;color:#64748b;font-weight:700;font-size:0.68rem;
  text-transform:uppercase;letter-spacing:0.5px;padding:12px 18px;
  border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap;}
.cs-table td{padding:13px 18px;border-bottom:1px solid #f1f5f9;
  vertical-align:top;color:#334155;font-size:0.83rem;}
.cs-table tr:last-child td{border-bottom:none;}
.cs-table tr:hover td{background:#f8fafc;}
.co-logo{width:32px;height:32px;border-radius:8px;background:#f1f5f9;display:flex;
  align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;color:#475569;flex-shrink:0;}
.td-clamp2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:0.78rem;color:#64748b;}
.td-clamp3{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;font-size:0.75rem;color:#475569;}

/* empty states */
.empty-box{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:64px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.04);}

/* ══ STREAMLIT OVERRIDES ══ */
div.stButton>button{background:#fff!important;color:#475569!important;
  border:1px solid #e2e8f0!important;border-radius:8px!important;font-weight:600!important;
  font-size:0.85rem!important;font-family:'DM Sans',sans-serif!important;
  padding:8px 14px!important;transition:all 0.15s!important;}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{background:#2563EB!important;color:#fff!important;
  border-color:#2563EB!important;box-shadow:0 2px 8px rgba(37,99,235,0.25)!important;}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}
div[data-testid="stTextInput"] input{background:#fff!important;border:1px solid #e2e8f0!important;
  border-radius:8px!important;font-family:'DM Sans',sans-serif!important;}
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
# AI / FETCH HELPERS  (Browse Jobs)
# ══════════════════════════════════════════════════════════════════════════════
def _groq(prompt, max_tokens=300):
    if not GROQ_KEY: return ""
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
            json={"model":"llama-3.1-8b-instant",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":max_tokens,"temperature":0.3},
            timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception: return ""

def _ai_enrich(job):
    title = job.get("title","")
    desc  = job.get("description","")[:2500]
    reqs  = job.get("requirements","")[:1000]
    if not desc and not reqs:
        job["ai_summary"] = "No description available."
        job["ai_reqs"]    = ""
        return job
    prompt = (f"Title: {title}\n\nDescription:\n{desc}\n\nRequirements:\n{reqs}\n\n"
              "Return JSON with keys: summary (2 sentences), requirements (4-6 bullets starting with •), "
              "salary (from text or empty), job_type (Full-time/Part-time/Contract/empty). "
              "Return ONLY JSON, no markdown.")
    raw = _groq(prompt, 400)
    try:
        raw = re.sub(r"```(?:json)?","",raw).strip().rstrip("```").strip()
        d = json.loads(raw)
        job["ai_summary"] = d.get("summary","")
        job["ai_reqs"]    = d.get("requirements","")
        if not job.get("salary"):    job["salary"]    = d.get("salary","")
        if not job.get("job_type"):  job["job_type"]  = d.get("job_type","")
    except Exception:
        job["ai_summary"] = _groq(f"Summarise in 2 sentences: {title}\n{desc[:800]}", 120)
        job["ai_reqs"]    = reqs[:400]
    return job

def _fetch_apify(keyword, location, company, date_filter):
    if not APIFY_KEY: return []
    dm = {"Any time":"","Last 24 hours":"r86400","Past week":"r604800","Past month":"r2592000"}
    kw = f"{company.strip()} {keyword.strip()}".strip() if company.strip() else keyword.strip()
    inp = {"title":kw,"location":location.strip() or "United States","rows":20,"scrapeCompany":True,"proxy":{"useApifyProxy":True}}
    if dm.get(date_filter): inp["publishedAt"] = dm[date_filter]
    try:
        r = requests.post("https://api.apify.com/v2/acts/bebity~linkedin-jobs-scraper/run-sync-get-dataset-items",
            params={"token":APIFY_KEY,"timeout":90,"memory":512},json=inp,timeout=100)
        if r.status_code==200:
            items=r.json()
            if isinstance(items,list): return items
    except Exception: pass
    return []

def _fetch_guest(keyword, location, company, date_filter):
    from bs4 import BeautifulSoup
    dm = {"Any time":"","Last 24 hours":"r86400","Past week":"r604800","Past month":"r2592000"}
    kw = f"{keyword.strip()} {company.strip()}".strip()
    if not kw: return []
    hdrs = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36","Accept-Language":"en-US,en;q=0.9"}
    params = {"keywords":kw,"location":location.strip(),"start":0,"count":25}
    f = dm.get(date_filter,"")
    if f: params["f_TPR"] = f
    try:
        resp = requests.get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",params=params,headers=hdrs,timeout=20)
        if resp.status_code != 200: return []
    except Exception: return []
    soup = BeautifulSoup(resp.text,"html.parser")
    jobs = []
    for card in soup.find_all("li")[:20]:
        try:
            en = card.find("div",{"data-entity-urn":True})
            jid = ""
            if en: jid = en.get("data-entity-urn","").split(":")[-1]
            if not jid:
                lt = card.find("a",href=re.compile(r"/jobs/view/(\d+)"))
                if lt:
                    m = re.search(r"/jobs/view/(\d+)",lt["href"])
                    if m: jid = m.group(1)
            if not jid: continue
            t = card.find("h3") or card.find("span",class_=re.compile("title"))
            c2 = card.find("h4") or card.find("a",class_=re.compile("hidden-nested-link"))
            l2 = card.find("span",class_=re.compile("job-search-card__location"))
            tm = card.find("time")
            la = card.find("a",href=re.compile(r"linkedin\.com/jobs"))
            jobs.append({"id":jid,"title":t.get_text(strip=True) if t else "Unknown Role",
                "companyName":c2.get_text(strip=True) if c2 else "Unknown Company",
                "location":l2.get_text(strip=True) if l2 else "",
                "publishedAt":tm.get("datetime","") if tm else "",
                "jobUrl":la["href"].split("?")[0] if la else f"https://www.linkedin.com/jobs/view/{jid}",
                "description":"","salary":"","applicantsCount":"","requirements":""})
        except Exception: continue
    DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    for job in jobs[:12]:
        try:
            det = requests.get(DETAIL.format(job_id=job["id"]),headers=hdrs,timeout=10)
            if det.status_code==200:
                ds = BeautifulSoup(det.text,"html.parser")
                dt = ds.find("div",class_=re.compile("description__text")) or ds.find("div",class_=re.compile("show-more-less-html"))
                if dt: job["description"] = dt.get_text(separator=" ",strip=True)[:3000]
                st2 = ds.find("span",class_=re.compile("compensation"))
                if st2: job["salary"] = st2.get_text(strip=True)
                at = ds.find("span",class_=re.compile("num-applicants|applicant"))
                if at: job["applicantsCount"] = at.get_text(strip=True)
        except Exception: pass
    return jobs

def _norm(raw):
    desc = raw.get("description") or raw.get("descriptionText") or raw.get("jobDescription") or ""
    company = raw.get("companyName") or raw.get("company") or "Unknown Company"
    url = raw.get("jobUrl") or raw.get("url") or raw.get("applyUrl") or "#"
    jid = str(raw.get("id") or raw.get("jobId") or abs(hash(url+str(raw.get("title","")))))
    return {"id":jid,"title":raw.get("title","Unknown Role"),"company":company,
            "location":raw.get("location",""),"salary":raw.get("salary") or raw.get("salaryRange") or "",
            "description":desc,"requirements":raw.get("requirements") or raw.get("jobRequirements") or "",
            "url":url,"posted":raw.get("publishedAt") or raw.get("postedAt") or "",
            "applicants":str(raw.get("applicantsCount") or raw.get("numApplicants") or raw.get("views") or ""),
            "job_type":raw.get("contractType") or raw.get("employmentType") or "",
            "ai_summary":"","ai_reqs":""}

def fetch_and_enrich(keyword, location, company, date_filter):
    raw = []
    if APIFY_KEY:
        raw = _fetch_apify(keyword, location, company, date_filter)
    if not raw:
        try: raw = _fetch_guest(keyword, location, company, date_filter)
        except Exception as e: return [], f"Could not fetch jobs: {e}"
    if not raw: return [], "No jobs found. Try a broader keyword or different location."
    jobs = [_norm(r) for r in raw[:20]]
    for i,job in enumerate(jobs): jobs[i] = _ai_enrich(job)
    return jobs, ""

def _save_applied(job):
    if not _sb: return False
    try:
        _sb.table("applied_jobs").insert({
            "user_id":user_id,"company":job.get("company",""),
            "title":job.get("title",""),"description":job.get("description","")[:2000],
            "requirements":job.get("ai_reqs") or job.get("requirements",""),
            "salary":job.get("salary",""),"job_type":job.get("job_type",""),
            "location":job.get("location",""),"source_url":job.get("url",""),
            "applicants":job.get("applicants",""),"ai_summary":job.get("ai_summary",""),
        }).execute()
        return True
    except Exception: return False

def _load_applied():
    if not _sb: return []
    try:
        res = _sb.table("applied_jobs").select("*").eq("user_id",user_id).order("applied_at",desc=True).execute()
        return res.data or []
    except Exception: return []

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD  (My Applications tab)
# ══════════════════════════════════════════════════════════════════════════════
apps = get_all_applications()
df = pd.DataFrame(apps) if apps else pd.DataFrame(columns=[
    "id","company_name","position","stage","applied_date","last_updated",
    "email_subject","recruiter_email","recruiter_name","recruiter_title",
    "linkedin_url","salary_range","interview_date","interview_type","location","notes"])
for col in ["recruiter_email","recruiter_name","recruiter_title","linkedin_url",
            "salary_range","interview_date","interview_type","location","notes","email_subject"]:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].fillna("").astype(str)
if "stage" not in df.columns: df["stage"] = "Applied"
total_count = len(df)

# Filter
_search = st.session_state.app2_search
_stage  = st.session_state.app2_stage
filtered = df.copy()
if _search:
    m = (filtered.company_name.str.contains(_search,case=False,na=False) |
         filtered.position.str.contains(_search,case=False,na=False))
    filtered = filtered[m]
if _stage != "All Stages":
    filtered = filtered[filtered.stage==_stage]
ROWS = 8
total_rows  = len(filtered)
total_pages = max(1, math.ceil(total_rows/ROWS))
if st.session_state.app2_page >= total_pages: st.session_state.app2_page = total_pages-1
cur = st.session_state.app2_page
ps  = cur*ROWS; pe = min(ps+ROWS, total_rows)
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
    <button class="add-btn" id="topbar-add-btn">
      <span class="add-btn-icon">add</span> Add Application
    </button>
  </div>
</div>
<script>
document.getElementById('topbar-add-btn').onclick = function() {{
  var btns = window.parent.document.querySelectorAll('[data-testid="stButton"] button');
  for(var i=0;i<btns.length;i++){{
    if(btns[i].innerText.trim()==='__ADD__'){{btns[i].click();break;}}
  }}
}};
</script>
""", unsafe_allow_html=True)

# Hidden add trigger
_ha,_ = st.columns([1,20])
with _ha:
    if st.button("__ADD__", key="add_trigger"):
        st.session_state.app2_add_open = not st.session_state.app2_add_open
        st.rerun()
st.markdown("""<style>[data-testid="stHorizontalBlock"]:first-of-type{
  position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ADD APPLICATION FORM
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app2_add_open:
    st.markdown('<div style="padding:0 28px 0;">', unsafe_allow_html=True)
    with st.expander("➕ Add New Application", expanded=True):
        ac1, ac2 = st.columns(2)
        with ac1:
            add_co  = st.text_input("Company Name", placeholder="e.g. Google", key="add_co")
            add_pos = st.text_input("Job Title",    placeholder="e.g. Software Engineer", key="add_pos")
        with ac2:
            add_dt  = st.date_input("Applied Date", key="add_dt")
            add_stg = st.selectbox("Stage", ["Applied","Interview","Offer","Rejected"], key="add_stg")
        if st.button("➕ Save Application", type="primary", key="add_sub"):
            if add_co and add_pos:
                with st.spinner("🔍 Finding recruiter..."):
                    info = enrich_application(add_co)
                upsert_application(add_co, add_pos, str(add_dt), "Manually added",
                    info.get("recruiter_email",""), info.get("recruiter_name",""),
                    info.get("recruiter_title",""), info.get("linkedin_url",""))
                st.success(f"✅ Added **{add_pos}** at **{add_co}**")
                st.session_state.app2_add_open = False
                st.rerun()
            else:
                st.warning("Please fill in Company Name and Job Title.")
    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB SWITCHER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="app-content">', unsafe_allow_html=True)

tc1, tc2, _ = st.columns([1.2, 1.4, 8])
with tc1:
    if st.button("📋  My Applications",
                 type="primary" if st.session_state.app2_tab=="my" else "secondary",
                 key="tab_my", use_container_width=True):
        st.session_state.app2_tab = "my"; st.rerun()
with tc2:
    if st.button("🔍  Browse LinkedIn Jobs",
                 type="primary" if st.session_state.app2_tab=="browse" else "secondary",
                 key="tab_browse", use_container_width=True):
        st.session_state.app2_tab = "browse"; st.rerun()
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ══  TAB 1: MY APPLICATIONS  ═════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app2_tab == "my":

    # Filter bar
    stage_opts  = ["All Stages","Applied","Interview","Offer","Rejected"]
    stage_html  = "".join(f'<option value="{s}" {"selected" if s==_stage else ""}>{s}</option>' for s in stage_opts)

    st.markdown(f"""
    <div class="filter-row">
      <div class="search-wrap">
        <span class="search-icon">search</span>
        <input class="search-input" type="text" id="app-search"
               placeholder="Search by company or job title..." value="{_search}"
               oninput="window._doSearch(this.value)" />
      </div>
      <select class="stage-sel" id="app-stage" onchange="window._doStage(this.value)">
        {stage_html}
      </select>
      <button class="filters-btn">
        <span style="font-family:'Material Symbols Outlined';font-size:16px;line-height:1;
                     font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;">tune</span>
        Filters
      </button>
    </div>
    """, unsafe_allow_html=True)

    # Hidden Streamlit filter inputs
    _fc1, _fc2, _ = st.columns([3, 1, 6])
    with _fc1:
        sv = st.text_input("SRH", value=_search, key="app2_srh_w", label_visibility="collapsed")
    with _fc2:
        stv = st.selectbox("STG", stage_opts, key="app2_stg_w", label_visibility="collapsed")
    if sv != _search: st.session_state.app2_search=sv; st.rerun()
    if stv != _stage: st.session_state.app2_stage=stv; st.rerun()
    st.markdown("""<style>[data-testid="stHorizontalBlock"]:nth-of-type(2){
      position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
    </style>""", unsafe_allow_html=True)

    # ── TABLE ────────────────────────────────────────────────────────────────
    SCLS = {"Applied":"s-Applied","Interview":"s-Interview","Offer":"s-Offer",
            "Rejected":"s-Rejected","Wishlist":"s-Wishlist"}

    rows_html = ""
    if page_df.empty:
        rows_html = ('<tr><td colspan="6" style="text-align:center;color:#94a3b8;'
                     'padding:60px;font-size:0.9rem;">&#128235; No applications yet. '
                     'Add one above or sync Gmail from the Dashboard.</td></tr>')
    else:
        for i, (_, r) in enumerate(page_df.iterrows()):
            stage   = str(r.get("stage","Applied"))
            rec_n   = str(r.get("recruiter_name","")).strip()
            li      = str(r.get("linkedin_url","")).strip()
            has_rec = bool(rec_n or li)
            let     = str(r["company_name"])[0].upper() if r["company_name"] else "?"
            bcls    = SCLS.get(stage,"s-Applied")
            abs_idx = ps + i
            rows_html += f"""
            <tr onclick="window._openMod({abs_idx})" data-idx="{abs_idx}">
              <td><div class="co-cell">
                <div class="co-av">{let}</div>
                <span class="co-name">{r['company_name']}</span>
              </div></td>
              <td style="color:#475569;">{r['position']}</td>
              <td style="color:#64748b;white-space:nowrap;">{r.get('applied_date','')}</td>
              <td><span class="s-badge {bcls}">{stage}</span></td>
              <td style="text-align:center;">
                {'<span class="rec-yes">&#10003;</span>' if has_rec else '<span class="rec-no"></span>'}
              </td>
              <td>
                <button class="view-det" onclick="event.stopPropagation();window._openMod({abs_idx})">
                  View Details
                </button>
              </td>
            </tr>"""

    # Pagination
    def _pslots(c,t):
        if t<=7: return list(range(t))
        r=[0]; lo,hi=max(1,c-2),min(t-2,c+2)
        if lo>1: r.append(None)
        r.extend(range(lo,hi+1))
        if hi<t-2: r.append(None)
        r.append(t-1); return r

    sl = _pslots(cur, total_pages) if total_pages > 1 else []
    pg_btns = ""
    if total_pages > 1:
        pd_ = "disabled" if cur==0 else ""
        nd_ = "disabled" if cur==total_pages-1 else ""
        pg_btns += f'<button class="pg-nav" onclick="window._pgP()" {pd_}>&#8249;</button>'
        for s in sl:
            if s is None: pg_btns += '<span style="color:#94a3b8;padding:0 3px;">…</span>'
            else: pg_btns += f'<button class="pg-b {"active" if s==cur else ""}" onclick="window._pgG({s})">{s+1}</button>'
        pg_btns += f'<button class="pg-nav" onclick="window._pgN()" {nd_}>&#8250;</button>'

    st.markdown(f"""
    <div class="tbl-card">
      <table class="tbl-table">
        <thead><tr>
          <th>Company Name</th><th>Job Title</th><th>Applied Date</th>
          <th>Stage</th><th style="text-align:center;">Recruiter Found</th><th>Actions</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
      <div class="pg-row">
        <span class="pg-info">Showing {ps+1} to {pe} of {total_rows} applications</span>
        <div class="pg-btns">{pg_btns}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Hidden Streamlit pagination
    if total_pages > 1:
        bc = st.columns(2 + len(sl))
        with bc[0]:
            if st.button("&#9664;",key="pg2_p",disabled=(cur==0),use_container_width=True):
                st.session_state.app2_page=cur-1; st.rerun()
        for i,s in enumerate(sl):
            with bc[i+1]:
                if s is None:
                    st.markdown("<div style='text-align:center;color:#94a3b8;'>…</div>",unsafe_allow_html=True)
                else:
                    if st.button(str(s+1),key=f"pg2_{s}",
                                 type="primary" if s==cur else "secondary",
                                 use_container_width=True):
                        st.session_state.app2_page=s; st.rerun()
        with bc[-1]:
            if st.button("&#9654;",key="pg2_n",disabled=(cur==total_pages-1),use_container_width=True):
                st.session_state.app2_page=cur+1; st.rerun()
        st.markdown("""<style>[data-testid="stHorizontalBlock"]:nth-of-type(3){
          position:absolute;opacity:0;pointer-events:none;height:0;overflow:hidden;}
        </style>""", unsafe_allow_html=True)

    # ── MODAL ────────────────────────────────────────────────────────────────
    rows_json = []
    for _, r in filtered.iterrows():
        rows_json.append({
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

    st.markdown(f"""
    <div id="app-modal" style="display:none;" class="mod-overlay"
         onclick="if(event.target===this)window._closeMod()">
      <div class="mod-box">
        <div class="mod-hdr">
          <div>
            <div class="mod-co" id="m-co"></div>
            <div class="mod-title" id="m-ti"></div>
          </div>
          <button class="mod-close" onclick="window._closeMod()">close</button>
        </div>
        <div class="mod-body">
          <div class="mod-pills" id="m-pills"></div>
          <div class="mod-grid" id="m-grid"></div>
          <div id="m-email-wrap" style="display:none;">
            <div class="mod-sec-lbl">Source Email</div>
            <div class="mod-text" id="m-email" style="font-size:0.82rem;"></div>
          </div>
          <div id="m-rec-wrap" style="display:none;">
            <div class="mod-sec-lbl">Recruiter</div>
            <div class="mod-rec" id="m-rec"></div>
          </div>
          <div id="m-notes-wrap" style="display:none;">
            <div class="mod-sec-lbl">Notes</div>
            <div class="mod-text" id="m-notes"></div>
          </div>
        </div>
        <div class="mod-foot">
          <a id="m-li" href="#" target="_blank"
             style="display:none;flex:1;padding:10px;border-radius:10px;background:#eff6ff;
                    color:#2563EB;font-size:0.875rem;font-weight:700;text-align:center;
                    text-decoration:none!important;border:1px solid #bfdbfe;">
            &#128279; View on LinkedIn
          </a>
          <button class="mod-btn-s" onclick="window._closeMod()">Close</button>
        </div>
      </div>
    </div>
    <script>
    var _D = {json.dumps(rows_json)};
    function _sb2(s){{
      var m={{"Applied":"mp-Applied","Interview":"mp-Interview","Offer":"mp-Offer","Rejected":"mp-Rejected"}};
      return '<span class="mpill '+(m[s]||"mp-Applied")+'">'+s+'</span>';
    }}
    window._openMod = function(i){{
      var r=_D[i]; if(!r)return;
      document.getElementById('m-co').textContent  = r.company.toUpperCase();
      document.getElementById('m-ti').textContent  = r.title;
      var p=_sb2(r.stage);
      if(r.location) p+='<span class="mpill mp-loc">&#128205; '+r.location+'</span>';
      if(r.salary)   p+='<span class="mpill mp-sal">&#128176; '+r.salary+'</span>';
      if(r.recruiter_name) p+='<span class="mpill mp-rec">&#128100; Recruiter Found</span>';
      document.getElementById('m-pills').innerHTML=p;
      var g='';
      g+='<div class="mod-cell"><div class="mod-cell-lbl">Applied Date</div><div class="mod-cell-val">'+(r.applied_date||'—')+'</div></div>';
      g+='<div class="mod-cell"><div class="mod-cell-lbl">Stage</div><div class="mod-cell-val">'+r.stage+'</div></div>';
      g+='<div class="mod-cell"><div class="mod-cell-lbl">Last Updated</div><div class="mod-cell-val">'+(r.last_updated||'—')+'</div></div>';
      if(r.interview_date) g+='<div class="mod-cell"><div class="mod-cell-lbl">Interview Date</div><div class="mod-cell-val">'+r.interview_date+'</div></div>';
      if(r.interview_type) g+='<div class="mod-cell"><div class="mod-cell-lbl">Interview Type</div><div class="mod-cell-val">'+r.interview_type+'</div></div>';
      if(r.salary)         g+='<div class="mod-cell"><div class="mod-cell-lbl">Salary Range</div><div class="mod-cell-val">'+r.salary+'</div></div>';
      document.getElementById('m-grid').innerHTML=g;
      var ew=document.getElementById('m-email-wrap');
      if(r.email_subject&&r.email_subject!=='Manually added'){{document.getElementById('m-email').textContent=r.email_subject;ew.style.display='';}}
      else ew.style.display='none';
      var rw=document.getElementById('m-rec-wrap');
      if(r.recruiter_name||r.recruiter_email||r.linkedin_url){{
        var rc='';
        if(r.recruiter_name)  rc+='<div style="font-weight:700;color:#0f172a;font-size:0.9rem;margin-bottom:3px;">&#128100; '+r.recruiter_name+'</div>';
        if(r.recruiter_title) rc+='<div style="color:#64748b;font-size:0.8rem;margin-bottom:5px;">'+r.recruiter_title+'</div>';
        if(r.recruiter_email) rc+='<div style="font-size:0.82rem;color:#334155;">&#9993; '+r.recruiter_email+'</div>';
        document.getElementById('m-rec').innerHTML=rc;
        rw.style.display='';
      }} else rw.style.display='none';
      var li=document.getElementById('m-li');
      if(r.linkedin_url){{li.href=r.linkedin_url;li.style.display='block';}}
      else li.style.display='none';
      var nw=document.getElementById('m-notes-wrap');
      if(r.notes){{document.getElementById('m-notes').textContent=r.notes;nw.style.display='';}}
      else nw.style.display='none';
      document.getElementById('app-modal').style.display='flex';
      document.body.style.overflow='hidden';
    }};
    window._closeMod=function(){{
      document.getElementById('app-modal').style.display='none';
      document.body.style.overflow='';
    }};
    document.addEventListener('keydown',function(e){{if(e.key==='Escape')window._closeMod();}});
    window._doSearch=function(v){{
      var inp=window.parent.document.querySelectorAll('[data-testid="stTextInput"] input');
      if(inp.length){{
        var s=Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
        s.call(inp[0],v); inp[0].dispatchEvent(new Event('input',{{bubbles:true}}));
      }}
    }};
    window._doStage=function(v){{}};
    window._pgP=function(){{var b=window.parent.document.querySelectorAll('[data-testid="stButton"] button');for(var i=0;i<b.length;i++){{if(b[i].textContent.trim()==='◄'){{b[i].click();break;}}}}}};
    window._pgN=function(){{var b=window.parent.document.querySelectorAll('[data-testid="stButton"] button');for(var i=0;i<b.length;i++){{if(b[i].textContent.trim()==='►'){{b[i].click();break;}}}}}};
    window._pgG=function(n){{var b=window.parent.document.querySelectorAll('[data-testid="stButton"] button');for(var i=0;i<b.length;i++){{if(b[i].textContent.trim()===String(n+1)){{b[i].click();break;}}}}}};
    </script>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  TAB 2: BROWSE LINKEDIN JOBS  ════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
else:
    # Search panel
    st.markdown('<div class="search-panel"><div class="search-panel-lbl">&#128269; Search LinkedIn Jobs</div>', unsafe_allow_html=True)
    f1,f2,f3,f4 = st.columns([3,2,2,2])
    with f1: kw        = st.text_input("Role",     placeholder="e.g. Data Scientist",   key="jb_kw",   label_visibility="collapsed")
    with f2: company_q = st.text_input("Company",  placeholder="e.g. Google",           key="jb_co",   label_visibility="collapsed")
    with f3: location_q= st.text_input("Location", placeholder="e.g. New York, Remote", key="jb_loc",  label_visibility="collapsed")
    with f4: date_f    = st.selectbox("Posted",["Any time","Last 24 hours","Past week","Past month"],key="jb_date",label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    _,bc,_ = st.columns([4,2,4])
    with bc:
        search_clicked = st.button("&#128640; Search Jobs", type="primary", use_container_width=True, key="jb_search")

    if search_clicked:
        if not kw.strip() and not company_q.strip():
            st.warning("⚠️ Please enter a job title or company name.")
        else:
            with st.status("&#128269; Fetching jobs &amp; generating AI insights…", expanded=True) as status:
                st.write("⏳ Connecting to LinkedIn data sources…")
                jobs, err = fetch_and_enrich(kw, location_q, company_q, date_f)
                if err:
                    status.update(label=f"❌ {err}", state="error")
                    st.session_state.job_results = []
                else:
                    st.write(f"✅ Found {len(jobs)} jobs · AI extracted summaries & requirements")
                    st.session_state.job_results = jobs
                    status.update(label=f"✅ {len(jobs)} jobs ready!", state="complete")

    jobs = st.session_state.get("job_results", [])

    if not jobs:
        st.markdown("""
        <div class="empty-box">
          <div style="font-size:2.5rem;margin-bottom:12px;">&#127919;</div>
          <div style="font-size:1rem;font-weight:600;color:#64748b;">Search for live LinkedIn jobs above</div>
          <div style="font-size:0.85rem;color:#94a3b8;margin-top:6px;">AI summaries &amp; requirements extracted · Saved only when you apply</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='font-size:0.875rem;color:#64748b;margin-bottom:16px;'>"
                    f"Showing <strong>{len(jobs)}</strong> live results · "
                    f"<span style='color:#2563EB;font-weight:600;font-size:0.78rem;'>Session-only — saved on Apply</span></div>",
                    unsafe_allow_html=True)

        for job in jobs:
            jid = str(job["id"])
            already = jid in st.session_state.applied_jobs

            # Build pill row (pre-built to avoid f-string rendering bug)
            pills = []
            if already:               pills.append('<span class="pill p-applied">&#10003; Applied</span>')
            if job.get("salary"):      pills.append(f'<span class="pill p-salary">&#128176; {job["salary"]}</span>')
            if job.get("job_type"):    pills.append(f'<span class="pill p-type">{job["job_type"]}</span>')
            if job.get("applicants"):  pills.append(f'<span class="pill p-views">&#128101; {job["applicants"]}</span>')
            if job.get("posted"):      pills.append(f'<span class="pill p-posted">&#128336; {job["posted"]}</span>')
            pills_html = "".join(pills)

            meta_parts = []
            if job.get("location"): meta_parts.append(f"&#128205; {job['location']}")
            meta_html = "  &nbsp;&#183;&nbsp;  ".join(meta_parts)

            summary   = job.get("ai_summary","") or job.get("description","")[:250]
            ai_reqs   = job.get("ai_reqs","")   or job.get("requirements","")[:400]
            desc_full = job.get("description","")

            # Build conditional blocks outside f-string
            reqs_block = ""
            if ai_reqs:
                clean = ai_reqs.replace("•","<br>•").lstrip("<br>")
                reqs_block = f'<div class="card-div"></div><div class="sec-lbl">Key Requirements &amp; Qualifications</div><div class="sec-req">{clean}</div>'

            desc_block = ""
            if desc_full and desc_full.strip() != summary.strip():
                preview = desc_full[:600] + ("…" if len(desc_full)>600 else "")
                desc_block = f'<div class="card-div"></div><div class="sec-lbl">Full Description</div><div class="sec-txt" style="font-size:0.82rem;">{preview}</div>'

            col_l, col_r = st.columns([8,2], gap="medium")
            with col_l:
                st.markdown(
                    f'<div class="job-card">'
                    f'<div class="jc-co">&#127970; {job["company"]}</div>'
                    f'<div class="jc-title">{job["title"]}</div>'
                    f'<div class="jc-meta">{meta_html}</div>'
                    f'<div style="margin-bottom:12px;">{pills_html}</div>'
                    f'<div class="sec-lbl">AI Summary</div>'
                    f'<div class="sec-txt">{summary}</div>'
                    f'{reqs_block}'
                    f'{desc_block}'
                    f'</div>',
                    unsafe_allow_html=True)

            with col_r:
                st.markdown("<div style='padding-top:22px;'>", unsafe_allow_html=True)
                if job.get("url") and job["url"] != "#":
                    st.link_button("&#128279; View on LinkedIn", job["url"], use_container_width=True)
                if already:
                    st.button("&#10003; Applied", key=f"ap_{jid}", disabled=True, use_container_width=True)
                else:
                    if st.button("&#128640; Apply Now", key=f"ap_{jid}", type="primary", use_container_width=True):
                        _save_applied(job)
                        st.session_state.applied_jobs[jid] = job
                        st.success(f"✅ Saved **{job['title']}** at **{job['company']}**!")
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# close app-content
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.caption("CareerSync v3.0 · Applications · LinkedIn via Apify · AI by Groq · ❤️")