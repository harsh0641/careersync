"""
pages/1_Dashboard.py — CareerSync Main Dashboard
Full UI matching the HTML design reference.
Per-user data via Supabase. Empty on first load until Gmail sync.
"""

import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import streamlit as st
import pandas as pd

from database        import get_all_applications, update_stage, delete_application, upsert_application, update_recruiter_info
from email_service   import fetch_application_emails
from ai_service      import parse_emails_concurrent
from recruiter_finder import enrich_all, enrich_application
from auth            import inject_gmail_env, gmail_configured, get_user_by_id

try:
    from credits_tracker import get_all as credits_get_all, SERVICES as CREDIT_SERVICES
    _CREDITS_OK = True
except ImportError:
    _CREDITS_OK = False

# ── Auth guard ─────────────────────────────────────────────────────────────────
if not st.session_state.get("user"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state["user"]
inject_gmail_env(user)

st.set_page_config(
    page_title="CareerSync — Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Hide Streamlit chrome ──────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"]{display:none!important;}
[data-testid="stSidebar"]{display:none!important;}
.block-container{padding-top:0!important;padding-bottom:2rem!important;max-width:100%!important;}
</style>
""", unsafe_allow_html=True)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');

html,body,.stApp,[data-testid="stAppViewContainer"],
section.main,[data-testid="stMain"]{
  background:#f8fafc!important;
  font-family:'DM Sans',sans-serif!important;
  color:#0f172a!important;
}

/* Header */
.cs-header{
  position:sticky;top:0;z-index:100;
  background:#fff;border-bottom:1px solid #e2e8f0;
  padding:0 2rem;height:64px;
  display:flex;align-items:center;justify-content:space-between;
}
.cs-logo{display:flex;align-items:center;gap:8px;font-size:1.25rem;font-weight:700;color:#0f172a;}
.cs-logo-icon{width:32px;height:32px;background:#2563EB;border-radius:8px;
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;}
.cs-header-right{display:flex;align-items:center;gap:12px;}

/* Stat cards */
.stat-card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;
  padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);text-align:center;}
.stat-num{font-size:1.75rem;font-weight:700;line-height:1;margin-bottom:4px;}
.stat-label{font-size:0.72rem;color:#64748b;font-weight:700;
  text-transform:uppercase;letter-spacing:0.7px;}

/* Table */
.cs-wrap{background:#fff;border:1px solid #e2e8f0;border-radius:12px;
  overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.cs-table{width:100%;border-collapse:collapse;font-family:'DM Sans',sans-serif;}
.cs-table th{background:#f8fafc;color:#64748b;font-weight:700;font-size:0.72rem;
  text-transform:uppercase;letter-spacing:0.5px;padding:14px 20px;
  border-bottom:1px solid #e2e8f0;text-align:left;white-space:nowrap;}
.cs-table td{padding:14px 20px;border-bottom:1px solid #f1f5f9;
  vertical-align:middle;color:#334155;font-size:0.83rem;}
.cs-table tr:last-child td{border-bottom:none;}
.cs-table tr:hover td{background:#f8fafc;}
.co-logo{width:32px;height:32px;border-radius:8px;background:#f1f5f9;
  display:flex;align-items:center;justify-content:center;
  font-size:0.75rem;font-weight:700;color:#475569;flex-shrink:0;}
.co-name{font-weight:700;color:#0f172a;font-size:0.88rem;}
.job-role{color:#475569;font-size:0.83rem;}
.date-txt{color:#64748b;font-size:0.78rem;white-space:nowrap;}

/* Badges */
.badge{display:inline-flex;align-items:center;padding:3px 10px;
  border-radius:20px;font-size:0.72rem;font-weight:700;}
.b-applied  {background:#f1f5f9;color:#475569;}
.b-interview{background:#dbeafe;color:#1d4ed8;}
.b-offer    {background:#dcfce7;color:#15803d;}
.b-rejected {background:#fee2e2;color:#dc2626;}

/* Recruiter */
.rec-name{font-weight:700;color:#0f172a;font-size:0.83rem;display:block;}
.rec-title{color:#64748b;font-size:0.72rem;display:block;margin-top:1px;}
.li-btn{display:inline-flex;align-items:center;gap:4px;background:#fff;
  color:#2563EB;border:1px solid #bfdbfe;border-radius:6px;
  padding:2px 8px;font-size:0.68rem;font-weight:700;
  text-decoration:none;margin-top:3px;}
.li-btn:hover{background:#eff6ff;}
.no-data{color:#cbd5e1;font-size:0.78rem;font-style:italic;}
.email-txt{font-size:0.8rem;font-weight:500;color:#334155;word-break:break-all;}

/* Credits panel */
.credit-wrap{background:#fff;border:1px solid #e2e8f0;border-radius:12px;
  padding:20px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
.credit-bar-bg{height:8px;background:#f1f5f9;border-radius:9999px;overflow:hidden;margin-top:6px;}
.credit-bar-fill{height:100%;border-radius:9999px;}

/* Pro tip */
.pro-tip{background:rgba(37,99,235,.06);border:1px solid rgba(37,99,235,.15);
  border-radius:12px;padding:16px;display:flex;gap:10px;margin-top:12px;}

/* Pagination */
div.stButton>button{
  background:#fff!important;color:#475569!important;
  border:1px solid #e2e8f0!important;border-radius:8px!important;
  font-weight:600!important;font-size:0.85rem!important;
  font-family:'DM Sans',sans-serif!important;
  padding:6px 12px!important;
  box-shadow:0 1px 2px rgba(0,0,0,0.04)!important;
  transition:all 0.15s ease!important;
}
div.stButton>button:hover{background:#f8fafc!important;border-color:#cbd5e1!important;}
div.stButton>button[kind="primary"]{
  background:#2563EB!important;color:#fff!important;
  border-color:#2563EB!important;
  box-shadow:0 4px 6px -1px rgba(37,99,235,0.25)!important;
}
div.stButton>button[kind="primary"]:hover{background:#1d4ed8!important;}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea{
  background:#fff!important;border:1px solid #e2e8f0!important;
  border-radius:8px!important;font-family:'DM Sans',sans-serif!important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"]>div{
  background:#fff!important;border:1px solid #e2e8f0!important;border-radius:8px!important;
}
[data-testid="stTabs"] button{font-family:'DM Sans',sans-serif!important;font-weight:600!important;}
[data-testid="stTabs"] button[aria-selected="true"]{color:#2563EB!important;border-bottom-color:#2563EB!important;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = 0

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="cs-header">
  <div class="cs-logo">
    <div class="cs-logo-icon">💼</div>
    CareerSync
  </div>
  <div class="cs-header-right">
    <span style="font-size:0.85rem;color:#64748b;">
      👋 {user.get('name','').split()[0] if user.get('name') else 'Welcome'}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Action buttons ─────────────────────────────────────────────────────────────
with st.container():
    b1, b2, b3, b4, b5 = st.columns([1.2, 1.8, 1.6, 1.2, 1])
    with b1:
        sync_clicked = st.button("🔄 Sync Gmail", use_container_width=True, type="primary")
    with b2:
        enrich_clicked = st.button("🔍 Find Missing Recruiters", use_container_width=True)
    with b3:
        force_enrich = st.button("⚡ Force Re-Enrich ALL", use_container_width=True)
    with b4:
        if st.button("📁 Saved Jobs", use_container_width=True):
            try:
                st.switch_page("pages/Saved_Jobs.py")
            except Exception:
                st.info("Saved Jobs page not found.")
    with b5:
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state["user"]
            st.switch_page("app.py")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ── Enrich helper ──────────────────────────────────────────────────────────────
def _run_enrich_for(apps_list: list, label: str):
    companies = list({a["company_name"] for a in apps_list})
    with st.status(f"{label} ({len(companies)} companies)…", expanded=True) as status:
        try:
            found_count = 0
            for company in companies:
                st.write(f"🔎 Searching **{company}**…")
                info  = enrich_application(company)
                name  = info.get("recruiter_name",  "")
                email = info.get("recruiter_email", "")
                title = info.get("recruiter_title", "")
                li    = info.get("linkedin_url",    "")
                src   = info.get("source", "")
                for a in apps_list:
                    if a["company_name"] == company:
                        update_recruiter_info(a["id"], email, name, title, li)
                if name or email or li:
                    found_count += 1
                    detail  = f"**{name}**" if name else f"`{email}`" if email else "LinkedIn found"
                    src_tag = f" *(via {src})*" if src else ""
                    st.write(f"✅ {detail}{src_tag}")
                else:
                    st.write(f"❌ Nothing found for **{company}**")
            status.update(label=f"✅ Done! Found data for {found_count}/{len(companies)} companies.", state="complete")
            st.rerun()
        except Exception as e:
            status.update(label=f"❌ Error: {e}", state="error")
            import traceback; st.code(traceback.format_exc())


# ── Sync ───────────────────────────────────────────────────────────────────────
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
                        companies = list({p["company_name"] for p in parsed})
                        enriched  = enrich_all(companies)
                        st.write("💾 Saving to database...")
                        for app in parsed:
                            info = enriched.get(app["company_name"], {})
                            upsert_application(
                                company_name=app["company_name"],
                                position=app["job_title"],
                                applied_date=app["date"],
                                email_subject=app["subject"],
                                recruiter_email=info.get("recruiter_email", ""),
                                recruiter_name=info.get("recruiter_name",  ""),
                                recruiter_title=info.get("recruiter_title",""),
                                linkedin_url=info.get("linkedin_url",     ""),
                            )
                    status.update(label=f"✅ Done! {len(parsed)} applications saved.", state="complete")
                    st.session_state.page = 0
                else:
                    status.update(label="No new emails found.", state="complete")
            except Exception as e:
                status.update(label=f"❌ Error: {e}", state="error")
                st.error(str(e))

if enrich_clicked:
    all_apps = get_all_applications()
    missing = [a for a in all_apps
               if not str(a.get("linkedin_url","")).strip()
               and not str(a.get("recruiter_email","")).strip()
               and not str(a.get("recruiter_name","")).strip()]
    if not missing:
        st.success("✅ All applications already have recruiter data!")
    else:
        _run_enrich_for(missing, "🔍 Finding recruiters")

if force_enrich:
    all_apps = get_all_applications()
    if not all_apps:
        st.warning("No applications in database yet.")
    else:
        _run_enrich_for(all_apps, "⚡ Force Re-Enriching ALL")

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
apps = get_all_applications()
df   = pd.DataFrame(apps) if apps else pd.DataFrame(columns=[
    "id","company_name","position","stage","applied_date","last_updated",
    "email_subject","recruiter_email","recruiter_name","recruiter_title","linkedin_url",
])
for col in ["recruiter_email","recruiter_name","recruiter_title","linkedin_url"]:
    if col not in df.columns: df[col] = ""
    df[col] = df[col].fillna("").astype(str)
if "stage" not in df.columns: df["stage"] = "Applied"

# ══════════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════════
total      = len(df)
applied    = len(df[df.stage == "Applied"])    if not df.empty else 0
interviews = len(df[df.stage == "Interview"])  if not df.empty else 0
offers     = len(df[df.stage == "Offer"])      if not df.empty else 0
rejected   = len(df[df.stage == "Rejected"])   if not df.empty else 0
with_rec   = len(df[df.linkedin_url.str.len() > 0]) if not df.empty else 0

c1,c2,c3,c4,c5,c6 = st.columns(6)
for col, label, val, color in zip(
    [c1,c2,c3,c4,c5,c6],
    ["Total","Applied","Interviews","Offers","Rejected","Recruiters Found"],
    [total,applied,interviews,offers,rejected,with_rec],
    ["#0f172a","#2563eb","#d97706","#16a34a","#dc2626","#7c3aed"],
):
    with col:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-num" style="color:{color}">{val}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTERS
# ══════════════════════════════════════════════════════════════════════════════
f1, f2, f3 = st.columns([3, 1, 1])
with f1:
    search = st.text_input("🔍 Search by Company or Job Title", placeholder="e.g. Google, Engineer...")
with f2:
    stage_f = st.selectbox("Stage", ["All","Applied","Interview","Offer","Rejected"])
with f3:
    rec_f = st.selectbox("Recruiter", ["All","Found","Not Found"])

filtered = df.copy()
if search:
    m = (filtered.company_name.str.contains(search, case=False, na=False) |
         filtered.position.str.contains(search, case=False, na=False))
    filtered = filtered[m]
if stage_f != "All":
    filtered = filtered[filtered.stage == stage_f]
if rec_f == "Found":
    filtered = filtered[filtered.linkedin_url.str.len() > 0]
elif rec_f == "Not Found":
    filtered = filtered[filtered.linkedin_url.str.len() == 0]

filter_key = f"{search}|{stage_f}|{rec_f}"
if st.session_state.get("_fkey") != filter_key:
    st.session_state.page  = 0
    st.session_state._fkey = filter_key

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — 2/3 table + 1/3 credits
# ══════════════════════════════════════════════════════════════════════════════
ROWS_PER_PAGE = 8
total_rows  = len(filtered)
total_pages = max(1, math.ceil(total_rows / ROWS_PER_PAGE))
if st.session_state.page >= total_pages:
    st.session_state.page = total_pages - 1
cur_page   = st.session_state.page
page_start = cur_page * ROWS_PER_PAGE
page_end   = min(page_start + ROWS_PER_PAGE, total_rows)
page_df    = filtered.iloc[page_start:page_end]

BADGE_MAP = {
    "Applied":   "b-applied",
    "Interview": "b-interview",
    "Offer":     "b-offer",
    "Rejected":  "b-rejected",
}


def build_table(rows_df):
    thead = (
        '<div class="cs-wrap"><table class="cs-table"><thead><tr>'
        '<th>Company</th><th>Job Title</th><th>Stage</th>'
        '<th>Applied Date</th><th>Recruiter</th><th>Email</th>'
        '</tr></thead><tbody>'
    )
    if rows_df.empty:
        return (
            thead +
            '<tr><td colspan="6" style="text-align:center;color:#94a3b8;'
            'padding:60px;font-size:0.9rem;">'
            '📭 No applications yet. Hit <strong>Sync Gmail</strong> to get started!'
            '</td></tr></tbody></table></div>'
        )
    rows = ""
    for _, r in rows_df.iterrows():
        badge  = BADGE_MAP.get(str(r["stage"]), "b-applied")
        rec_n  = str(r.get("recruiter_name",  "")).strip()
        rec_t  = str(r.get("recruiter_title", "")).strip()
        li_url = str(r.get("linkedin_url",    "")).strip()
        email  = str(r.get("recruiter_email", "")).strip()
        letter = str(r["company_name"])[0].upper() if r["company_name"] else "?"

        if rec_n and li_url:
            rec_cell = (f'<span class="rec-name">👤 {rec_n}</span>'
                        f'<span class="rec-title">{rec_t}</span>'
                        f'<a href="{li_url}" target="_blank" class="li-btn">🔗 LinkedIn</a>')
        elif rec_n:
            rec_cell = (f'<span class="rec-name">👤 {rec_n}</span>'
                        f'<span class="rec-title">{rec_t}</span>')
        elif li_url:
            rec_cell = f'<a href="{li_url}" target="_blank" class="li-btn">🔗 LinkedIn</a>'
        else:
            rec_cell = '<span class="no-data">Not found</span>'

        email_cell = (f'<span class="email-txt">{email}</span>'
                      if email else '<span class="no-data">—</span>')

        rows += (
            f"<tr>"
            f'<td><div style="display:flex;align-items:center;gap:10px;">'
            f'<div class="co-logo">{letter}</div>'
            f'<span class="co-name">{r["company_name"]}</span></div></td>'
            f'<td><span class="job-role">{r["position"]}</span></td>'
            f'<td><span class="badge {badge}">{r["stage"]}</span></td>'
            f'<td><span class="date-txt">{r["applied_date"]}</span></td>'
            f"<td>{rec_cell}</td><td>{email_cell}</td>"
            f"</tr>"
        )
    return thead + rows + "</tbody></table></div>"


def build_credits_panel():
    if not _CREDITS_OK:
        return '<div class="credit-wrap"><p style="color:#94a3b8;font-size:.85rem;">Credits tracker not available.</p></div>'
    state = credits_get_all()
    SHOW  = [
        ("google_cse","Google Custom Search","Search API calls",       "#2563EB"),
        ("hunter",    "Hunter.io",           "Email finding credits",  "#22c55e"),
        ("groq",      "Groq AI",             "AI generation calls",    "#8b5cf6"),
    ]
    items = ""
    for key, name, sub, color in SHOW:
        svc   = CREDIT_SERVICES.get(key, {})
        entry = state.get(key, {})
        total = svc.get("total", 100)
        used  = entry.get("used", 0)
        pct   = max(2, int((used / total) * 100)) if total > 0 else 2
        items += f"""
<div style="margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:4px;">
    <div>
      <div style="font-size:.875rem;font-weight:700;color:#0f172a;">{name}</div>
      <div style="font-size:.72rem;color:#94a3b8;margin-top:1px;">{sub}</div>
    </div>
    <span style="font-size:.78rem;font-weight:700;color:#334155;">{used:,} / {total:,}</span>
  </div>
  <div class="credit-bar-bg">
    <div class="credit-bar-fill" style="background:{color};width:{pct}%;"></div>
  </div>
</div>"""
    return f"""
<div class="credit-wrap">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
    <span style="font-size:1rem;font-weight:700;color:#0f172a;">Credit Usage</span>
  </div>
  {items}
  <div style="height:1px;background:#f1f5f9;margin:16px 0;"></div>
  <button style="width:100%;padding:10px;border-radius:8px;border:1px solid #e2e8f0;
    background:#fff;font-size:.875rem;font-weight:700;color:#0f172a;cursor:pointer;
    font-family:'DM Sans',sans-serif;">Upgrade Plan</button>
</div>
<div class="pro-tip">
  <span style="font-size:1.3rem;">💡</span>
  <div>
    <div style="font-size:.875rem;font-weight:700;color:#0f172a;margin-bottom:4px;">Pro Tip</div>
    <div style="font-size:.8rem;color:#475569;line-height:1.55;">
      Syncing your Gmail daily improves response tracking accuracy by up to 45%.
    </div>
  </div>
</div>"""


# ── Two-column layout ──────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;'>"
        f"<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin:0;'>"
        f"📋 Applications <span style='color:#94a3b8;font-weight:400;font-size:0.9rem;'>({total_rows})</span>"
        f"</h3></div>",
        unsafe_allow_html=True,
    )
    st.markdown(build_table(page_df), unsafe_allow_html=True)

    # Pagination
    if total_pages > 1:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-size:0.8rem;color:#64748b;margin-bottom:6px;'>"
            f"Showing {page_start+1}–{page_end} of {total_rows}</p>",
            unsafe_allow_html=True,
        )

        def page_slots(cur, total):
            if total <= 7: return list(range(total))
            result = [0]
            lo, hi = max(1, cur-2), min(total-2, cur+2)
            if lo > 1: result.append(None)
            result.extend(range(lo, hi+1))
            if hi < total-2: result.append(None)
            result.append(total-1)
            return result

        slots    = page_slots(cur_page, total_pages)
        n_cols   = 2 + len(slots)
        btn_cols = st.columns(n_cols)

        with btn_cols[0]:
            if st.button("◀", key="pg_prev", disabled=(cur_page==0), use_container_width=True):
                st.session_state.page = cur_page-1; st.rerun()
        for i, slot in enumerate(slots):
            with btn_cols[i+1]:
                if slot is None:
                    st.markdown("<div style='text-align:center;padding-top:6px;color:#94a3b8;'>…</div>", unsafe_allow_html=True)
                else:
                    is_cur   = (slot == cur_page)
                    btn_type = "primary" if is_cur else "secondary"
                    if st.button(str(slot+1), key=f"pg_{slot}", type=btn_type, use_container_width=True):
                        st.session_state.page = slot; st.rerun()
        with btn_cols[-1]:
            if st.button("▶", key="pg_next", disabled=(cur_page==total_pages-1), use_container_width=True):
                st.session_state.page = cur_page+1; st.rerun()

with col_right:
    st.markdown(
        "<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>"
        "Credit Usage</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(build_credits_panel(), unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# AI COLD EMAIL GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h3 style='font-size:1.05rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>"
    "✨ AI Cold Email Generator</h3>",
    unsafe_allow_html=True,
)

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
    st.info("💡 No recruiters with emails on this page yet. Sync emails or find recruiters first.", icon="ℹ️")
else:
    ce1, ce2, ce3 = st.columns([2.5, 1.5, 1])
    with ce1:
        sel_label = st.selectbox("Select Recruiter", [r["label"] for r in rows_for_email],
                                  key="email_rec_sel", label_visibility="collapsed")
        sel_rec   = next((r for r in rows_for_email if r["label"] == sel_label), None)
    with ce2:
        tone = st.selectbox("Tone", ["Professional","Friendly & Warm","Concise & Direct","Enthusiastic"],
                             key="email_tone", label_visibility="collapsed")
    with ce3:
        gen_email = st.button("✨ Generate", key="gen_email_btn", type="primary", use_container_width=True)

    if gen_email and sel_rec:
        greet  = f"Hi {sel_rec['rec_name'].split()[0]}," if sel_rec["rec_name"] else "Hi,"
        prompt = (
            f"Write a {tone.lower()} cold follow-up email from a job seeker "
            f"to a recruiter at {sel_rec['company']} about the {sel_rec['position']} role.\n\n"
            f"Opening: {greet}\n\nStrict rules:\n"
            f"- Max 130 words\n"
            f"- First line MUST be: Subject: <subject here>\n"
            f"- Then blank line\n"
            f"- Then body starting with {greet}\n"
            f"- No square brackets or placeholders\n"
            f"- Close with: Best regards,\n"
            f"- Tone: {tone.lower()}"
        )
        with st.spinner("✨ Writing your cold email..."):
            try:
                import requests as _req
                from config import GROQ_API_KEY as _gk
                resp = _req.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Content-Type":"application/json","Authorization":f"Bearer {_gk}"},
                    json={"model":"llama-3.1-8b-instant",
                          "messages":[{"role":"user","content":prompt}],
                          "max_tokens":420,"temperature":0.72},
                    timeout=20,
                )
                result   = resp.json()
                raw_text = result["choices"][0]["message"]["content"].strip()
                lines    = raw_text.split("\n")
                subj_out, body_lines, past_subj = "", [], False
                for ln in lines:
                    if not subj_out and ln.lower().startswith("subject:"):
                        subj_out = ln[len("subject:"):].strip(); past_subj = True
                    elif past_subj:
                        body_lines.append(ln)
                if not subj_out and lines:
                    subj_out = lines[0]; body_lines = lines[1:]
                st.session_state["ai_email_subj"] = subj_out
                st.session_state["ai_email_body"] = "\n".join(body_lines).lstrip("\n").strip()
                st.session_state["ai_email_to"]   = sel_rec["email"]
            except Exception as ex:
                st.error(f"❌ Groq error: {ex}")

    if st.session_state.get("ai_email_subj") or st.session_state.get("ai_email_body"):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        subj_edited = st.text_input("Subject Line", value=st.session_state.get("ai_email_subj",""), key="ai_subj_field")
        body_edited = st.text_area("Email Body",    value=st.session_state.get("ai_email_body",""), height=200, key="ai_body_field")
        ca, cb, _ = st.columns([1.2, 1.4, 3])
        with ca:
            if st.button("📋 Copy Email", key="copy_email_btn"):
                st.success("Use Ctrl+A in the body field to select all!", icon="✅")
        with cb:
            to_addr = st.session_state.get("ai_email_to","")
            mailto  = (f"mailto:{to_addr}"
                       f"?subject={subj_edited.replace(' ','%20')}"
                       f"&body={body_edited[:500].replace(chr(10),'%0A').replace(' ','%20')}")
            st.link_button("📨 Open in Mail Client", mailto)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MANAGE APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h3 style='font-size:1.1rem;font-weight:700;color:#0f172a;margin-bottom:4px;'>"
    "⚙️ Manage Applications</h3>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["✏️ Update Stage","🔍 Find Recruiter","➕ Add Manually","🗑️ Delete"])

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
            st.success(f"Updated to **{ns}**."); st.rerun()

with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    if df.empty:
        st.info("No applications yet.")
    else:
        opts2 = {f"{r['company_name']} — {r['position']}": (r["id"], r["company_name"]) for _, r in df.iterrows()}
        sel2  = st.selectbox("Select application", list(opts2.keys()), key="t2_sel")
        app_id2, company2 = opts2[sel2]
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⚡ Run Full Pipeline", key="t2_find", use_container_width=True, type="primary"):
                with st.status(f"Running all sources for {company2}…", expanded=True) as s2:
                    try:
                        info = enrich_application(company2)
                        update_recruiter_info(app_id2,
                            info.get("recruiter_email",""), info.get("recruiter_name",""),
                            info.get("recruiter_title",""), info.get("linkedin_url",""))
                        if info.get("recruiter_name") or info.get("linkedin_url"):
                            s2.update(label=f"✅ Found via {info.get('source','?')}!", state="complete")
                            st.success(f"**{info.get('recruiter_name','—')}** · {info.get('recruiter_title','—')}")
                        else:
                            s2.update(label="No result found", state="error")
                        st.rerun()
                    except Exception as e:
                        s2.update(label=f"Error: {e}", state="error")
        with col_b:
            with st.expander("✏️ Override manually"):
                me     = st.text_input("Recruiter Email", key="t2_me")
                mn     = st.text_input("Recruiter Name",  key="t2_mn")
                mt_val = st.text_input("Recruiter Title", key="t2_mt")
                ml     = st.text_input("LinkedIn URL",    key="t2_ml")
                if st.button("💾 Save Override", key="t2_save"):
                    update_recruiter_info(app_id2, me, mn, mt_val, ml)
                    st.success("Saved!"); st.rerun()

with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        mc = st.text_input("Company Name", key="m_co")
        mt = st.text_input("Job Title",    key="m_ti")
    with c2:
        md = st.date_input("Applied Date", key="m_da")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Add Application", key="m_add", type="primary"):
        if mc and mt:
            info = enrich_application(mc)
            upsert_application(mc, mt, str(md), "Manually added",
                info.get("recruiter_email",""), info.get("recruiter_name",""),
                info.get("recruiter_title",""), info.get("linkedin_url",""))
            st.success(f"Added **{mt}** at **{mc}**."); st.rerun()
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
            st.success("Deleted."); st.rerun()

st.divider()
st.caption("CareerSync v3.0 · Gmail · Groq AI · Hunter.io · Apollo.io · Supabase · ❤️")