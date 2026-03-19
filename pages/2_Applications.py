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
# GLOBAL CSS  —  LinkedIn-inspired, Sora font, clean card system
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── reset & base ── */
*,*::before,*::after{box-sizing:border-box;}
html,body,.stApp,[data-testid="stAppViewContainer"],
section.main,[data-testid="stMain"]{
  background:#f0f2f5 !important;
  font-family:'Sora',sans-serif !important;
  color:#0a0e1a !important;
}
.block-container{
  padding-top:1.6rem !important;
  padding-bottom:3rem !important;
  max-width:1100px !important;
}

/* ── sidebar ── */
[data-testid="stSidebar"]{
  background:#ffffff !important;
  border-right:1px solid #e0e4ea !important;
}
[data-testid="stSidebar"] .stButton>button{
  text-align:left !important; justify-content:flex-start !important;
  background:transparent !important; color:#4a5568 !important;
  border:none !important; box-shadow:none !important;
  font-size:0.875rem !important; font-weight:500 !important;
  padding:9px 12px !important; border-radius:8px !important;
  width:100% !important; font-family:'Sora',sans-serif !important;
}
[data-testid="stSidebar"] .stButton>button:hover{
  background:#f0f2f5 !important; color:#0a0e1a !important;
}
[data-testid="collapsedControl"]{display:none !important;}

