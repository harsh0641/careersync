"""
pages/2_Applications.py — CareerSync Job Application Portal
- Browse Jobs: Apify LinkedIn scraper → live results (session only, never stored)
- Applied Jobs: jobs saved to Supabase when user clicks Apply
- AI summaries: Groq llama-3.1-8b-instant
"""

import os, sys, time, requests
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
    if st.session_state.get("user"):
        return True
    uid = st.query_params.get("uid", "")
    if uid:
        user = get_user_by_id(uid)
        if user:
            st.session_state["user"]    = user
            st.session_state["user_id"] = uid
            return True
    return False

def _logout():
    for k in ["user", "user_id"]:
        st.session_state.pop(k, None)
    st.query_params.clear()
    st.switch_page("app.py")

if not _restore():
    st.switch_page("app.py")
    st.stop()

user = st.session_state["user"]
st.query_params["uid"] = user["id"]
inject_gmail_env(user)

# ══════════════════════════════════════════════════════════════════════════════
# IMPORTS (after auth)
# ══════════════════════════════════════════════════════════════════════════════
from config import GROQ_API_KEY

try:
    from supabase import create_client
    SUPABASE_URL = os.environ.get("SUPABASE_URL", st.secrets.get("SUPABASE_URL", ""))
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", ""))
    _sb = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None
except Exception:
    _sb = None

