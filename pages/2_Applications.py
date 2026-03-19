import os, sys, json, re, time, requests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import streamlit as st
from auth import get_user_by_id, inject_gmail_env

st.set_page_config(
    page_title="CareerSync — Applications",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# AUTH GUARD
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
    for k in ["user", "user_id"]: st.session_state.pop(k, None)
    st.query_params.clear()
    st.switch_page("app.py")

if not _restore():
    st.switch_page("app.py"); st.stop()

user = st.session_state["user"]
st.query_params["uid"] = user["id"]
inject_gmail_env(user)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG & KEYS
# ══════════════════════════════════════════════════════════════════════════════
def _get(key, default=""):
    try:
        val = st.secrets.get(key, "")
        if val: return val
    except Exception: pass
    return os.getenv(key, default)

GROQ_KEY    = _get("GROQ_API_KEY")
APIFY_KEY   = _get("APIFY_API_KEY")
GOOGLE_KEY  = _get("GOOGLE_API_KEY")
GOOGLE_CSE  = _get("GOOGLE_CSE_ID")
SUP_URL     = _get("SUPABASE_URL")
SUP_KEY     = _get("SUPABASE_KEY")

try:
    from supabase import create_client
    _sb = create_client(SUP_URL, SUP_KEY) if SUP_URL and SUP_KEY else None
except Exception:
    _sb = None

user_id = user["id"]

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');
    [data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important;}
    [data-testid="stSidebar"] .stButton>button{
      text-align:left!important;justify-content:flex-start!important;
      background:transparent!important;color:#475569!important;
      border:none!important;box-shadow:none!important;
      font-size:0.9rem!important;font-weight:500!important;
      padding:9px 12px!important;border-radius:8px!important;width:100%!important;
      font-family:'DM Sans',sans-serif!important;}
    [data-testid="stSidebar"] .stButton>button:hover{background:#f8fafc!important;color:#0f172a!important;}
    [data-testid="collapsedControl"]{display:none!important;}
    </style>
    """, unsafe_allow_html=True)

    name_disp  = user.get("name", "User")
    email_disp = user.get("email", "")
    avatar_let = name_disp[0].upper() if name_disp else "U"

    st.markdown(f"""
    <div style="padding:20px 16px 16px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #f1f5f9;">
      <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;display:flex;
                  align-items:center;justify-content:center;flex-shrink:0;">
        <span style="font-family:'Material Symbols Outlined';font-size:17px;color:#fff;
                     font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">sync_alt</span>
      </div>
      <span style="font-size:1.1rem;font-weight:700;color:#0f172a;font-family:'DM Sans',sans-serif;">CareerSync</span>
    </div>
    <div style="padding:12px 12px 8px;">
    """, unsafe_allow_html=True)

    nav_pages = [
        ("dashboard",  "Dashboard",        "pages/1_Dashboard.py"),
        ("work",       "Applications",     "pages/2_Applications.py"),
        ("mail",       "Cold Email",       "pages/3_Cold_Email.py"),
        ("plumbing",   "Research Pipeline","pages/4_Pipeline.py"),
        ("settings",   "Settings",         "pages/5_Settings.py"),
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
          <div style="font-size:0.7rem;color:#64748b;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{email_disp}</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
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
.block-container{padding-top:1.5rem!important;padding-bottom:3rem!important;max-width:1180px!important;}

/* ══ FULL-WIDTH JOB CARD ══ */
.jcard{background:#fff;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;
  box-shadow:0 1px 4px rgba(0,0,0,0.04);transition:box-shadow 0.15s;margin-bottom:12px;}
.jcard:hover{box-shadow:0 6px 24px rgba(0,0,0,0.09);}
.jcard-body{padding:22px 26px 18px;}
.jcard-top{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:4px;}
.jcard-company{font-size:0.72rem;font-weight:700;color:#2563EB;text-transform:uppercase;
  letter-spacing:0.8px;display:flex;align-items:center;gap:5px;}
.jcard-title{font-size:1.05rem;font-weight:700;color:#0f172a;line-height:1.35;margin:5px 0 10px;}
.jcard-meta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:12px;}
.jcard-meta-item{font-size:0.8rem;color:#64748b;display:flex;align-items:center;gap:4px;}
.pill-row{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;}
.pill{display:inline-flex;align-items:center;gap:4px;padding:4px 11px;border-radius:9999px;
  font-size:0.72rem;font-weight:700;white-space:nowrap;}
.p-applied{background:#dcfce7;color:#15803d;}
.p-salary {background:#fef9c3;color:#854d0e;}
.p-views  {background:#ede9fe;color:#6d28d9;}
.p-posted {background:#f0f9ff;color:#0369a1;}
.p-type   {background:#f1f5f9;color:#475569;}
.jdivider{height:1px;background:#f1f5f9;margin:14px 0;}
.jsec-lbl{font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.8px;margin-bottom:6px;}
.jsec-txt{font-size:0.875rem;color:#475569;line-height:1.75;}
.jsec-req{font-size:0.875rem;color:#334155;line-height:1.75;padding:12px 16px;
  background:#f8fafc;border-radius:10px;border-left:3px solid #2563EB;}
.jcard-footer{padding:14px 26px;background:#f8fafc;border-top:1px solid #f1f5f9;
  display:flex;align-items:center;gap:10px;}
.jcard-apply{flex:1;padding:10px 0;border-radius:10px;background:#2563EB;color:#fff;
  font-size:0.9rem;font-weight:700;border:none;cursor:pointer;font-family:'DM Sans',sans-serif;
  box-shadow:0 2px 8px rgba(37,99,235,0.25);transition:background 0.15s;text-align:center;}
.jcard-apply:hover{background:#1d4ed8;}
.jcard-applied{flex:1;padding:10px 0;border-radius:10px;background:#dcfce7;color:#15803d;
  font-size:0.9rem;font-weight:700;border:1px solid #bbf7d0;cursor:default;
  font-family:'DM Sans',sans-serif;text-align:center;}
.jcard-view{padding:10px 18px;border-radius:10px;background:#fff;color:#2563EB;
  font-size:0.875rem;font-weight:700;border:1px solid #bfdbfe;cursor:pointer;
  font-family:'DM Sans',sans-serif;text-decoration:none!important;
  display:inline-flex;align-items:center;gap:5px;white-space:nowrap;transition:background 0.15s;}
.jcard-view:hover{background:#eff6ff;}

/* ── SEARCH PANEL ── */
.search-panel{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:22px 24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.search-panel-title{font-size:0.7rem;font-weight:700;color:#0f172a;
  text-transform:uppercase;letter-spacing:0.8px;margin-bottom:14px;}

/* ══ APPLIED JOBS — CLEAN TABLE ══ */
.app-wrap{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.app-tbl{width:100%;border-collapse:collapse;}
.app-tbl th{padding:13px 20px;font-size:0.7rem;font-weight:700;color:#94a3b8;
  text-transform:uppercase;letter-spacing:0.7px;text-align:left;white-space:nowrap;
  border-bottom:1px solid #f1f5f9;}
.app-tbl td{padding:16px 20px;border-bottom:1px solid #f1f5f9;font-size:0.875rem;
  color:#334155;vertical-align:middle;}
.app-tbl tr:last-child td{border-bottom:none;}
.app-tbl tbody tr{cursor:pointer;transition:background 0.1s;}
.app-tbl tbody tr:hover td{background:#f8fafc;}
.co-cell{display:flex;align-items:center;gap:12px;}
.co-av{width:36px;height:36px;border-radius:9px;background:#f1f5f9;display:flex;
  align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;
  color:#475569;flex-shrink:0;border:1px solid #e8edf2;}
.co-nm{font-weight:600;color:#0f172a;font-size:0.9rem;}
.sbadge{display:inline-flex;align-items:center;padding:4px 12px;border-radius:7px;font-size:0.78rem;font-weight:600;}
.sb-Applied  {background:#f1f5f9;color:#475569;}
.sb-Interview{background:#dbeafe;color:#1d4ed8;}
.sb-Offer    {background:#dcfce7;color:#15803d;}
.sb-Rejected {background:#fee2e2;color:#dc2626;}
.rdot-y{width:22px;height:22px;border-radius:50%;background:#22c55e;
  display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:700;}
.rdot-n{width:22px;height:22px;border-radius:50%;background:#e2e8f0;display:inline-block;}
.vdet{color:#2563EB;font-weight:600;font-size:0.875rem;cursor:pointer;
  border:none;background:none;font-family:'DM Sans',sans-serif;padding:0;}
.vdet:hover{text-decoration:underline;}

/* ══ MODAL ══ */
.mod-ov{position:fixed;inset:0;background:rgba(15,23,42,0.5);z-index:9999;
  display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(3px);}
.mod-box{background:#fff;border-radius:20px;width:100%;max-width:680px;max-height:90vh;
  overflow-y:auto;box-shadow:0 24px 60px rgba(0,0,0,0.2);}
.mod-box::-webkit-scrollbar{width:5px;}
.mod-box::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:3px;}
.mod-hdr{padding:24px 28px 18px;border-bottom:1px solid #f1f5f9;display:flex;
  align-items:flex-start;justify-content:space-between;position:sticky;top:0;
  background:#fff;z-index:1;border-radius:20px 20px 0 0;}
.mod-co{font-size:0.7rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:5px;}
.mod-ti{font-size:1.15rem;font-weight:700;color:#0f172a;line-height:1.3;}
.mod-x{width:30px;height:30px;border-radius:8px;border:1px solid #e2e8f0;background:#fff;
  display:flex;align-items:center;justify-content:center;cursor:pointer;color:#64748b;
  font-family:'Material Symbols Outlined';font-size:18px;flex-shrink:0;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;transition:background 0.15s;}
.mod-x:hover{background:#f8fafc;}
.mod-body{padding:22px 28px;}
.mod-pills{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:18px;}
.mpill{display:inline-flex;align-items:center;gap:4px;padding:4px 12px;border-radius:9999px;font-size:0.75rem;font-weight:600;}
.mp-Applied  {background:#f1f5f9;color:#475569;}
.mp-Interview{background:#dbeafe;color:#1d4ed8;}
.mp-Offer    {background:#dcfce7;color:#15803d;}
.mp-Rejected {background:#fee2e2;color:#dc2626;}
.mp-loc{background:#f0f9ff;color:#0369a1;}
.mp-sal{background:#fef9c3;color:#854d0e;}
.mp-rec{background:#dcfce7;color:#15803d;}
.mp-typ{background:#f1f5f9;color:#475569;}
.mp-app{background:#ede9fe;color:#6d28d9;}
.mod-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;}
.mod-cell{background:#f8fafc;border-radius:10px;padding:12px 14px;}
.mod-cell-l{font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.6px;margin-bottom:3px;}
.mod-cell-v{font-size:0.875rem;font-weight:600;color:#0f172a;}
.mod-sl{font-size:0.68rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.7px;margin:16px 0 7px;}
.mod-txt{font-size:0.875rem;color:#475569;line-height:1.7;background:#f8fafc;padding:12px 14px;border-radius:10px;}
.mod-req{font-size:0.875rem;color:#334155;line-height:1.75;padding:12px 16px;
  background:#f8fafc;border-radius:10px;border-left:3px solid #2563EB;}
.mod-rec-box{background:#f8fafc;border-radius:10px;padding:12px 14px;}
.mod-foot{display:flex;gap:10px;padding:18px 28px;border-top:1px solid #f1f5f9;
  position:sticky;bottom:0;background:#fff;border-radius:0 0 20px 20px;}
.mod-li-btn{flex:1;padding:10px;border-radius:10px;background:#eff6ff;color:#2563EB;
  font-size:0.875rem;font-weight:700;text-align:center;text-decoration:none!important;
  border:1px solid #bfdbfe;display:block;}
.mod-li-btn:hover{background:#dbeafe;}
.mod-close{flex:1;padding:10px;border-radius:10px;background:#fff;color:#475569;
  font-size:0.875rem;font-weight:700;border:1px solid #e2e8f0;cursor:pointer;
  font-family:'DM Sans',sans-serif;transition:all 0.15s;}
.mod-close:hover{background:#f8fafc;}

/* ── STAT CARDS ── */
.stat-mini{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:18px;
  text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.stat-mini-val{font-size:1.8rem;font-weight:700;line-height:1;}
.stat-mini-lbl{font-size:0.7rem;color:#64748b;font-weight:700;text-transform:uppercase;
  letter-spacing:0.7px;margin-top:4px;}

/* ── STREAMLIT OVERRIDES ── */
div.stButton>button{background:#fff!important;color:#475569!important;
  border:1px solid #e2e8f0!important;border-radius:8px!important;font-weight:600!important;
  font-size:0.85rem!important;font-family:'DM Sans',sans-serif!important;
  padding:8px 14px!important;transition:all 0.15s!important;}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{background:#2563EB!important;color:#fff!important;
  border-color:#2563EB!important;box-shadow:0 2px 8px rgba(37,99,235,0.25)!important;}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}
div[data-testid="stTextInput"] input{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
.stAlert{border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("app_view","browse"),("job_results",[]),("applied_jobs",{}),("ai_data",{})]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS  (identical to original)
# ══════════════════════════════════════════════════════════════════════════════
def _groq(prompt: str, max_tokens: int = 300) -> str:
    if not GROQ_KEY: return ""
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model":"llama-3.1-8b-instant",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":max_tokens,"temperature":0.3},timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception: return ""

def _ai_enrich(job: dict) -> dict:
    title = job.get("title",""); desc = job.get("description","")[:2500]; reqs = job.get("requirements","")[:1000]
    if not desc and not reqs:
        job["ai_summary"] = "No description available for this listing."; job["ai_reqs"] = ""; return job
    combined = f"Title: {title}\n\nDescription:\n{desc}\n\nRequirements:\n{reqs}"
    prompt = f"""{combined}

Based on the above job listing, return a JSON object with exactly these keys:
{{
  "summary": "2 sentences describing what the role involves and who it is for",
  "requirements": "bullet list of 4-6 key requirements/qualifications, each on a new line starting with •",
  "salary": "salary range if mentioned anywhere, else empty string",
  "job_type": "Full-time / Part-time / Contract / Internship based on description, else empty string"
}}
Return ONLY the JSON, no markdown, no explanation."""
    raw = _groq(prompt, max_tokens=400)
    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        data = json.loads(raw)
        job["ai_summary"] = data.get("summary", "")
        job["ai_reqs"]    = data.get("requirements", "")
        if not job.get("salary"):   job["salary"]   = data.get("salary", "")
        if not job.get("job_type"): job["job_type"] = data.get("job_type", "")
    except Exception:
        job["ai_summary"] = _groq(f"Summarise this job in 2 sentences:\nTitle: {title}\n{desc[:800]}", max_tokens=120)
        job["ai_reqs"] = reqs[:400] if reqs else ""
    return job

def _fetch_apify(keyword, location, company, date_filter):
    if not APIFY_KEY: return []
    date_map = {"Any time":"","Last 24 hours":"r86400","Past week":"r604800","Past month":"r2592000"}
    search_kw = keyword.strip()
    if company.strip(): search_kw = f"{company.strip()} {search_kw}".strip()
    input_data = {"title":search_kw,"location":location.strip() or "United States",
                  "rows":20,"scrapeCompany":True,"proxy":{"useApifyProxy":True}}
    if date_map.get(date_filter): input_data["publishedAt"] = date_map[date_filter]
    try:
        resp = requests.post("https://api.apify.com/v2/acts/bebity~linkedin-jobs-scraper/run-sync-get-dataset-items",
            params={"token":APIFY_KEY,"timeout":90,"memory":512},json=input_data,timeout=100)
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list): return items
    except Exception: pass
    return []

def _fetch_linkedin_guest(keyword, location, company, date_filter):
    from bs4 import BeautifulSoup
    date_map = {"Any time":"","Last 24 hours":"r86400","Past week":"r604800","Past month":"r2592000"}
    f_tpr = date_map.get(date_filter, "")
    search_kw = keyword.strip()
    if company.strip(): search_kw = f"{search_kw} {company.strip()}".strip()
    if not search_kw: return []
    hdrs = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36","Accept-Language":"en-US,en;q=0.9"}
    params = {"keywords":search_kw,"location":location.strip(),"start":0,"count":25}
    if f_tpr: params["f_TPR"] = f_tpr
    try:
        resp = requests.get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",params=params,headers=hdrs,timeout=20)
        if resp.status_code != 200: return []
    except Exception: return []
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for card in soup.find_all("li")[:20]:
        try:
            entity = card.find("div", {"data-entity-urn":True}); job_id = ""
            if entity: job_id = entity.get("data-entity-urn","").split(":")[-1]
            if not job_id:
                link_tag = card.find("a", href=re.compile(r"/jobs/view/(\d+)"))
                if link_tag:
                    m = re.search(r"/jobs/view/(\d+)", link_tag["href"])
                    if m: job_id = m.group(1)
            if not job_id: continue
            title_tag   = card.find("h3") or card.find("span",class_=re.compile("title"))
            company_tag = card.find("h4") or card.find("a",class_=re.compile("hidden-nested-link"))
            loc_tag     = card.find("span",class_=re.compile("job-search-card__location"))
            time_tag    = card.find("time")
            link_a      = card.find("a", href=re.compile(r"linkedin\.com/jobs"))
            job_url = (link_a["href"].split("?")[0] if link_a else f"https://www.linkedin.com/jobs/view/{job_id}")
            jobs.append({"id":job_id,
                "title":title_tag.get_text(strip=True) if title_tag else "Unknown Role",
                "companyName":company_tag.get_text(strip=True) if company_tag else "Unknown Company",
                "location":loc_tag.get_text(strip=True) if loc_tag else "",
                "publishedAt":time_tag.get("datetime","") if time_tag else "",
                "jobUrl":job_url,"description":"","salary":"","applicantsCount":"","requirements":""})
        except Exception: continue
    for job in jobs[:12]:
        try:
            det = requests.get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job['id']}",headers=hdrs,timeout=10)
            if det.status_code == 200:
                ds = BeautifulSoup(det.text, "html.parser")
                desc_tag = ds.find("div", class_=re.compile("description__text")) or ds.find("div", class_=re.compile("show-more-less-html"))
                if desc_tag: job["description"] = desc_tag.get_text(separator=" ", strip=True)[:3000]
                sal_tag = ds.find("span", class_=re.compile("compensation"))
                if sal_tag: job["salary"] = sal_tag.get_text(strip=True)
                app_tag = ds.find("span", class_=re.compile("num-applicants|applicant"))
                if app_tag: job["applicantsCount"] = app_tag.get_text(strip=True)
        except Exception: pass
    return jobs

def _normalise(raw: dict) -> dict:
    desc = raw.get("description") or raw.get("descriptionText") or raw.get("jobDescription") or ""
    company = raw.get("companyName") or raw.get("company") or "Unknown Company"
    url = raw.get("jobUrl") or raw.get("url") or raw.get("applyUrl") or "#"
    job_id = str(raw.get("id") or raw.get("jobId") or abs(hash(url + str(raw.get("title","")))))
    return {"id":job_id,"title":raw.get("title","Unknown Role"),"company":company,
            "location":raw.get("location",""),"salary":raw.get("salary") or raw.get("salaryRange") or "",
            "description":desc,"requirements":raw.get("requirements") or raw.get("jobRequirements") or "",
            "url":url,"posted":raw.get("publishedAt") or raw.get("postedAt") or raw.get("posted_date") or "",
            "applicants":str(raw.get("applicantsCount") or raw.get("numApplicants") or raw.get("views") or ""),
            "job_type":raw.get("contractType") or raw.get("employmentType") or "",
            "company_url":raw.get("companyUrl",""),"logo_url":raw.get("companyLogo",""),
            "ai_summary":"","ai_reqs":""}

def fetch_and_enrich(keyword, location, company, date_filter):
    raw = []
    if APIFY_KEY:
        raw = _fetch_apify(keyword, location, company, date_filter)
    if not raw:
        try:
            raw = _fetch_linkedin_guest(keyword, location, company, date_filter)
        except Exception as e:
            return [], f"Could not fetch jobs: {e}"
    if not raw:
        return [], "No jobs found. Try a broader keyword or different location."
    jobs = [_normalise(r) for r in raw[:20]]
    for i, job in enumerate(jobs): jobs[i] = _ai_enrich(job)
    return jobs, ""

def _save_applied(job: dict) -> bool:
    if not _sb: return False
    try:
        _sb.table("applied_jobs").insert({
            "user_id":user_id,"company":job.get("company",""),"title":job.get("title",""),
            "description":job.get("description","")[:2000],
            "requirements":job.get("ai_reqs") or job.get("requirements",""),
            "salary":job.get("salary",""),"job_type":job.get("job_type",""),
            "location":job.get("location",""),"source_url":job.get("url",""),
            "applicants":job.get("applicants",""),"ai_summary":job.get("ai_summary",""),
        }).execute(); return True
    except Exception: return False

def _load_applied() -> list[dict]:
    if not _sb: return []
    try:
        res = _sb.table("applied_jobs").select("*").eq("user_id",user_id).order("applied_at",desc=True).execute()
        return res.data or []
    except Exception: return []

# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER + TOGGLE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h2 style='font-size:1.5rem;font-weight:700;color:#0f172a;margin-bottom:4px;'>Job Applications</h2>"
    "<p style='font-size:0.875rem;color:#64748b;margin-bottom:20px;'>"
    "Search live LinkedIn jobs with AI-powered insights · Track every application.</p>",
    unsafe_allow_html=True)

c_browse, c_applied, _ = st.columns([1.1, 1.1, 6])
with c_browse:
    if st.button("🔍  Browse Jobs",
                 type="primary" if st.session_state.app_view=="browse" else "secondary",
                 use_container_width=True, key="btn_browse"):
        st.session_state.app_view = "browse"; st.rerun()
with c_applied:
    if st.button("📋  Applied Jobs",
                 type="primary" if st.session_state.app_view=="applied" else "secondary",
                 use_container_width=True, key="btn_applied"):
        st.session_state.app_view = "applied"; st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VIEW A — BROWSE JOBS  ← full-width cards, all details, Apply inside card
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app_view == "browse":

    with st.container():
        st.markdown('<div class="search-panel"><div class="search-panel-title">🔍 Search LinkedIn Jobs</div>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns([3, 2, 2, 2])
        with f1: kw        = st.text_input("Role",     placeholder="e.g. Data Scientist, Product Manager", key="jb_kw",   label_visibility="collapsed")
        with f2: company_q = st.text_input("Company",  placeholder="e.g. Google, Amazon",                  key="jb_co",   label_visibility="collapsed")
        with f3: location_q= st.text_input("Location", placeholder="e.g. New York, Remote",                key="jb_loc",  label_visibility="collapsed")
        with f4: date_f    = st.selectbox("Posted", ["Any time","Last 24 hours","Past week","Past month"],  key="jb_date", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    _, btn_col, _ = st.columns([4, 2, 4])
    with btn_col:
        search_clicked = st.button("🚀  Search Jobs", type="primary", use_container_width=True, key="jb_search")

    if search_clicked:
        if not kw.strip() and not company_q.strip():
            st.warning("⚠️ Please enter a job title or company name.")
        else:
            with st.status("🔎 Fetching live LinkedIn jobs & generating AI insights…", expanded=True) as status:
                st.write("⏳ Connecting to job data sources…")
                jobs, err = fetch_and_enrich(kw, location_q, company_q, date_f)
                if err:
                    status.update(label=f"❌ {err}", state="error")
                    st.session_state.job_results = []
                else:
                    st.write(f"✅ Found {len(jobs)} jobs")
                    st.write("🤖 AI extracted summaries, requirements & salary from each listing")
                    st.session_state.job_results = jobs
                    status.update(label=f"✅ {len(jobs)} jobs ready with full AI analysis!", state="complete")

    jobs = st.session_state.get("job_results", [])

    if not jobs:
        st.markdown("""
        <div style="text-align:center;padding:64px 0;color:#94a3b8;">
          <div style="font-size:2.5rem;margin-bottom:12px;">🎯</div>
          <div style="font-size:1rem;font-weight:600;color:#64748b;">Search for live LinkedIn jobs above</div>
          <div style="font-size:0.85rem;margin-top:6px;">AI summaries · Requirements · Salary · Applicants · Saved only when you apply</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div style='font-size:0.875rem;color:#64748b;margin-bottom:18px;'>"
            f"Showing <strong>{len(jobs)}</strong> live results · "
            f"<span style='color:#2563EB;font-weight:600;font-size:0.78rem;'>Session-only — saved only when you apply</span></div>",
            unsafe_allow_html=True)

        for job in jobs:
            jid            = str(job["id"])
            already_applied = jid in st.session_state.applied_jobs

            # Pills row — all info at a glance
            pills = []
            if already_applied:          pills.append('<span class="pill p-applied">✅ Applied</span>')
            if job.get("salary"):         pills.append(f'<span class="pill p-salary">💰 {job["salary"]}</span>')
            if job.get("job_type"):       pills.append(f'<span class="pill p-type">{job["job_type"]}</span>')
            if job.get("applicants"):     pills.append(f'<span class="pill p-views">👥 {job["applicants"]} applicants</span>')
            if job.get("posted"):         pills.append(f'<span class="pill p-posted">🕐 {job["posted"]}</span>')
            pills_html = "".join(pills)

            # Meta row
            meta = []
            if job.get("location"): meta.append(f'<span class="jcard-meta-item">📍 {job["location"]}</span>')
            meta_html = "".join(meta)

            # Content blocks — pre-built to avoid f-string rendering bug
            summary   = job.get("ai_summary","") or job.get("description","")[:300]
            ai_reqs   = job.get("ai_reqs","")   or job.get("requirements","")[:500]
            desc_full = job.get("description","")

            reqs_block = ""
            if ai_reqs:
                clean = ai_reqs.replace("•","<br>•").lstrip("<br>")
                reqs_block = (
                    '<div class="jdivider"></div>'
                    '<div class="jsec-lbl">Key Requirements &amp; Qualifications</div>'
                    f'<div class="jsec-req">{clean}</div>'
                )

            desc_block = ""
            if desc_full and desc_full.strip() != summary.strip():
                preview = desc_full[:700] + ("…" if len(desc_full) > 700 else "")
                desc_block = (
                    '<div class="jdivider"></div>'
                    '<div class="jsec-lbl">Full Description</div>'
                    f'<div class="jsec-txt" style="font-size:0.82rem;color:#64748b;">{preview}</div>'
                )

            # Footer buttons
            view_btn = ""
            if job.get("url") and job["url"] != "#":
                view_btn = f'<a href="{job["url"]}" target="_blank" class="jcard-view">🔗 View on LinkedIn</a>'

            if already_applied:
                apply_btn = '<button class="jcard-applied" disabled>✅ Applied</button>'
            else:
                apply_btn = f'<button class="jcard-apply" id="jbtn_{jid}">🚀 Apply Now</button>'

            # Render complete full-width card
            st.markdown(
                f'<div class="jcard">'
                f'<div class="jcard-body">'
                f'<div class="jcard-company">🏢 {job["company"]}</div>'
                f'<div class="jcard-title">{job["title"]}</div>'
                f'<div class="jcard-meta">{meta_html}</div>'
                f'<div class="pill-row">{pills_html}</div>'
                f'<div class="jdivider"></div>'
                f'<div class="jsec-lbl">AI Summary</div>'
                f'<div class="jsec-txt">{summary}</div>'
                f'{reqs_block}'
                f'{desc_block}'
                f'</div>'
                f'<div class="jcard-footer">'
                f'{view_btn}'
                f'{apply_btn}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True)

            # Streamlit Apply Now button — hidden, wired to HTML button via JS
            if not already_applied:
                if st.button(f"__apply_{jid}__", key=f"st_apply_{jid}"):
                    _save_applied(job)
                    st.session_state.applied_jobs[jid] = job
                    st.success(f"✅ Saved **{job['title']}** at **{job['company']}**!")
                    st.rerun()
                st.markdown(f"""
<style>
button[data-testid="baseButton-secondary"]:has(+ *) {{display:none;}}
div:has(> button[data-testid="baseButton-secondary"]) {{height:0!important;overflow:hidden!important;margin:0!important;padding:0!important;}}
</style>
<script>
(function(){{
  var b=document.getElementById('jbtn_{jid}');
  if(!b)return;
  b.onclick=function(){{
    var all=window.parent.document.querySelectorAll('[data-testid="stButton"] button');
    for(var i=0;i<all.length;i++){{
      if(all[i].innerText.trim()==='__apply_{jid}__'){{all[i].click();return;}}
    }}
  }};
}})();
</script>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VIEW B — APPLIED JOBS  (clean table + click → modal with ALL details)
# ══════════════════════════════════════════════════════════════════════════════
else:
    db_jobs = _load_applied()
    seen_urls = {j.get("source_url","") for j in db_jobs}
    session_extras = [
        {"company":j.get("company",""),"title":j.get("title",""),
         "location":j.get("location",""),"salary":j.get("salary",""),
         "job_type":j.get("job_type",""),"source_url":j.get("url",""),
         "applied_at":"Just now","description":j.get("description",""),
         "requirements":j.get("ai_reqs","") or j.get("requirements",""),
         "ai_summary":j.get("ai_summary",""),"applicants":j.get("applicants",""),
         "recruiter_name":"","recruiter_email":"","recruiter_title":""}
        for j in st.session_state.applied_jobs.values()
        if j.get("url","") not in seen_urls
    ]
    all_applied = db_jobs + session_extras

    if not all_applied:
        st.markdown("""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:16px;
                    padding:64px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
          <div style="font-size:2.8rem;margin-bottom:12px;">📭</div>
          <div style="font-size:1rem;font-weight:600;color:#0f172a;">No applied jobs yet</div>
          <div style="font-size:0.85rem;color:#64748b;margin-top:6px;">Browse jobs and click <strong>Apply Now</strong> to track them here.</div>
        </div>""", unsafe_allow_html=True)
    else:
        # Stat row
        c1,c2,c3,c4 = st.columns(4)
        for col,val,lbl,color in [
            (c1, len(all_applied),                                                    "Total Applied",   "#2563EB"),
            (c2, len({j.get("company","") for j in all_applied if j.get("company")}), "Companies",       "#7c3aed"),
            (c3, sum(1 for j in all_applied if j.get("salary","")),                   "With Salary",     "#16a34a"),
            (c4, "–",                                                                  "Interviews",      "#d97706"),
        ]:
            with col:
                st.markdown(f'<div class="stat-mini"><div class="stat-mini-val" style="color:{color};">{val}</div>'
                            f'<div class="stat-mini-lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # Clean table
        SCLS = {"Applied":"sb-Applied","Interview":"sb-Interview","Offer":"sb-Offer","Rejected":"sb-Rejected"}
        rows_html = ""
        for i, j in enumerate(all_applied):
            co    = j.get("company","—")
            title = j.get("title","—")
            dt    = str(j.get("applied_at",""))[:10] or "—"
            stage = j.get("stage","Applied") if "stage" in j else "Applied"
            has_r = bool(j.get("recruiter_name","") or j.get("recruiter_email",""))
            let   = co[0].upper() if co else "?"
            rows_html += f"""
<tr onclick="window._openMod({i})">
  <td><div class="co-cell"><div class="co-av">{let}</div><span class="co-nm">{co}</span></div></td>
  <td style="color:#475569;">{title}</td>
  <td style="color:#64748b;white-space:nowrap;">{dt}</td>
  <td><span class="sbadge {SCLS.get(stage,'sb-Applied')}">{stage}</span></td>
  <td style="text-align:center;">{'<span class="rdot-y">&#10003;</span>' if has_r else '<span class="rdot-n"></span>'}</td>
  <td><button class="vdet" onclick="event.stopPropagation();window._openMod({i})">View Details</button></td>
</tr>"""

        st.markdown(f"""
<div class="app-wrap">
  <table class="app-tbl">
    <thead><tr>
      <th>Company Name</th><th>Job Title</th><th>Applied Date</th>
      <th>Stage</th><th style="text-align:center;">Recruiter Found</th><th>Actions</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div style="padding:13px 20px;border-top:1px solid #f1f5f9;font-size:0.82rem;color:#64748b;">
    Showing 1 to {len(all_applied)} of {len(all_applied)} applications
  </div>
</div>""", unsafe_allow_html=True)

        # Modal data — all fields
        modal_data = []
        for j in all_applied:
            modal_data.append({
                "company":        j.get("company",""),
                "title":          j.get("title",""),
                "stage":          j.get("stage","Applied") if "stage" in j else "Applied",
                "applied_at":     str(j.get("applied_at",""))[:19].replace("T"," "),
                "location":       j.get("location",""),
                "salary":         j.get("salary",""),
                "job_type":       j.get("job_type",""),
                "applicants":     j.get("applicants",""),
                "ai_summary":     j.get("ai_summary","") or j.get("description","")[:500],
                "requirements":   j.get("requirements",""),
                "recruiter_name": j.get("recruiter_name",""),
                "recruiter_title":j.get("recruiter_title",""),
                "recruiter_email":j.get("recruiter_email",""),
                "source_url":     j.get("source_url", j.get("url","")),
            })

        st.markdown(f"""
<div id="app-modal" style="display:none;" class="mod-ov"
     onclick="if(event.target===this)window._closeMod()">
  <div class="mod-box">
    <div class="mod-hdr">
      <div>
        <div class="mod-co" id="m-co"></div>
        <div class="mod-ti" id="m-ti"></div>
      </div>
      <button class="mod-x" onclick="window._closeMod()">close</button>
    </div>
    <div class="mod-body">
      <div class="mod-pills" id="m-pills"></div>
      <div class="mod-grid"  id="m-grid"></div>
      <div id="m-sum-w" style="display:none;">
        <div class="mod-sl">AI Summary</div>
        <div class="mod-txt" id="m-sum"></div>
      </div>
      <div id="m-req-w" style="display:none;">
        <div class="mod-sl">Requirements &amp; Qualifications</div>
        <div class="mod-req" id="m-req"></div>
      </div>
      <div id="m-rec-w" style="display:none;">
        <div class="mod-sl">Recruiter</div>
        <div class="mod-rec-box" id="m-rec"></div>
      </div>
    </div>
    <div class="mod-foot">
      <a id="m-li" href="#" target="_blank" class="mod-li-btn" style="display:none;">
        &#128279; View on LinkedIn
      </a>
      <button class="mod-close" onclick="window._closeMod()">Close</button>
    </div>
  </div>
</div>

<script>
var _MD={json.dumps(modal_data)};
function _sc(s){{var m={{"Applied":"mp-Applied","Interview":"mp-Interview","Offer":"mp-Offer","Rejected":"mp-Rejected"}};return m[s]||"mp-Applied";}}
window._openMod=function(i){{
  var r=_MD[i]; if(!r)return;
  document.getElementById('m-co').textContent=r.company.toUpperCase();
  document.getElementById('m-ti').textContent=r.title;
  var p='<span class="mpill '+_sc(r.stage)+'">'+r.stage+'</span>';
  if(r.location)   p+='<span class="mpill mp-loc">&#128205; '+r.location+'</span>';
  if(r.salary)     p+='<span class="mpill mp-sal">&#128176; '+r.salary+'</span>';
  if(r.job_type)   p+='<span class="mpill mp-typ">'+r.job_type+'</span>';
  if(r.applicants) p+='<span class="mpill mp-app">&#128101; '+r.applicants+' applicants</span>';
  if(r.recruiter_name) p+='<span class="mpill mp-rec">&#128100; Recruiter Found</span>';
  document.getElementById('m-pills').innerHTML=p;
  var g='';
  g+='<div class="mod-cell"><div class="mod-cell-l">Applied Date</div><div class="mod-cell-v">'+(r.applied_at||'—')+'</div></div>';
  g+='<div class="mod-cell"><div class="mod-cell-l">Stage</div><div class="mod-cell-v">'+r.stage+'</div></div>';
  if(r.salary)     g+='<div class="mod-cell"><div class="mod-cell-l">Salary</div><div class="mod-cell-v">'+r.salary+'</div></div>';
  if(r.applicants) g+='<div class="mod-cell"><div class="mod-cell-l">Applicants</div><div class="mod-cell-v">'+r.applicants+'</div></div>';
  if(r.job_type)   g+='<div class="mod-cell"><div class="mod-cell-l">Job Type</div><div class="mod-cell-v">'+r.job_type+'</div></div>';
  if(r.source_url) g+='<div class="mod-cell" style="grid-column:1/-1"><div class="mod-cell-l">Source URL</div><div class="mod-cell-v" style="word-break:break-all;font-size:0.8rem;"><a href="'+r.source_url+'" target="_blank" style="color:#2563EB;text-decoration:none;">View Original Job &#8599;</a></div></div>';
  document.getElementById('m-grid').innerHTML=g;
  var sw=document.getElementById('m-sum-w');
  if(r.ai_summary){{document.getElementById('m-sum').textContent=r.ai_summary;sw.style.display='';}}
  else sw.style.display='none';
  var rw=document.getElementById('m-req-w');
  if(r.requirements){{
    document.getElementById('m-req').innerHTML=r.requirements.replace(/\n/g,'<br>').replace(/•/g,'<br>•').replace(/^<br>/,'');
    rw.style.display='';
  }} else rw.style.display='none';
  var rcw=document.getElementById('m-rec-w');
  if(r.recruiter_name||r.recruiter_email){{
    var rc='';
    if(r.recruiter_name)  rc+='<div style="font-weight:700;color:#0f172a;font-size:0.9rem;margin-bottom:3px;">&#128100; '+r.recruiter_name+'</div>';
    if(r.recruiter_title) rc+='<div style="color:#64748b;font-size:0.8rem;margin-bottom:5px;">'+r.recruiter_title+'</div>';
    if(r.recruiter_email) rc+='<div style="font-size:0.82rem;color:#334155;">&#9993; '+r.recruiter_email+'</div>';
    document.getElementById('m-rec').innerHTML=rc;
    rcw.style.display='';
  }} else rcw.style.display='none';
  var li=document.getElementById('m-li');
  if(r.source_url){{li.href=r.source_url;li.style.display='block';}}
  else li.style.display='none';
  document.getElementById('app-modal').style.display='flex';
  document.body.style.overflow='hidden';
}};
window._closeMod=function(){{
  document.getElementById('app-modal').style.display='none';
  document.body.style.overflow='';
}};
document.addEventListener('keydown',function(e){{if(e.key==='Escape')window._closeMod();}});
</script>
""", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.caption("CareerSync · LinkedIn jobs via Apify · AI insights by Groq llama-3.1-8b · ❤️")