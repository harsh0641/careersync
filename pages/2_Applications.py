"""
pages/2_Applications.py — CareerSync Job Application Portal
Data: Apify LinkedIn Jobs Scraper (richest data) + Groq AI extraction
Fields: company, title, location, salary, description, requirements,
        applicants/views, posted date, source URL
Applied Jobs: saved to Supabase with all fields + timestamp
"""

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

# Supabase client
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
    [data-testid="stSidebar"] .stButton>button:hover{
      background:#f8fafc!important;color:#0f172a!important;}
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
              {label}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
                        color:#64748b;font-size:0.9rem;font-weight:500;font-family:'DM Sans',sans-serif;">
              <span style="font-family:'Material Symbols Outlined';font-size:20px;
                           font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;">{icon}</span>
              {label}
            </div>""", unsafe_allow_html=True)
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
    </div>
    """, unsafe_allow_html=True)

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

/* ── JOB CARD ── */
.job-card{
  background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:24px 28px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
  transition:box-shadow 0.15s,transform 0.1s;
}
.job-card:hover{box-shadow:0 6px 20px rgba(0,0,0,0.08);transform:translateY(-1px);}
.job-card-company{
  font-size:0.72rem;font-weight:700;color:#2563EB;
  text-transform:uppercase;letter-spacing:0.8px;margin-bottom:5px;
  display:flex;align-items:center;gap:6px;
}
.job-card-title{font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:8px;line-height:1.3;}
.job-card-meta{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:12px;}
.job-meta-item{display:flex;align-items:center;gap:5px;font-size:0.8rem;color:#64748b;}
.job-meta-item .mi{font-family:'Material Symbols Outlined';font-size:15px;
  font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;line-height:1;color:#94a3b8;}

/* ── PILLS / BADGES ── */
.pill-row{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:14px;}
.pill{display:inline-flex;align-items:center;gap:4px;padding:4px 11px;border-radius:9999px;
  font-size:0.72rem;font-weight:700;white-space:nowrap;}
.pill-applied  {background:#dcfce7;color:#15803d;}
.pill-salary   {background:#fef9c3;color:#854d0e;}
.pill-views    {background:#ede9fe;color:#6d28d9;}
.pill-posted   {background:#f0f9ff;color:#0369a1;}
.pill-type     {background:#f1f5f9;color:#475569;}

/* ── SECTION LABELS ── */
.section-label{
  font-size:0.72rem;font-weight:700;color:#94a3b8;
  text-transform:uppercase;letter-spacing:0.8px;
  margin:14px 0 5px;
}
.section-text{font-size:0.875rem;color:#475569;line-height:1.7;}
.section-req{
  font-size:0.82rem;color:#334155;line-height:1.7;
  padding:12px 16px;background:#f8fafc;border-radius:10px;
  border-left:3px solid #2563EB;margin-top:4px;
}

/* ── DIVIDER in card ── */
.card-divider{height:1px;background:#f1f5f9;margin:14px 0;}

/* ── ACTION BUTTONS ── */
.btn-apply{
  width:100%;padding:11px;border-radius:10px;
  background:#2563EB;color:#fff;font-size:0.9rem;font-weight:700;
  border:none;cursor:pointer;font-family:'DM Sans',sans-serif;
  transition:background 0.15s;box-shadow:0 2px 8px rgba(37,99,235,0.25);
}
.btn-apply:hover{background:#1d4ed8;}
.btn-applied{
  width:100%;padding:11px;border-radius:10px;
  background:#dcfce7;color:#15803d;font-size:0.9rem;font-weight:700;
  border:1px solid #bbf7d0;cursor:default;font-family:'DM Sans',sans-serif;
}
.btn-view{
  width:100%;padding:10px;border-radius:10px;
  background:#fff;color:#2563EB;font-size:0.875rem;font-weight:700;
  border:1px solid #bfdbfe;cursor:pointer;font-family:'DM Sans',sans-serif;
  transition:background 0.15s;text-align:center;text-decoration:none!important;
  display:block;
}
.btn-view:hover{background:#eff6ff;}

/* ── SEARCH PANEL ── */
.search-panel{
  background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  padding:24px;margin-bottom:22px;box-shadow:0 1px 4px rgba(0,0,0,0.04);
}
.search-panel-title{
  font-size:0.7rem;font-weight:700;color:#0f172a;
  text-transform:uppercase;letter-spacing:0.8px;margin-bottom:14px;
}

/* ── APPLIED TABLE ── */
.cs-wrap{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
  overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.04);}
.cs-table{width:100%;border-collapse:collapse;}
.cs-table th{background:#f8fafc;color:#64748b;font-weight:700;font-size:0.7rem;
  text-transform:uppercase;letter-spacing:0.6px;padding:13px 20px;
  border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap;}
.cs-table td{padding:15px 20px;border-bottom:1px solid #f1f5f9;
  vertical-align:top;color:#334155;font-size:0.83rem;}
.cs-table tr:last-child td{border-bottom:none;}
.cs-table tr:hover td{background:#f8fafc;}
.co-logo{width:34px;height:34px;border-radius:9px;background:#f1f5f9;
  display:flex;align-items:center;justify-content:center;
  font-size:0.8rem;font-weight:700;color:#475569;flex-shrink:0;}
.td-company{display:flex;align-items:center;gap:10px;}
.td-desc{font-size:0.78rem;color:#64748b;line-height:1.5;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.td-req{font-size:0.75rem;color:#475569;line-height:1.5;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;}

/* ── STAT CARDS ── */
.stat-mini{background:#fff;border:1px solid #e2e8f0;border-radius:14px;
  padding:18px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.stat-mini-val{font-size:1.8rem;font-weight:700;line-height:1;}
.stat-mini-lbl{font-size:0.7rem;color:#64748b;font-weight:700;
  text-transform:uppercase;letter-spacing:0.7px;margin-top:4px;}

/* ── EMPTY STATE ── */
.empty-state{text-align:center;padding:64px 0;color:#94a3b8;}
.empty-state-icon{font-size:2.8rem;margin-bottom:12px;}
.empty-state-title{font-size:1rem;font-weight:600;color:#64748b;}
.empty-state-sub{font-size:0.85rem;margin-top:6px;}

/* ── STREAMLIT OVERRIDES ── */
div.stButton>button{
  background:#fff!important;color:#475569!important;border:1px solid #e2e8f0!important;
  border-radius:8px!important;font-weight:600!important;font-size:0.85rem!important;
  font-family:'DM Sans',sans-serif!important;padding:8px 14px!important;transition:all 0.15s!important;}
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
# ── CORE HELPERS ──────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _groq(prompt: str, max_tokens: int = 300) -> str:
    """Call Groq llama-3.1-8b-instant."""
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


def _ai_enrich(job: dict) -> dict:
    """
    Use Groq to extract / enhance:
    - 2-sentence summary
    - requirements bullet list
    - salary (if parseable from description)
    Returns updated job dict.
    """
    title = job.get("title","")
    desc  = job.get("description","")[:2500]
    reqs  = job.get("requirements","")[:1000]

    if not desc and not reqs:
        job["ai_summary"]  = "No description available for this listing."
        job["ai_reqs"]     = ""
        return job

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
        # strip markdown fences
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
        data = json.loads(raw)
        job["ai_summary"]  = data.get("summary", "")
        job["ai_reqs"]     = data.get("requirements", "")
        if not job.get("salary"):
            job["salary"]  = data.get("salary", "")
        if not job.get("job_type"):
            job["job_type"] = data.get("job_type", "")
    except Exception:
        # fallback: plain summarise
        job["ai_summary"] = _groq(
            f"Summarise this job in 2 sentences:\nTitle: {title}\n{desc[:800]}",
            max_tokens=120)
        job["ai_reqs"] = reqs[:400] if reqs else ""
    return job


# ── SOURCE 1: Apify LinkedIn Jobs Scraper (richest data) ─────────────────────
def _fetch_apify(keyword: str, location: str, company: str,
                 date_filter: str) -> list[dict]:
    """
    Uses Apify bebity/linkedin-jobs-scraper actor.
    Returns raw list of job dicts.
    """
    if not APIFY_KEY:
        return []

    date_map = {
        "Any time":      "",
        "Last 24 hours": "r86400",
        "Past week":     "r604800",
        "Past month":    "r2592000",
    }

    search_kw = keyword.strip()
    if company.strip(): search_kw = f"{company.strip()} {search_kw}".strip()

    input_data = {
        "title":        search_kw,
        "location":     location.strip() or "United States",
        "rows":         20,
        "scrapeCompany":True,
        "proxy":        {"useApifyProxy": True},
    }
    if date_map.get(date_filter):
        input_data["publishedAt"] = date_map[date_filter]

    try:
        # Run actor synchronously and get dataset
        run_url = "https://api.apify.com/v2/acts/bebity~linkedin-jobs-scraper/run-sync-get-dataset-items"
        resp = requests.post(
            run_url,
            params={"token": APIFY_KEY, "timeout": 90, "memory": 512},
            json=input_data,
            timeout=100
        )
        if resp.status_code == 200:
            items = resp.json()
            if isinstance(items, list): return items
    except Exception:
        pass
    return []


# ── SOURCE 2: LinkedIn Guest API (free fallback) ─────────────────────────────
def _fetch_linkedin_guest(keyword: str, location: str, company: str,
                          date_filter: str) -> list[dict]:
    """Free LinkedIn guest endpoint — no API key needed."""
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
    params = {"keywords": search_kw, "location": location.strip(),
              "start": 0, "count": 25}
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
                "id":          job_id,
                "title":       title_tag.get_text(strip=True) if title_tag else "Unknown Role",
                "companyName": company_tag.get_text(strip=True) if company_tag else "Unknown Company",
                "location":    loc_tag.get_text(strip=True) if loc_tag else "",
                "publishedAt": time_tag.get("datetime","") if time_tag else "",
                "jobUrl":      job_url,
                "description": "", "salary": "", "applicantsCount": "", "requirements": "",
            }
            jobs.append(j)
        except Exception:
            continue

    # Fetch descriptions for top 12
    for job in jobs[:12]:
        try:
            det = requests.get(DETAIL.format(job_id=job["id"]), headers=hdrs, timeout=10)
            if det.status_code == 200:
                ds = BeautifulSoup(det.text, "html.parser")
                desc_tag = (ds.find("div", class_=re.compile("description__text")) or
                            ds.find("div", class_=re.compile("show-more-less-html")))
                if desc_tag:
                    job["description"] = desc_tag.get_text(separator=" ", strip=True)[:3000]
                sal_tag = ds.find("span", class_=re.compile("compensation"))
                if sal_tag: job["salary"] = sal_tag.get_text(strip=True)
                app_tag = ds.find("span", class_=re.compile("num-applicants|applicant"))
                if app_tag: job["applicantsCount"] = app_tag.get_text(strip=True)
        except Exception:
            pass

    return jobs


# ── NORMALISE raw → standard dict ────────────────────────────────────────────
def _normalise(raw: dict) -> dict:
    desc = (raw.get("description") or raw.get("descriptionText") or
            raw.get("jobDescription") or "")
    company = (raw.get("companyName") or raw.get("company") or "Unknown Company")
    url = (raw.get("jobUrl") or raw.get("url") or raw.get("applyUrl") or "#")
    job_id = str(raw.get("id") or raw.get("jobId") or
                 abs(hash(url + str(raw.get("title","")))))
    applicants = str(raw.get("applicantsCount") or raw.get("numApplicants") or
                     raw.get("views") or "")
    return {
        "id":           job_id,
        "title":        raw.get("title","Unknown Role"),
        "company":      company,
        "location":     raw.get("location",""),
        "salary":       (raw.get("salary") or raw.get("salaryRange") or ""),
        "description":  desc,
        "requirements": (raw.get("requirements") or raw.get("jobRequirements") or ""),
        "url":          url,
        "posted":       (raw.get("publishedAt") or raw.get("postedAt") or raw.get("posted_date") or ""),
        "applicants":   applicants,
        "job_type":     (raw.get("contractType") or raw.get("employmentType") or ""),
        "company_url":  raw.get("companyUrl",""),
        "logo_url":     raw.get("companyLogo",""),
        "ai_summary":   "",
        "ai_reqs":      "",
    }


# ── FETCH + ENRICH pipeline ───────────────────────────────────────────────────
def fetch_and_enrich(keyword, location, company, date_filter) -> tuple[list, str]:
    """
    1. Try Apify (richest data)
    2. Fallback to LinkedIn guest scraper
    3. AI-enrich each job
    """
    raw = []
    source = ""

    # Try Apify first
    if APIFY_KEY:
        raw = _fetch_apify(keyword, location, company, date_filter)
        if raw: source = "Apify LinkedIn Scraper"

    # Fallback
    if not raw:
        try:
            raw = _fetch_linkedin_guest(keyword, location, company, date_filter)
            if raw: source = "LinkedIn Public API"
        except Exception as e:
            return [], f"Could not fetch jobs: {e}"

    if not raw:
        return [], "No jobs found. Try a broader keyword or different location."

    jobs = [_normalise(r) for r in raw[:20]]

    # AI enrich all jobs
    for i, job in enumerate(jobs):
        jobs[i] = _ai_enrich(job)

    return jobs, ""


# ── DB helpers ────────────────────────────────────────────────────────────────
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
            "ai_summary":   job.get("ai_summary",""),
        }).execute()
        return True
    except Exception:
        return False


def _load_applied() -> list[dict]:
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
# ══  VIEW A: BROWSE JOBS  ════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app_view == "browse":

    # ── Search Panel ────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="search-panel"><div class="search-panel-title">🔍 Search LinkedIn Jobs</div>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns([3, 2, 2, 2])
        with f1: kw       = st.text_input("Role", placeholder="e.g. Data Scientist, Product Manager", key="jb_kw", label_visibility="collapsed")
        with f2: company_q= st.text_input("Company", placeholder="e.g. Google, Amazon", key="jb_co", label_visibility="collapsed")
        with f3: location_q=st.text_input("Location", placeholder="e.g. New York, Remote", key="jb_loc", label_visibility="collapsed")
        with f4: date_f   = st.selectbox("Posted", ["Any time","Last 24 hours","Past week","Past month"], key="jb_date", label_visibility="collapsed")
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

    # ── Results ─────────────────────────────────────────────────────────────
    jobs = st.session_state.get("job_results", [])

    if not jobs:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-state-icon">🎯</div>
          <div class="empty-state-title">Search for jobs above</div>
          <div class="empty-state-sub">Live LinkedIn results · AI summaries · Full details extracted</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div style='font-size:0.875rem;color:#64748b;margin-bottom:18px;'>"
            f"Showing <strong>{len(jobs)}</strong> live results · "
            f"<span style='color:#2563EB;font-weight:600;font-size:0.78rem;'>Session-only — saved only when you apply</span></div>",
            unsafe_allow_html=True)

        for job in jobs:
            jid            = str(job["id"])
            already_applied= jid in st.session_state.applied_jobs

            # ── Build metadata row ───────────────────────────────────────────
            pills = []
            if already_applied:
                pills.append('<span class="pill pill-applied">✅ Applied</span>')
            if job.get("salary"):
                pills.append(f'<span class="pill pill-salary">💰 {job["salary"]}</span>')
            if job.get("job_type"):
                pills.append(f'<span class="pill pill-type">{job["job_type"]}</span>')
            if job.get("applicants"):
                pills.append(f'<span class="pill pill-views">👥 {job["applicants"]}</span>')
            if job.get("posted"):
                pills.append(f'<span class="pill pill-posted">🕐 {job["posted"]}</span>')
            pills_html = "".join(pills)

            meta_parts = []
            if job.get("location"): meta_parts.append(f'<span class="job-meta-item"><span class="mi">location_on</span>{job["location"]}</span>')
            if job.get("company_url"): pass  # used internally
            meta_html = "".join(meta_parts)

            summary  = job.get("ai_summary","") or job.get("description","")[:250]
            ai_reqs  = job.get("ai_reqs","")   or job.get("requirements","")[:400]
            desc_full= job.get("description","")

            # ── Card + Action columns ────────────────────────────────────────
            col_card, col_action = st.columns([8, 2], gap="medium")

            with col_card:
                st.markdown(f"""
                <div class="job-card">
                  <div class="job-card-company">
                    <span style="font-family:'Material Symbols Outlined';font-size:14px;
                                 font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
                                 line-height:1;color:#2563EB;">business</span>
                    {job['company']}
                  </div>
                  <div class="job-card-title">{job['title']}</div>
                  <div class="job-card-meta">{meta_html}</div>
                  <div class="pill-row">{pills_html}</div>

                  <div class="section-label">AI Summary</div>
                  <div class="section-text">{summary}</div>

                  {'<div class="card-divider"></div><div class="section-label">Key Requirements & Qualifications</div><div class="section-req">' + ai_reqs.replace("•","<br>•").lstrip("<br>") + "</div>" if ai_reqs else ""}

                  {'<div class="card-divider"></div><div class="section-label">Full Description</div><div class="section-text" style="font-size:0.82rem;color:#64748b;">' + desc_full[:600] + ("…" if len(desc_full)>600 else "") + "</div>" if desc_full and desc_full != summary else ""}
                </div>
                """, unsafe_allow_html=True)

            with col_action:
                st.markdown("<div style='padding-top:24px;display:flex;flex-direction:column;gap:10px;'>", unsafe_allow_html=True)

                # View Job link
                if job.get("url") and job["url"] != "#":
                    st.link_button("🔗 View on LinkedIn", job["url"], use_container_width=True)

                # Apply / Applied button
                if already_applied:
                    st.button("✅ Applied", key=f"apply_{jid}", disabled=True, use_container_width=True)
                else:
                    if st.button("🚀 Apply Now", key=f"apply_{jid}", type="primary", use_container_width=True):
                        _save_applied(job)
                        st.session_state.applied_jobs[jid] = job
                        st.success(f"✅ Saved **{job['title']}** at **{job['company']}**!")
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ══  VIEW B: APPLIED JOBS  ═══════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown(
        "<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:16px;'>"
        "📋 Your Applied Jobs</h3>", unsafe_allow_html=True)

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
            "description":  j.get("description",""),
            "requirements": j.get("ai_reqs","") or j.get("requirements",""),
            "ai_summary":   j.get("ai_summary",""),
            "applicants":   j.get("applicants",""),
        }
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
          <div style="font-size:0.85rem;color:#64748b;margin-top:6px;">
            Browse jobs and click <strong>Apply Now</strong> to track them here.
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── Stats row ────────────────────────────────────────────────────────
        total_apps = len(all_applied)
        companies  = len({j.get("company","") for j in all_applied if j.get("company")})
        with_salary= sum(1 for j in all_applied if j.get("salary"))
        c1,c2,c3,c4 = st.columns(4)
        for col, val, lbl, color in [
            (c1, total_apps,  "Total Applied",    "#2563EB"),
            (c2, companies,   "Companies",         "#7c3aed"),
            (c3, with_salary, "With Salary Info",  "#16a34a"),
            (c4, "–",         "Interviews",        "#d97706"),
        ]:
            with col:
                st.markdown(f"""
                <div class="stat-mini">
                  <div class="stat-mini-val" style="color:{color};">{val}</div>
                  <div class="stat-mini-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # ── Full applied jobs table ──────────────────────────────────────────
        rows_html = ""
        for j in all_applied:
            company    = j.get("company","—")
            title      = j.get("title","—")
            location   = j.get("location","")
            salary     = j.get("salary","")
            job_type   = j.get("job_type","")
            source_url = j.get("source_url", j.get("url",""))
            applied_at = j.get("applied_at","")
            description= j.get("ai_summary") or j.get("description","")
            requirements= j.get("requirements","")
            applicants = j.get("applicants","")

            date_str = str(applied_at)[:19].replace("T"," ") if applied_at else "—"
            letter   = company[0].upper() if company else "?"

            salary_html = (f'<span class="pill pill-salary" style="font-size:0.7rem;">'
                          f'💰 {salary}</span>' if salary else '<span style="color:#cbd5e1;">—</span>')
            type_html   = (f'<span class="pill pill-type" style="font-size:0.7rem;">{job_type}</span>'
                          if job_type else "")
            app_html    = (f'<span class="pill pill-views" style="font-size:0.7rem;">👥 {applicants}</span>'
                          if applicants else "")
            link_html   = (f'<a href="{source_url}" target="_blank" '
                          f'style="color:#2563EB;font-weight:700;font-size:0.78rem;'
                          f'text-decoration:none;display:inline-flex;align-items:center;gap:4px;">'
                          f'🔗 View Job</a>' if source_url else "—")

            rows_html += f"""
            <tr>
              <td>
                <div class="td-company">
                  <div class="co-logo">{letter}</div>
                  <div>
                    <div style="font-weight:700;color:#0f172a;font-size:0.9rem;">{company}</div>
                    <div style="color:#64748b;font-size:0.75rem;">{location}</div>
                  </div>
                </div>
              </td>
              <td>
                <div style="font-weight:600;color:#0f172a;font-size:0.875rem;margin-bottom:3px;">{title}</div>
                <div style="display:flex;gap:5px;flex-wrap:wrap;">{type_html}{app_html}</div>
              </td>
              <td>
                <div class="td-desc">{description[:200] + '…' if len(description)>200 else description}</div>
              </td>
              <td>
                <div class="td-req">{requirements[:300] + '…' if len(requirements)>300 else requirements}</div>
              </td>
              <td>{salary_html}</td>
              <td>{link_html}</td>
              <td style="color:#64748b;font-size:0.78rem;white-space:nowrap;">{date_str}</td>
            </tr>"""

        st.markdown(f"""
        <div class="cs-wrap">
          <table class="cs-table">
            <thead><tr>
              <th>Company</th>
              <th>Job Title</th>
              <th>AI Summary</th>
              <th>Requirements</th>
              <th>Salary</th>
              <th>Link</th>
              <th>Applied Date</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.caption("CareerSync · LinkedIn jobs via Apify · AI insights by Groq llama-3.1-8b · ❤️")