APIFY_KEY = os.environ.get("APIFY_API_KEY", st.secrets.get("APIFY_API_KEY", ""))

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR  (same style as Dashboard)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <style>
    [data-testid="stSidebar"]{background:#fff!important;border-right:1px solid #e2e8f0!important;}
    [data-testid="stSidebar"] .stButton>button{
      text-align:left!important;justify-content:flex-start!important;
      background:transparent!important;color:#475569!important;
      border:none!important;box-shadow:none!important;
      font-size:0.9rem!important;font-weight:500!important;
      padding:8px 12px!important;border-radius:8px!important;width:100%!important;}
    [data-testid="stSidebar"] .stButton>button:hover{
      background:#f8fafc!important;color:#0f172a!important;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;align-items:center;gap:8px;padding:20px 4px 24px;">
      <div style="width:32px;height:32px;background:#2563EB;border-radius:8px;
                  display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;">💼</div>
      <span style="font-size:1.15rem;font-weight:700;color:#0f172a;">CareerSync</span>
    </div>
    """, unsafe_allow_html=True)

    nav_pages = [
        ("🏠", "Dashboard",        "pages/1_Dashboard.py"),
        ("📋", "Applications",     "pages/2_Applications.py"),
        ("✉️",  "Cold Email",       "pages/3_Cold_Email.py"),
        ("🔍", "Research Pipeline","pages/4_Pipeline.py"),
        ("⚙️", "Settings",         "pages/5_Settings.py"),
    ]
    for icon, label, path in nav_pages:
        is_active = (label == "Applications")
        if is_active:
            st.markdown(f"""
            <div style="background:rgba(37,99,235,0.08);color:#2563EB;display:flex;
                 align-items:center;gap:10px;padding:10px 12px;border-radius:8px;
                 margin-bottom:2px;font-weight:700;font-size:0.9rem;">
              {icon}  {label}
            </div>""", unsafe_allow_html=True)
        else:
            if st.button(f"{icon}  {label}", key=f"nav_{label}"):
                try:
                    st.switch_page(path)
                except Exception:
                    st.info(f"{label} page coming soon!")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.divider()

    name_disp  = user.get("name", "User")
    email_disp = user.get("email", "")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 4px 12px;">
      <div style="width:36px;height:36px;border-radius:50%;background:#e0e7ff;
                  display:flex;align-items:center;justify-content:center;
                  font-weight:700;color:#3730a3;font-size:0.9rem;flex-shrink:0;">
        {name_disp[0].upper() if name_disp else "U"}
      </div>
      <div style="min-width:0;">
        <div style="font-weight:700;font-size:0.85rem;color:#0f172a;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name_disp}</div>
        <div style="font-size:0.72rem;color:#64748b;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{email_disp}</div>
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"],
section.main,[data-testid="stMain"]{
  background:#f8fafc!important;font-family:'DM Sans',sans-serif!important;color:#0f172a!important;}
.block-container{padding-top:2rem!important;padding-bottom:2rem!important;max-width:1200px!important;}

/* Toggle pill */
.toggle-wrap{display:flex;background:#f1f5f9;border-radius:12px;padding:4px;gap:4px;width:fit-content;margin-bottom:24px;}
.toggle-btn{padding:8px 24px;border-radius:8px;font-size:0.875rem;font-weight:600;cursor:pointer;border:none;transition:all 0.2s;}
.toggle-active{background:#fff;color:#2563EB;box-shadow:0 1px 4px rgba(0,0,0,0.10);}
.toggle-inactive{background:transparent;color:#64748b;}

/* Job card */
.job-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:20px 24px;
  margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.04);transition:box-shadow 0.15s;}
.job-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.08);}
.job-company{font-size:0.72rem;font-weight:700;color:#2563EB;text-transform:uppercase;letter-spacing:0.6px;}
.job-title{font-size:1rem;font-weight:700;color:#0f172a;margin:4px 0;}
.job-meta{font-size:0.78rem;color:#64748b;margin-bottom:10px;}
.job-summary{font-size:0.85rem;color:#475569;line-height:1.6;margin-bottom:12px;}
.job-badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;
  font-size:0.72rem;font-weight:700;background:#f1f5f9;color:#475569;margin-right:6px;}
.applied-badge{background:#dcfce7;color:#15803d;}
.salary-badge{background:#fef9c3;color:#854d0e;}

/* Applied table */
.cs-wrap{background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.cs-table{width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;}
.cs-table th{background:#f8fafc;color:#64748b;font-weight:700;font-size:0.72rem;
  text-transform:uppercase;letter-spacing:0.5px;padding:14px 20px;
  border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap;}
.cs-table td{padding:14px 20px;border-bottom:1px solid #f1f5f9;vertical-align:middle;color:#334155;font-size:0.83rem;}
.cs-table tr:last-child td{border-bottom:none;}
.cs-table tr:hover td{background:#f8fafc;}
.co-logo{width:32px;height:32px;border-radius:8px;background:#f1f5f9;
  display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;color:#475569;flex-shrink:0;}

div.stButton>button{
  background:#fff!important;color:#475569!important;border:1px solid #e2e8f0!important;
  border-radius:8px!important;font-weight:600!important;font-size:0.85rem!important;
  font-family:'DM Sans',sans-serif!important;padding:6px 12px!important;transition:all 0.15s!important;}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{background:#2563EB!important;color:#fff!important;border-color:#2563EB!important;}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}
div[data-testid="stTextInput"] input,div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{
  background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "app_view"      not in st.session_state: st.session_state.app_view      = "browse"
if "job_results"   not in st.session_state: st.session_state.job_results   = []
if "applied_jobs"  not in st.session_state: st.session_state.applied_jobs  = {}  # id → job dict
if "ai_summaries"  not in st.session_state: st.session_state.ai_summaries  = {}  # job_id → summary

user_id = user["id"]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _groq_summarise(title: str, description: str) -> str:
    """Call Groq to generate a 2-sentence job summary."""
    if not GROQ_API_KEY or not description:
        return description[:200] + "…" if len(description) > 200 else description
    prompt = (
        f"Job title: {title}\n\nDescription:\n{description[:1500]}\n\n"
        "Write exactly 2 clear, concise sentences summarising this role for a job seeker. "
        "Focus on what the role involves and key requirements. No bullet points."
    )
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": "llama-3.1-8b-instant",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 120, "temperature": 0.4},
            timeout=15
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return description[:200] + "…" if len(description) > 200 else description


def _fetch_linkedin_jobs(keyword: str, location: str, company: str,
                         date_filter: str) -> tuple[list[dict], str]:
    """
    Fetch LinkedIn jobs via Apify actor: bebity/linkedin-jobs-scraper
    Uses async run + polling so it never times out.
    Returns (jobs_list, error_message).
    Results are session-only — NOT stored in DB.
    """
    if not APIFY_KEY:
        return [], "Apify API key not configured. Add APIFY_API_KEY to Streamlit secrets."

    # Map date filter → LinkedIn f_TPR value
    date_map = {
        "Any time":      "",
        "Last 24 hours": "r86400",
        "Past week":     "r604800",
        "Past month":    "r2592000",
    }
    f_tpr = date_map.get(date_filter, "")

    # Build search keyword
    search_kw = keyword.strip()
    if company.strip():
        search_kw = f"{search_kw} {company.strip()}".strip()
    if not search_kw:
        search_kw = "software engineer"

    # ── Actor: bebity/linkedin-jobs-scraper ─────────────────────────────────
    # Correct input schema for this actor
    actor_input = {
        "title":    search_kw,
        "location": location.strip() or "",
        "rows":     20,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }
    if f_tpr:
        actor_input["publishedAt"] = f_tpr

    ACTOR_ID = "bebity~linkedin-jobs-scraper"
    BASE     = "https://api.apify.com/v2"
    HEADERS  = {"Content-Type": "application/json"}
    PARAMS   = {"token": APIFY_KEY}

    # ── Step 1: Start the run (async) ────────────────────────────────────────
    try:
        start_resp = requests.post(
            f"{BASE}/acts/{ACTOR_ID}/runs",
            json=actor_input,
            params={**PARAMS, "memory": 512, "timeout": 120},
            headers=HEADERS,
            timeout=30,
        )
    except requests.exceptions.ConnectionError:
        return [], "Network error — cannot reach Apify. Check your connection."
    except requests.exceptions.Timeout:
        return [], "Request timed out starting the job scraper."

    if start_resp.status_code not in (200, 201):
        try:
            err = start_resp.json().get("error", {}).get("message", start_resp.text[:200])
        except Exception:
            err = start_resp.text[:200]
        return [], f"Apify error {start_resp.status_code}: {err}"

    run_data = start_resp.json().get("data", {})
    run_id   = run_data.get("id", "")
    if not run_id:
        return [], "Apify did not return a run ID. Try again."

    # ── Step 2: Poll until SUCCEEDED or FAILED (max 120s) ───────────────────
    poll_url = f"{BASE}/actor-runs/{run_id}"
    deadline  = time.time() + 120
    status    = "RUNNING"

    while time.time() < deadline:
        try:
            poll = requests.get(poll_url, params=PARAMS, timeout=15)
            status = poll.json().get("data", {}).get("status", "RUNNING")
        except Exception:
            time.sleep(5)
            continue

        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            return [], f"Scraper run {status}. LinkedIn may be blocking — try again."
        time.sleep(5)  # poll every 5s
    else:
        return [], "Scraper timed out after 120s. LinkedIn was slow — try again."

    # ── Step 3: Fetch dataset items ──────────────────────────────────────────
    dataset_id = poll.json().get("data", {}).get("defaultDatasetId", "")
    if not dataset_id:
        return [], "No dataset returned from scraper run."

    try:
        data_resp = requests.get(
            f"{BASE}/datasets/{dataset_id}/items",
            params={**PARAMS, "format": "json", "clean": "true"},
            timeout=30,
        )
        items = data_resp.json() if data_resp.status_code == 200 else []
        return items, ""
    except Exception as e:
        return [], f"Failed to fetch results: {e}"


def _save_applied_job(job: dict):
    """Save applied job to Supabase applied_jobs table."""
    if not _sb:
        return False
    try:
        row = {
            "user_id":     user_id,
            "company":     job.get("companyName", job.get("company", "")),
            "title":       job.get("title", ""),
            "description": job.get("description", ""),
            "requirements":job.get("requirements", ""),
            "salary":      job.get("salary", job.get("salaryRange", "")),
            "source_url":  job.get("jobUrl", job.get("url", "")),
            "location":    job.get("location", ""),
        }
        _sb.table("applied_jobs").insert(row).execute()
        return True
    except Exception:
        return False


def _load_applied_jobs() -> list[dict]:
    """Load this user's applied jobs from Supabase."""
    if not _sb:
        return []
    try:
        res = (_sb.table("applied_jobs")
               .select("*")
               .eq("user_id", user_id)
               .order("applied_at", desc=True)
               .execute())
        return res.data or []
    except Exception:
        return []


def _normalise(raw: dict) -> dict:
    """Normalise bebity/linkedin-jobs-scraper result fields to a consistent shape."""
    # bebity fields: title, companyName, location, salary, description, jobUrl, publishedAt
    # Also handle variations from other actors
    desc = (raw.get("description") or
            raw.get("descriptionText") or
            raw.get("jobDescription") or "")

    company = (raw.get("companyName") or
               raw.get("company") or
               raw.get("company_name") or "Unknown Company")

    url = (raw.get("jobUrl") or
           raw.get("url") or
           raw.get("applyUrl") or "#")

    # Generate a stable ID from URL or title+company
    job_id = (raw.get("id") or
              raw.get("jobId") or
              str(abs(hash(url + raw.get("title","")))))

    return {
        "id":          str(job_id),
        "title":       raw.get("title", "Unknown Role"),
        "company":     company,
        "location":    raw.get("location", ""),
        "salary":      (raw.get("salary") or raw.get("salaryRange") or
                        raw.get("salary_range") or ""),
        "description": desc,
        "requirements":raw.get("requirements") or raw.get("jobRequirements") or "",
        "url":         url,
        "posted":      (raw.get("publishedAt") or raw.get("postedAt") or
                        raw.get("posted_date") or ""),
        "views":       (raw.get("views") or raw.get("applicantsCount") or
                        raw.get("numApplicants") or ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h2 style='font-size:1.5rem;font-weight:700;color:#0f172a;margin-bottom:4px;'>Job Applications</h2>"
    "<p style='font-size:0.875rem;color:#64748b;margin-bottom:20px;'>"
    "Discover live LinkedIn jobs or track what you've already applied to.</p>",
    unsafe_allow_html=True
)

# ══════════════════════════════════════════════════════════════════════════════
# TOGGLE  —  Browse Jobs  |  Applied Jobs
# ══════════════════════════════════════════════════════════════════════════════
col_browse, col_applied, _ = st.columns([1, 1, 6])
with col_browse:
    if st.button("🔍  Browse Jobs",
                 type="primary" if st.session_state.app_view == "browse" else "secondary",
                 use_container_width=True, key="btn_browse"):
        st.session_state.app_view = "browse"
        st.rerun()
with col_applied:
    if st.button("📋  Applied Jobs",
                 type="primary" if st.session_state.app_view == "applied" else "secondary",
                 use_container_width=True, key="btn_applied"):
        st.session_state.app_view = "applied"
        st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VIEW  A:  BROWSE JOBS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.app_view == "browse":

    # ── Search & Filter panel ────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;
                padding:20px 24px 16px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
      <div style="font-size:0.78rem;font-weight:700;color:#0f172a;text-transform:uppercase;
                  letter-spacing:0.6px;margin-bottom:12px;">🔍 Search LinkedIn Jobs</div>
    """, unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([3, 2, 2, 2])
    with f1:
        kw = st.text_input("Job Role / Title", placeholder="e.g. Product Manager", key="jb_kw",
                           label_visibility="collapsed")
    with f2:
        company_q = st.text_input("Company", placeholder="e.g. Google", key="jb_co",
                                  label_visibility="collapsed")
    with f3:
        location_q = st.text_input("Location", placeholder="e.g. San Francisco", key="jb_loc",
                                   label_visibility="collapsed")
    with f4:
        date_f = st.selectbox("Posted", ["Any time", "Last 24 hours", "Past week", "Past month"],
                              key="jb_date", label_visibility="collapsed")

    st.markdown("</div>", unsafe_allow_html=True)

    _, btn_col, _ = st.columns([5, 2, 5])
    with btn_col:
        search_clicked = st.button("🚀 Search Jobs", type="primary",
                                   use_container_width=True, key="jb_search")

    if search_clicked:
        if not kw.strip() and not company_q.strip():
            st.warning("Please enter a job title or company name.")
        else:
            with st.status("🔎 Fetching live LinkedIn jobs via Apify…", expanded=True) as status:
                st.write("⏳ Starting LinkedIn scraper…")
                raw_results, err = _fetch_linkedin_jobs(kw, location_q, company_q, date_f)

                if err:
                    status.update(label=f"❌ {err}", state="error")
                    st.session_state.job_results = []
                elif not raw_results:
                    status.update(label="No jobs found for this search.", state="error")
                    st.session_state.job_results = []
                    st.warning("No jobs found. Try a broader keyword or different location.")
                else:
                    st.write(f"✅ Scraped {len(raw_results)} jobs from LinkedIn!")
                    st.write("✨ Generating AI summaries with Groq…")
                    jobs_norm = [_normalise(r) for r in raw_results]
                    # Pre-generate all AI summaries during load
                    summaries = {}
                    for j in jobs_norm:
                        jid = str(j["id"])
                        summaries[jid] = _groq_summarise(j["title"], j["description"])
                    st.session_state.job_results   = jobs_norm
                    st.session_state.ai_summaries  = summaries
                    status.update(
                        label=f"✅ Found {len(jobs_norm)} jobs with AI summaries!",
                        state="complete"
                    )

    # ── Results ─────────────────────────────────────────────────────────────
    jobs = st.session_state.get("job_results", [])

    if not jobs:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#94a3b8;">
          <div style="font-size:2.5rem;margin-bottom:12px;">🎯</div>
          <div style="font-size:1rem;font-weight:600;">Search for jobs above</div>
          <div style="font-size:0.85rem;margin-top:6px;">Live results from LinkedIn — nothing is stored until you Apply</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div style='font-size:0.875rem;color:#64748b;margin-bottom:16px;'>"
            f"Showing <strong>{len(jobs)}</strong> live results · "
            f"<span style='color:#2563EB;font-size:0.78rem;'>Results are session-only and not saved</span></div>",
            unsafe_allow_html=True
        )

        for job in jobs:
            jid = str(job["id"])
            already_applied = jid in st.session_state.applied_jobs

            # Summaries pre-generated at search time; fallback to truncated description
            summary = st.session_state.ai_summaries.get(
                jid,
                job["description"][:200] + "…" if len(job.get("description","")) > 200
                else job.get("description","")
            )
            salary  = job.get("salary", "")
            views   = job.get("views", "")
            posted  = job.get("posted", "")

            # Build badge row
            meta_parts = []
            if job["location"]: meta_parts.append(f"📍 {job['location']}")
            if posted:          meta_parts.append(f"🕐 {posted}")
            if views:           meta_parts.append(f"👁 {views} views")
            meta_str = "  ·  ".join(meta_parts)

            # Render card using columns (left: info, right: apply button)
            card_left, card_right = st.columns([8, 2])
            with card_left:
                st.markdown(f"""
                <div class="job-card">
                  <div class="job-company">{job['company']}</div>
                  <div class="job-title">{job['title']}</div>
                  <div class="job-meta">{meta_str}</div>
                  {'<span class="job-badge salary-badge">💰 ' + salary + '</span>' if salary else ''}
                  {'<span class="job-badge applied-badge">✅ Applied</span>' if already_applied else ''}
                  <div class="job-summary">{summary}</div>
                </div>
                """, unsafe_allow_html=True)

            with card_right:
                st.markdown("<div style='padding-top:24px'></div>", unsafe_allow_html=True)

                # View on LinkedIn
                if job["url"] and job["url"] != "#":
                    st.link_button("🔗 View Job", job["url"], use_container_width=True)

                # Apply button
                if already_applied:
                    st.button("✅ Applied", key=f"apply_{jid}", disabled=True,
                              use_container_width=True)
                else:
                    if st.button("Apply Now", key=f"apply_{jid}",
                                 type="primary", use_container_width=True):
                        ok = _save_applied_job(job)
                        if ok or True:   # optimistic if DB not configured
                            st.session_state.applied_jobs[jid] = job
                            st.success(f"✅ Saved '{job['title']}' to your Applied Jobs!")
                            st.rerun()

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VIEW  B:  APPLIED JOBS
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown(
        "<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:16px;'>"
        "📋 Your Applied Jobs</h3>",
        unsafe_allow_html=True
    )

    # Load from Supabase + merge with session-applied (in case DB is slow)
    db_jobs = _load_applied_jobs()

    # Merge: DB rows + any session-applied not yet in DB
    seen_urls = {j.get("source_url", "") for j in db_jobs}
    session_extras = [
        j for j in st.session_state.applied_jobs.values()
        if j.get("url", "") not in seen_urls
    ]

    all_applied = db_jobs + [
        {
            "company":      j.get("company", ""),
            "title":        j.get("title", ""),
            "location":     j.get("location", ""),
            "salary":       j.get("salary", ""),
            "source_url":   j.get("url", ""),
            "applied_at":   "Just now",
            "description":  j.get("description", ""),
        }
        for j in session_extras
    ]

    if not all_applied:
        st.markdown("""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;
                    padding:60px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
          <div style="font-size:2.5rem;margin-bottom:12px;">📭</div>
          <div style="font-size:1rem;font-weight:600;color:#0f172a;">No applied jobs yet</div>
          <div style="font-size:0.85rem;color:#64748b;margin-top:6px;">
            Browse jobs and click <strong>Apply Now</strong> to track them here
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary stats
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
                        padding:16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size:1.8rem;font-weight:700;color:#2563EB;">{len(all_applied)}</div>
              <div style="font-size:0.72rem;color:#64748b;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.7px;margin-top:4px;">Total Applied</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            companies = len({j.get("company","") for j in all_applied if j.get("company")})
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
                        padding:16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size:1.8rem;font-weight:700;color:#7c3aed;">{companies}</div>
              <div style="font-size:0.72rem;color:#64748b;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.7px;margin-top:4px;">Companies</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;
                        padding:16px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
              <div style="font-size:1.8rem;font-weight:700;color:#16a34a;">–</div>
              <div style="font-size:0.72rem;color:#64748b;font-weight:700;text-transform:uppercase;
                          letter-spacing:0.7px;margin-top:4px;">Interviews</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Table
        rows_html = ""
        for j in all_applied:
            company    = j.get("company", "—")
            title      = j.get("title",   "—")
            location   = j.get("location","—")
            salary     = j.get("salary",  "")
            source_url = j.get("source_url", j.get("url", ""))
            applied_at = j.get("applied_at", "")

            # Date string: strip to date part
            date_str = str(applied_at)[:10] if applied_at else "—"
            letter   = company[0].upper() if company else "?"

            link_html = (f'<a href="{source_url}" target="_blank" '
                         f'style="color:#2563EB;font-weight:600;font-size:0.78rem;'
                         f'text-decoration:none;">🔗 View</a>'
                         if source_url else "—")

            salary_html = (f'<span style="background:#fef9c3;color:#854d0e;padding:2px 8px;'
                           f'border-radius:20px;font-size:0.72rem;font-weight:700;">{salary}</span>'
                           if salary else "—")

            rows_html += f"""
            <tr>
              <td><div style="display:flex;align-items:center;gap:10px;">
                <div class="co-logo">{letter}</div>
                <div>
                  <div style="font-weight:700;color:#0f172a;font-size:0.88rem;">{company}</div>
                  <div style="color:#64748b;font-size:0.75rem;">{location}</div>
                </div>
              </div></td>
              <td style="font-weight:500;">{title}</td>
              <td>{salary_html}</td>
              <td style="color:#64748b;font-size:0.78rem;">{date_str}</td>
              <td>{link_html}</td>
            </tr>"""

        st.markdown(f"""
        <div class="cs-wrap">
          <table class="cs-table">
            <thead><tr>
              <th>Company</th>
              <th>Job Title</th>
              <th>Salary</th>
              <th>Applied Date</th>
              <th>Link</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
st.caption("CareerSync · Live jobs powered by LinkedIn via Apify · AI summaries by Groq ❤️")