/* ── page header ── */
.page-title{
  font-size:1.45rem; font-weight:700; letter-spacing:-0.4px;
  color:#0a0e1a; margin-bottom:4px;
}
.page-sub{font-size:0.82rem; color:#8a94a6; margin-bottom:18px;}

/* ── view toggle buttons ── */
div.stButton>button{
  background:#ffffff !important; color:#4a5568 !important;
  border:1.5px solid #c8cdd6 !important;
  border-radius:9999px !important;
  font-weight:600 !important; font-size:0.82rem !important;
  font-family:'Sora',sans-serif !important;
  padding:8px 20px !important;
  transition:all 0.15s !important;
}
div.stButton>button:hover{
  border-color:#0a66c2 !important; color:#0a66c2 !important;
  background:#ffffff !important;
}
div.stButton>button[kind="primary"]{
  background:#0a66c2 !important; color:#ffffff !important;
  border-color:#0a66c2 !important;
  box-shadow:0 2px 10px rgba(10,102,194,0.28) !important;
}
div.stButton>button[kind="primary"]:hover{
  background:#0958a8 !important;
}

/* ── search panel ── */
.search-panel{
  background:#ffffff;
  border:1px solid #e0e4ea;
  border-radius:18px;
  padding:18px 22px;
  margin-bottom:18px;
  box-shadow:0 1px 3px rgba(0,0,0,0.07);
}
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{
  background:#f8f9fa !important;
  border:1.5px solid #e0e4ea !important;
  border-radius:8px !important;
  font-family:'Sora',sans-serif !important;
  font-size:0.82rem !important;
}
div[data-testid="stTextInput"] input:focus{
  border-color:#0a66c2 !important;
  background:#ffffff !important;
}

/* ── search button ── */
div.stButton>button[kind="primary"].search-action{
  border-radius:8px !important;
  padding:10px 24px !important;
}

/* ── results meta ── */
.results-meta{
  font-size:0.8rem; color:#8a94a6; margin-bottom:16px;
  display:flex; align-items:center; justify-content:space-between;
}
.results-meta strong{color:#4a5568;}

/* ══════════════════════════════════════
   JOB CARD — LinkedIn-style full detail
   ══════════════════════════════════════ */
.jc{
  background:#ffffff;
  border:1px solid #e0e4ea;
  border-radius:18px;
  overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.07);
  margin-bottom:14px;
  transition:box-shadow 0.18s, transform 0.14s;
}
.jc:hover{
  box-shadow:0 6px 24px rgba(0,0,0,0.10);
  transform:translateY(-2px);
}

/* card top strip */
.jc-top{
  padding:16px 22px 14px;
  border-bottom:1px solid #f4f6f8;
}
.jc-company-row{
  display:flex; align-items:center; gap:12px; margin-bottom:10px;
}
.jc-logo{
  width:46px; height:46px; border-radius:11px;
  border:1px solid #e0e4ea; background:#f0f4ff;
  display:flex; align-items:center; justify-content:center;
  font-size:1.05rem; font-weight:700; color:#0a66c2;
  flex-shrink:0; font-family:'JetBrains Mono',monospace;
}
.jc-company-name{
  font-size:0.72rem; font-weight:700; color:#0a66c2;
  text-transform:uppercase; letter-spacing:0.8px;
}
.jc-title{
  font-size:1.08rem; font-weight:700; color:#0a0e1a;
  line-height:1.3; margin-bottom:9px; letter-spacing:-0.2px;
}
.pill-row{display:flex; flex-wrap:wrap; gap:6px;}
.pill{
  display:inline-flex; align-items:center; gap:4px;
  padding:3px 11px; border-radius:9999px;
  font-size:0.7rem; font-weight:600; white-space:nowrap;
}
.pill-loc  {background:#f0f4ff;color:#3b5bdb;border:1px solid #c5d2f9;}
.pill-type {background:#f8f9fa;color:#4a5568;border:1px solid #e0e4ea;}
.pill-posted{background:#e8f5ed;color:#1a6636;border:1px solid #a8d5b5;}
.pill-salary{background:#fdf3e3;color:#915907;border:1px solid #f5d9a0;}
.pill-applied{background:#e8f5ed;color:#057642;border:1px solid #a8d5b5;}
.pill-hot  {background:#fdecea;color:#cc1016;border:1px solid #f5b8ba;}

/* card body */
.jc-body{padding:15px 22px;}
.jc-section{margin-bottom:14px;}
.jc-section:last-child{margin-bottom:0;}
.section-label{
  font-size:0.65rem; font-weight:700; color:#8a94a6;
  text-transform:uppercase; letter-spacing:0.9px;
  margin-bottom:6px;
}
.summary-box{
  font-size:0.825rem; color:#4a5568; line-height:1.7;
  background:#f8f9fa; border-radius:8px;
  padding:11px 14px; border-left:3px solid #93c5fd;
}
.reqs-list{
  background:#f0fdf4; border-radius:8px;
  padding:11px 14px; border-left:3px solid #86efac;
}
.req-item{
  display:flex; align-items:flex-start; gap:8px;
  font-size:0.8rem; color:#4a5568; line-height:1.55; margin-bottom:5px;
}
.req-item:last-child{margin-bottom:0;}
.req-dot{
  width:6px; height:6px; border-radius:50%;
  background:#22c55e; flex-shrink:0; margin-top:5px;
}
.salary-badge{
  display:inline-flex; align-items:center; gap:7px;
  background:#fdf3e3; border:1px solid #f5d9a0;
  border-radius:8px; padding:8px 14px;
  font-size:0.875rem; font-weight:700; color:#915907;
}
.no-salary{font-size:0.78rem; color:#8a94a6; font-style:italic;}

/* stats bar */
.jc-stats{
  display:flex; flex-wrap:wrap; gap:18px;
  padding:11px 22px; background:#fafbfc;
  border-top:1px solid #f0f2f5;
}
.stat-item{
  display:flex; align-items:center; gap:6px;
  font-size:0.75rem; color:#8a94a6;
}
.stat-val{font-weight:600; color:#4a5568;}

/* ══ streamlit link button override ══ */
a.stLinkButton{
  background:#ffffff !important; color:#0a66c2 !important;
  border:1.5px solid #cce0f5 !important;
  border-radius:8px !important; font-weight:600 !important;
  font-size:0.8rem !important; font-family:'Sora',sans-serif !important;
  transition:all 0.15s !important; text-decoration:none !important;
}
a.stLinkButton:hover{background:#e8f0fb !important;}

/* ══════════════════════════
   APPLIED JOBS TABLE
   ══════════════════════════ */
.stat-mini{
  background:#ffffff; border:1px solid #e0e4ea;
  border-radius:14px; padding:18px 20px;
  text-align:center;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.stat-mini-val{font-size:1.9rem; font-weight:700; line-height:1;}
.stat-mini-lbl{
  font-size:0.67rem; color:#8a94a6; font-weight:700;
  text-transform:uppercase; letter-spacing:0.8px; margin-top:5px;
}
.at-wrap{
  background:#ffffff; border:1px solid #e0e4ea;
  border-radius:18px; overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.at-table{width:100%; border-collapse:collapse;}
.at-table th{
  background:#f8f9fa; color:#8a94a6;
  font-weight:700; font-size:0.67rem;
  text-transform:uppercase; letter-spacing:0.7px;
  padding:13px 17px; border-bottom:2px solid #e0e4ea;
  text-align:left; white-space:nowrap;
}
.at-table td{
  padding:15px 17px; border-bottom:1px solid #f4f6f8;
  vertical-align:top; color:#4a5568; font-size:0.8rem;
}
.at-table tr:last-child td{border-bottom:none;}
.at-table tr:hover td{background:#fafbfc;}
.at-co{display:flex; align-items:center; gap:10px;}
.at-logo{
  width:36px; height:36px; border-radius:9px;
  background:#e8f0fb; border:1px solid #cce0f5;
  display:flex; align-items:center; justify-content:center;
  font-size:0.82rem; font-weight:700; color:#0a66c2;
  flex-shrink:0; font-family:'JetBrains Mono',monospace;
}
.at-co-name{font-weight:700; color:#0a0e1a; font-size:0.85rem;}
.at-co-loc{font-size:0.7rem; color:#8a94a6; margin-top:2px;}
.at-role-title{font-weight:700; color:#0a0e1a; font-size:0.85rem; margin-bottom:4px;}
.at-badges{display:flex; gap:5px; flex-wrap:wrap; margin-top:4px;}
.at-desc{
  font-size:0.75rem; color:#4a5568; line-height:1.55; max-width:210px;
  display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;
}
.at-req{
  font-size:0.73rem; color:#334155; line-height:1.55; max-width:195px;
  background:#f0fdf4; border-radius:7px; padding:7px 10px;
  border-left:2px solid #86efac;
  display:-webkit-box; -webkit-line-clamp:4; -webkit-box-orient:vertical; overflow:hidden;
}
.at-salary{
  font-size:0.82rem; font-weight:700; color:#915907;
  background:#fdf3e3; border:1px solid #f5d9a0;
  border-radius:7px; padding:4px 9px; display:inline-block; white-space:nowrap;
}
.at-salary-na{font-size:0.75rem; color:#8a94a6; font-style:italic;}
.at-url{
  color:#0a66c2; font-size:0.75rem; font-weight:600;
  text-decoration:none; background:#e8f0fb; border:1px solid #cce0f5;
  border-radius:6px; padding:4px 9px;
  display:inline-flex; align-items:center; gap:4px;
  white-space:nowrap; transition:background 0.15s;
}
.at-url:hover{background:#cce0f5;}
.at-ts{
  font-size:0.72rem; color:#8a94a6; white-space:nowrap;
  background:#f8f9fa; border:1px solid #e0e4ea;
  border-radius:6px; padding:3px 7px; display:inline-block;
}

/* ── empty state ── */
.empty-state{
  text-align:center; padding:64px 20px;
  background:#ffffff; border:1px solid #e0e4ea;
  border-radius:18px; box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.empty-icon{font-size:2.8rem; margin-bottom:14px;}
.empty-title{font-size:1rem; font-weight:700; color:#0a0e1a;}
.empty-sub{font-size:0.82rem; color:#8a94a6; margin-top:6px;}

/* ── misc overrides ── */
.stAlert{border-radius:10px !important;}
div[data-testid="stStatusWidget"]{border-radius:12px !important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    name_disp  = user.get("name", "User")
    email_disp = user.get("email", "")
    avatar_let = name_disp[0].upper() if name_disp else "U"

    st.markdown(f"""
    <div style="padding:20px 16px 16px;display:flex;align-items:center;gap:10px;
                border-bottom:1px solid #f0f2f5;">
      <div style="width:34px;height:34px;background:#0a66c2;border-radius:9px;
                  display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        <span style="color:#fff;font-size:1rem;font-weight:700;font-family:'JetBrains Mono',monospace;">CS</span>
      </div>
      <span style="font-size:1.05rem;font-weight:700;color:#0a0e1a;
                   font-family:'Sora',sans-serif;letter-spacing:-0.3px;">CareerSync</span>
    </div>
    <div style="padding:10px 10px 8px;">
    """, unsafe_allow_html=True)

    nav_pages = [
        ("Dashboard",         "pages/1_Dashboard.py"),
        ("Applications",      "pages/2_Applications.py"),
        ("Cold Email",        "pages/3_Cold_Email.py"),
        ("Research Pipeline", "pages/4_Pipeline.py"),
        ("Settings",          "pages/5_Settings.py"),
    ]

    NAV_ICONS = {
        "Dashboard":         "▦",
        "Applications":      "✦",
        "Cold Email":        "✉",
        "Research Pipeline": "◈",
        "Settings":          "⚙",
    }

    for label, path in nav_pages:
        is_active = (label == "Applications")
        icon = NAV_ICONS.get(label, "•")
        if is_active:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                        border-radius:8px;background:#e8f0fb;color:#0a66c2;
                        font-weight:600;font-size:0.85rem;font-family:'Sora',sans-serif;
                        margin-bottom:2px;">
              <span style="font-size:1rem;">{icon}</span>{label}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;
                        border-radius:8px;color:#8a94a6;font-size:0.85rem;
                        font-weight:500;font-family:'Sora',sans-serif;margin-bottom:2px;">
              <span style="font-size:1rem;">{icon}</span>
            </div>""", unsafe_allow_html=True)
            if st.button(label, key=f"nav_{label}"):
                try: st.switch_page(path)
                except: st.info(f"{label} coming soon!")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:#f0f2f5;margin:8px 0;'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:8px 14px 14px;">
      <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;
                  border-radius:10px;background:#f8f9fa;border:1px solid #e0e4ea;">
        <div style="width:36px;height:36px;border-radius:50%;background:#e8f0fb;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;color:#0a66c2;font-size:0.875rem;flex-shrink:0;">
          {avatar_let}
        </div>
        <div style="min-width:0;">
          <div style="font-size:0.82rem;font-weight:600;color:#0a0e1a;
                      font-family:'Sora',sans-serif;overflow:hidden;
                      text-overflow:ellipsis;white-space:nowrap;">{name_disp}</div>
          <div style="font-size:0.7rem;color:#8a94a6;overflow:hidden;
                      text-overflow:ellipsis;white-space:nowrap;">{email_disp}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Logout", key="sidebar_logout", use_container_width=True):
        _logout()

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("app_view","browse"),("job_results",[]),("applied_jobs",{}),("ai_data",{})]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# CORE HELPERS  (unchanged logic from original)
# ══════════════════════════════════════════════════════════════════════════════
def _groq(prompt: str, max_tokens: int = 300) -> str:
    if not GROQ_KEY: return ""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model":"llama-3.1-8b-instant",
                  "messages":[{"role":"user","content":prompt}],
                  "max_tokens":max_tokens,"temperature":0.3},
            timeout=15)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def _google_job_clicks(title: str, company: str) -> str:
    if not GOOGLE_KEY or not GOOGLE_CSE:
        return ""
    try:
        query = f"{title} {company} job"
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": GOOGLE_KEY, "cx": GOOGLE_CSE, "q": query, "num": 1},
            timeout=8
        )
        data = r.json()
        total = data.get("searchInformation", {}).get("totalResults", "")
        if total and int(total) > 0:
            t = int(total)
            if t >= 1_000_000:
                return f"{t//1_000_000}M+ searches"
            elif t >= 1_000:
                return f"{t//1_000}K+ searches"
            else:
                return f"{t} searches"
    except Exception:
        pass
    return ""


def _ai_enrich(job: dict) -> dict:
    title   = job.get("title","")
    company = job.get("company","")
    desc    = job.get("description","")[:3000]
    reqs    = job.get("requirements","")[:1200]

    combined = f"Job Title: {title}\nCompany: {company}\n"
    if desc:  combined += f"\nFull Description:\n{desc}"
    if reqs:  combined += f"\n\nRequirements Section:\n{reqs}"
    if not desc and not reqs:
        combined += "\n(No description provided — generate a realistic summary based on the role title.)"

    prompt = f"""{combined}

Based on the above, return ONLY a JSON object with exactly these keys:
{{
  "summary": "2-3 sentence summary: what the role involves, what kind of team/company, and who would thrive here",
  "requirements": "exactly 5 key requirements as bullet points, each on its own line starting with •",
  "salary": "salary range as string if mentioned or inferrable from role level, else empty string",
  "job_type": "Full-time / Part-time / Contract / Internship / Freelance based on clues, else 'Full-time'",
  "engagement": "estimated number of applicants or interest level as short string, e.g. '200+ applicants' or 'High demand role', based on role seniority and company size"
}}
Return ONLY the JSON. No markdown fences. No explanation."""

    raw = _groq(prompt, max_tokens=500)
    try:
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        data = json.loads(raw)
        job["ai_summary"]    = data.get("summary", "")
        job["ai_reqs"]       = data.get("requirements", "")
        job["ai_engagement"] = data.get("engagement", "")
        if not job.get("salary"):
            job["salary"]    = data.get("salary", "")
        if not job.get("job_type") or job["job_type"] == "":
            job["job_type"]  = data.get("job_type", "Full-time")
    except Exception:
        job["ai_summary"]    = _groq(
            f"Summarise this job in 2 sentences:\nTitle:{title}\nCompany:{company}\n{desc[:600]}",
            max_tokens=150)
        job["ai_reqs"]       = reqs[:500] if reqs else (
            "• Experience in related field\n• Strong communication skills\n"
            "• Problem-solving ability\n• Team collaboration\n• Relevant degree or equivalent")
        job["ai_engagement"] = ""

    if not job.get("applicants") and not job.get("ai_engagement"):
        google_val = _google_job_clicks(title, company)
        if google_val:
            job["ai_engagement"] = google_val

    return job


def _fetch_apify(keyword, location, company, date_filter) -> list:
    if not APIFY_KEY: return []
    date_map = {
        "Any time":"","Last 24 hours":"r86400",
        "Past week":"r604800","Past month":"r2592000",
    }
    search_kw = keyword.strip()
    if company.strip(): search_kw = f"{company.strip()} {search_kw}".strip()
    input_data = {
        "title": search_kw,
        "location": location.strip() or "United States",
        "rows": 25, "scrapeCompany": True,
        "proxy": {"useApifyProxy": True},
    }
    if date_map.get(date_filter):
        input_data["publishedAt"] = date_map[date_filter]
    try:
        run_url = "https://api.apify.com/v2/acts/bebity~linkedin-jobs-scraper/run-sync-get-dataset-items"
        resp = requests.post(
            run_url,
            params={"token": APIFY_KEY, "timeout": 90, "memory": 512},
            json=input_data, timeout=100
        )
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list): return items
    except Exception:
        pass
    return []


def _fetch_linkedin_guest(keyword, location, company, date_filter) -> list:
    from bs4 import BeautifulSoup
    date_map = {"Any time":"","Last 24 hours":"r86400","Past week":"r604800","Past month":"r2592000"}
    f_tpr = date_map.get(date_filter, "")
    search_kw = keyword.strip()
    if company.strip(): search_kw = f"{search_kw} {company.strip()}".strip()
    if not search_kw: return []

    SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    hdrs = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9",
    }
    params = {"keywords": search_kw, "location": location.strip(), "start": 0, "count": 25}
    if f_tpr: params["f_TPR"] = f_tpr
    try:
        resp = requests.get(SEARCH, params=params, headers=hdrs, timeout=20)
        if resp.status_code != 200: return []
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.find_all("li")
    jobs = []
    for card in cards[:20]:
        try:
            entity = card.find("div", {"data-entity-urn": True})
            job_id = ""
            if entity:
                job_id = entity.get("data-entity-urn","").split(":")[-1]
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
            job_url = (link_a["href"].split("?")[0] if link_a
                       else f"https://www.linkedin.com/jobs/view/{job_id}")
            j = {
                "id": job_id, "title": title_tag.get_text(strip=True) if title_tag else "Unknown Role",
                "companyName": company_tag.get_text(strip=True) if company_tag else "Unknown Company",
                "location": loc_tag.get_text(strip=True) if loc_tag else "",
                "publishedAt": time_tag.get("datetime","") if time_tag else "",
                "jobUrl": job_url,
                "description":"","salary":"","applicantsCount":"","requirements":"",
            }
            jobs.append(j)
        except Exception:
            continue

    for job in jobs[:15]:
        try:
            det = requests.get(DETAIL.format(job_id=job["id"]), headers=hdrs, timeout=10)
            if det.status_code == 200:
                ds = BeautifulSoup(det.text, "html.parser")
                desc_tag = (ds.find("div", class_=re.compile("description__text")) or
                            ds.find("div", class_=re.compile("show-more-less-html")))
                if desc_tag:
                    job["description"] = desc_tag.get_text(separator=" ", strip=True)[:3500]
                sal_tag = ds.find("span", class_=re.compile("compensation"))
                if sal_tag: job["salary"] = sal_tag.get_text(strip=True)
                app_tag = ds.find("span", class_=re.compile("num-applicants|applicant"))
                if app_tag: job["applicantsCount"] = app_tag.get_text(strip=True)
                views_tag = ds.find("span", class_=re.compile("views|impression"))
                if views_tag: job["views"] = views_tag.get_text(strip=True)
        except Exception:
            pass
    return jobs


def _normalise(raw: dict) -> dict:
    desc = (raw.get("description") or raw.get("descriptionText") or raw.get("jobDescription") or "")
    company = (raw.get("companyName") or raw.get("company") or "Unknown Company")
    url = (raw.get("jobUrl") or raw.get("url") or raw.get("applyUrl") or "#")
    job_id = str(raw.get("id") or raw.get("jobId") or
                 abs(hash(url + str(raw.get("title","")))))
    applicants = str(raw.get("applicantsCount") or raw.get("numApplicants") or "")
    views = str(raw.get("views") or raw.get("impressions") or raw.get("clicks") or "")
    return {
        "id": job_id, "title": raw.get("title","Unknown Role"),
        "company": company, "location": raw.get("location",""),
        "salary": (raw.get("salary") or raw.get("salaryRange") or ""),
        "description": desc,
        "requirements": (raw.get("requirements") or raw.get("jobRequirements") or ""),
        "url": url,
        "posted": (raw.get("publishedAt") or raw.get("postedAt") or raw.get("posted_date") or ""),
        "applicants": applicants, "views": views,
        "job_type": (raw.get("contractType") or raw.get("employmentType") or ""),
        "company_url": raw.get("companyUrl",""), "logo_url": raw.get("companyLogo",""),
        "ai_summary":"", "ai_reqs":"", "ai_engagement":"",
    }


def fetch_and_enrich(keyword, location, company, date_filter) -> tuple:
    raw = []
    source = ""
    if APIFY_KEY:
        raw = _fetch_apify(keyword, location, company, date_filter)
        if raw: source = "Apify LinkedIn Scraper"
    if not raw:
        try:
            raw = _fetch_linkedin_guest(keyword, location, company, date_filter)
            if raw: source = "LinkedIn Public API"
        except Exception as e:
            return [], f"Could not fetch jobs: {e}"
    if not raw:
        return [], "No jobs found. Try a broader keyword or different location."
    jobs = [_normalise(r) for r in raw[:20]]
    for i, job in enumerate(jobs):
        jobs[i] = _ai_enrich(job)
    return jobs, ""


def _save_applied(job: dict) -> bool:
    if not _sb: return False
    try:
        _sb.table("applied_jobs").insert({
            "user_id":      user_id,
            "company":      job.get("company",""),
            "title":        job.get("title",""),
            "description":  job.get("description","")[:2000],
            "requirements": job.get("ai_reqs") or job.get("requirements",""),
            "salary":       job.get("salary",""),
            "job_type":     job.get("job_type",""),
            "location":     job.get("location",""),
            "source_url":   job.get("url",""),
            "applicants":   job.get("applicants",""),
            "views":        job.get("views",""),
            "ai_summary":   job.get("ai_summary",""),
            "ai_engagement":job.get("ai_engagement",""),
        }).execute()
        return True
    except Exception:
        return False


def _load_applied() -> list:
    if not _sb: return []
    try:
        res = (_sb.table("applied_jobs")
               .select("*")
               .eq("user_id", user_id)
               .order("applied_at", desc=True)
               .execute())
        return res.data or []
    except Exception:
        return []


def _parse_reqs(reqs_str: str) -> list:
    if not reqs_str: return []
    items = []
    for line in reqs_str.replace("• ", "\n• ").split("\n"):
        line = line.strip().lstrip("•").lstrip("-").lstrip("*").strip()
        if line and len(line) > 5:
            items.append(line)
    return items[:6]


def _engagement(job: dict) -> str:
    if job.get("applicants") and job["applicants"] not in ("", "0"):
        return f"👥 {job['applicants']}"
    if job.get("views") and job["views"] not in ("", "0"):
        return f"👁 {job['views']} views"
    if job.get("ai_engagement"):
        return f"📊 {job['ai_engagement']}"
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='page-title'>Job Applications</div>"
    "<div class='page-sub'>"
    "Live LinkedIn jobs &nbsp;·&nbsp; AI-powered summaries &amp; requirements "
    "&nbsp;·&nbsp; Full engagement metrics &nbsp;·&nbsp; Track every application"
    "</div>",
    unsafe_allow_html=True
)

# ── View Toggle ──────────────────────────────────────────────────────────────
applied_count = len(st.session_state.applied_jobs)
c_browse, c_applied, _ = st.columns([1.2, 1.4, 6])
with c_browse:
    if st.button(
        "🔍  Browse Jobs",
        type="primary" if st.session_state.app_view == "browse" else "secondary",
        use_container_width=True, key="btn_browse"
    ):
        st.session_state.app_view = "browse"; st.rerun()
with c_applied:
    label = f"📋  Applied Jobs ({applied_count})" if applied_count else "📋  Applied Jobs"
    if st.button(
        label,
        type="primary" if st.session_state.app_view == "applied" else "secondary",
        use_container_width=True, key="btn_applied"
    ):
        st.session_state.app_view = "applied"; st.rerun()

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  VIEW A: BROWSE JOBS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app_view == "browse":

    # ── Search Panel ─────────────────────────────────────────────────────────
    st.markdown('<div class="search-panel">', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([3, 2, 2, 2])
    with f1: kw         = st.text_input("Role", placeholder="Job title, role, or keyword…",  key="jb_kw",   label_visibility="collapsed")
    with f2: company_q  = st.text_input("Company", placeholder="Company name…",               key="jb_co",   label_visibility="collapsed")
    with f3: location_q = st.text_input("Location", placeholder="Location or Remote…",        key="jb_loc",  label_visibility="collapsed")
    with f4: date_f     = st.selectbox("Posted", ["Any time","Last 24 hours","Past week","Past month"], key="jb_date", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    _, btn_col, _ = st.columns([4, 2, 4])
    with btn_col:
        search_clicked = st.button("🚀  Search Jobs", type="primary",
                                   use_container_width=True, key="jb_search")

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
                    st.write("🤖 AI extracted summaries, requirements, salary & engagement data")
                    st.session_state.job_results = jobs
                    status.update(label=f"✅ {len(jobs)} jobs ready with full AI analysis!", state="complete")

    # ── Results ──────────────────────────────────────────────────────────────
    jobs = st.session_state.get("job_results", [])

    if not jobs:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">🎯</div>
          <div class="empty-title">Search for jobs above</div>
          <div class="empty-sub">Live LinkedIn results · AI summaries · Requirements · Salary · Engagement metrics</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div class='results-meta'>"
            f"Showing <strong>{len(jobs)}</strong> live results with full AI analysis &nbsp;·&nbsp; "
            f"<span style='color:#0a66c2;font-weight:600;font-size:0.78rem;'>Click Apply Now to track</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        for job in jobs:
            jid = str(job["id"])
            already_applied = jid in st.session_state.applied_jobs
            letter = (job["company"][0].upper() if job.get("company") else "?")

            # Pills
            pills = []
            if already_applied:
                pills.append('<span class="pill pill-applied">✓ Applied</span>')
            if job.get("location"):
                pills.append(f'<span class="pill pill-loc">📍 {job["location"]}</span>')
            if job.get("job_type"):
                pills.append(f'<span class="pill pill-type">{job["job_type"]}</span>')
            if job.get("posted"):
                pills.append(f'<span class="pill pill-posted">🕐 {str(job["posted"])[:10]}</span>')
            pills_html = "".join(pills)

            # Summary
            summary = job.get("ai_summary","") or job.get("description","")[:300] or "No description available."

            # Requirements
            req_items = _parse_reqs(job.get("ai_reqs","") or job.get("requirements",""))
            if req_items:
                reqs_inner = "".join(
                    f'<div class="req-item"><div class="req-dot"></div><div>{r}</div></div>'
                    for r in req_items
                )
                reqs_block = (
                    '<div class="jc-section">'
                    '<div class="section-label">Requirements &amp; Qualifications</div>'
                    f'<div class="reqs-list">{reqs_inner}</div>'
                    '</div>'
                )
            else:
                reqs_block = ""

            # Salary
            salary_val = job.get("salary","")
            if salary_val:
                salary_block = (
                    '<div class="jc-section">'
                    '<div class="section-label">Salary</div>'
                    f'<div class="salary-badge">💰 {salary_val}</div>'
                    '</div>'
                )
            else:
                salary_block = (
                    '<div class="jc-section">'
                    '<div class="section-label">Salary</div>'
                    '<span class="no-salary">Not specified — may be discussed at interview</span>'
                    '</div>'
                )

            # Stats bar
            stats_items = []
            eng = _engagement(job)
            if eng:
                stats_items.append(f'<div class="stat-item">📊 <span class="stat-val">{eng}</span></div>')
            if job.get("posted"):
                stats_items.append(f'<div class="stat-item">🕐 <span class="stat-val">Posted {str(job["posted"])[:10]}</span></div>')
            if job.get("job_type"):
                stats_items.append(f'<div class="stat-item">💼 <span class="stat-val">{job["job_type"]}</span></div>')
            stats_html = "".join(stats_items)

            # Full card
            card_html = (
                '<div class="jc">'
                  '<div class="jc-top">'
                    '<div class="jc-company-row">'
                      f'<div class="jc-logo">{letter}</div>'
                      '<div>'
                        f'<div class="jc-company-name">{job["company"]}</div>'
                      '</div>'
                    '</div>'
                    f'<div class="jc-title">{job["title"]}</div>'
                    f'<div class="pill-row">{pills_html}</div>'
                  '</div>'
                  '<div class="jc-body">'
                    '<div class="jc-section">'
                      '<div class="section-label">✦ AI Summary</div>'
                      f'<div class="summary-box">{summary}</div>'
                    '</div>'
                    f'{reqs_block}'
                    f'{salary_block}'
                  '</div>'
                  f'<div class="jc-stats">{stats_html}</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

            # Action buttons (native Streamlit — below each card)
            a1, a2, a3 = st.columns([2, 2, 6])
            with a1:
                if job.get("url") and job["url"] != "#":
                    st.link_button("🔗 View on LinkedIn", job["url"], use_container_width=True)
            with a2:
                if already_applied:
                    st.button("✓ Applied", key=f"apply_{jid}", disabled=True,
                              use_container_width=True)
                else:
                    if st.button("🚀 Apply Now", key=f"apply_{jid}",
                                 type="primary", use_container_width=True):
                        _save_applied(job)
                        st.session_state.applied_jobs[jid] = job
                        st.success(f"✅ Saved **{job['title']}** at **{job['company']}**!")
                        st.rerun()

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  VIEW B: APPLIED JOBS
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;color:#0a0e1a;"
        "margin-bottom:16px;font-family:\"Sora\",sans-serif;'>"
        "📋 Your Applied Jobs</div>",
        unsafe_allow_html=True
    )

    db_jobs = _load_applied()

    # Merge DB + session
    seen_urls = {j.get("source_url","") for j in db_jobs}
    session_extras = [
        {
            "company":      j.get("company",""),
            "title":        j.get("title",""),
            "location":     j.get("location",""),
            "salary":       j.get("salary",""),
            "job_type":     j.get("job_type",""),
            "source_url":   j.get("url",""),
            "applied_at":   "Just now",
            "description":  j.get("ai_summary","") or j.get("description",""),
            "requirements": j.get("ai_reqs","") or j.get("requirements",""),
            "ai_summary":   j.get("ai_summary",""),
            "applicants":   j.get("applicants",""),
            "views":        j.get("views",""),
            "ai_engagement":j.get("ai_engagement",""),
        }
        for j in st.session_state.applied_jobs.values()
        if j.get("url","") not in seen_urls
    ]
    all_applied = db_jobs + session_extras

    if not all_applied:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-title">No applied jobs yet</div>
          <div class="empty-sub">Browse jobs and click <strong>Apply Now</strong> to track them here.</div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── Stats row ─────────────────────────────────────────────────────────
        total_apps  = len(all_applied)
        companies   = len({j.get("company","") for j in all_applied if j.get("company")})
        with_salary = sum(1 for j in all_applied if j.get("salary"))
        with_reqs   = sum(1 for j in all_applied if j.get("requirements") or j.get("ai_reqs",""))

        c1, c2, c3, c4 = st.columns(4)
        for col, val, lbl, color in [
            (c1, total_apps,  "Total Applied",     "#0a66c2"),
            (c2, companies,   "Companies",          "#6b21a8"),
            (c3, with_salary, "With Salary Info",   "#057642"),
            (c4, with_reqs,   "With Requirements",  "#915907"),
        ]:
            with col:
                st.markdown(f"""
                <div class="stat-mini">
                  <div class="stat-mini-val" style="color:{color};">{val}</div>
                  <div class="stat-mini-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # ── Applied jobs table ────────────────────────────────────────────────
        rows_html = ""
        for j in all_applied:
            company     = j.get("company","—")
            title       = j.get("title","—")
            location    = j.get("location","")
            salary      = j.get("salary","")
            job_type    = j.get("job_type","")
            source_url  = j.get("source_url") or j.get("url","")
            applied_at  = j.get("applied_at","")
            description = j.get("ai_summary") or j.get("description","")
            requirements= j.get("requirements") or j.get("ai_reqs","")
            applicants  = j.get("applicants","")
            views_val   = j.get("views","") or j.get("ai_engagement","")

            date_str = str(applied_at)[:19].replace("T"," ") if applied_at else "—"
            letter   = company[0].upper() if company else "?"

            # Salary cell
            salary_html = (
                f'<span class="at-salary">💰 {salary}</span>'
                if salary else
                '<span class="at-salary-na">Not specified</span>'
            )

            # Badges
            badges = ""
            if job_type:
                badges += f'<span class="pill pill-type" style="font-size:0.67rem;">{job_type}</span>'
            if applicants and applicants not in ("","0"):
                badges += f'<span class="pill pill-hot" style="font-size:0.67rem;">👥 {applicants}</span>'
            elif views_val:
                badges += f'<span class="pill pill-loc" style="font-size:0.67rem;">📊 {views_val}</span>'

            # Link
            link_html = (
                f'<a class="at-url" href="{source_url}" target="_blank">🔗 View Job</a>'
                if source_url and source_url != "#"
                else '<span style="color:#8a94a6;font-size:0.78rem;">—</span>'
            )

            req_preview = requirements[:350] + "…" if len(requirements) > 350 else requirements
            req_html = (
                f'<div class="at-req">{req_preview}</div>'
                if req_preview.strip()
                else '<span style="color:#8a94a6;font-size:0.78rem;">—</span>'
            )

            desc_preview = description[:250] + "…" if len(description) > 250 else description
            desc_html = (
                f'<div class="at-desc">{desc_preview}</div>'
                if desc_preview.strip()
                else '<span style="color:#8a94a6;font-size:0.78rem;">—</span>'
            )

            rows_html += f"""
            <tr>
              <td>
                <div class="at-co">
                  <div class="at-logo">{letter}</div>
                  <div>
                    <div class="at-co-name">{company}</div>
                    <div class="at-co-loc">{location or "Location not specified"}</div>
                  </div>
                </div>
              </td>
              <td>
                <div class="at-role-title">{title}</div>
                <div class="at-badges">{badges}</div>
              </td>
              <td>{desc_html}</td>
              <td>{req_html}</td>
              <td>{salary_html}</td>
              <td>{link_html}</td>
              <td><span class="at-ts">{date_str}</span></td>
            </tr>"""

        st.markdown(f"""
        <div class="at-wrap">
          <table class="at-table">
            <thead><tr>
              <th>Company</th>
              <th>Role</th>
              <th>AI Description</th>
              <th>Requirements</th>
              <th>Salary</th>
              <th>Source URL</th>
              <th>Applied Date</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.caption("CareerSync · LinkedIn jobs via Apify · AI insights by Groq llama-3.1-8b · Click tracking via Google CSE · ❤️")