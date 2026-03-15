"""
app.py — CareerSync Landing + Login + Register
Exact HTML UI design reference.
Navbar: only Log In + Get Started Free.
No floating buttons. No iframe. Pure Streamlit st.markdown.
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

st.set_page_config(
    page_title="CareerSync — Automated Job Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import register_user, login_user, supabase_ready, get_user_by_id

# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENT LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def _restore_session():
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

def _set_login(user: dict):
    st.session_state.pop("logged_out", None)
    st.session_state["user"]    = user
    st.session_state["user_id"] = user["id"]
    st.query_params["uid"]      = user["id"]

def go(view: str):
    st.session_state.auth_view = view

_restore_session()

if st.session_state.get("user"):
    st.switch_page("pages/1_Dashboard.py")
    st.stop()

if "auth_view" not in st.session_state:
    st.session_state.auth_view = "landing"

# ── Hide ALL Streamlit chrome ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="stSidebar"],
[data-testid="collapsedControl"],[data-testid="stHeader"]{display:none!important;}
html,body,.stApp,[data-testid="stAppViewContainer"],
section.main,[data-testid="stMain"]{
  background:#f6f6f8!important;
  font-family:'DM Sans',sans-serif!important;
  margin:0!important;padding:0!important;
}
.block-container{padding:0!important;max-width:100%!important;margin:0!important;}
[data-testid="stVerticalBlock"]{gap:0!important;}
/* Hide ALL streamlit buttons on landing except login/signup triggers */
.stButton{display:none!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE — entire page as pure HTML via st.markdown
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.auth_view == "landing":

    # Detect nav clicks via query params
    nav_action = st.query_params.get("nav", "")
    if nav_action == "login":
        st.query_params.clear()
        go("login"); st.rerun()
    elif nav_action == "signup":
        st.query_params.clear()
        go("register"); st.rerun()

    st.markdown(f"""
    <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'DM Sans', sans-serif; background: #f6f6f8; color: #0f172a; }}

    /* NAV */
    .nav {{
      position: sticky; top: 0; z-index: 999;
      background: rgba(246,246,248,0.92);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid #e2e8f0;
      height: 64px; padding: 0 2.5rem;
      display: flex; align-items: center; justify-content: space-between;
    }}
    .nav-logo {{
      display: flex; align-items: center; gap: 8px;
      font-size: 1.15rem; font-weight: 700; color: #0f172a; text-decoration: none;
    }}
    .nav-logo-icon {{ color: #2563EB; font-size: 1.3rem; }}
    .nav-btns {{ display: flex; align-items: center; gap: 10px; }}
    .btn-login {{
      background: #fff; color: #0f172a;
      border: 1.5px solid #e2e8f0; border-radius: 10px;
      padding: 9px 20px; font-size: 0.875rem; font-weight: 600;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      transition: all 0.15s; text-decoration: none; display: inline-flex; align-items: center;
    }}
    .btn-login:hover {{ background: #f8fafc; border-color: #cbd5e1; }}
    .btn-signup {{
      background: #2563EB; color: #fff;
      border: none; border-radius: 10px;
      padding: 9px 20px; font-size: 0.875rem; font-weight: 700;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      transition: all 0.15s; text-decoration: none; display: inline-flex; align-items: center;
      box-shadow: 0 2px 8px rgba(37,99,235,0.25);
    }}
    .btn-signup:hover {{ background: #1d4ed8; }}

    /* HERO */
    .hero {{
      max-width: 1280px; margin: 0 auto; padding: 80px 2.5rem 64px;
      display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center;
    }}
    @media(max-width:860px){{ .hero {{ grid-template-columns: 1fr; padding: 40px 1.5rem; }} }}
    .hero-badge {{
      display: inline-flex; align-items: center; gap: 7px; padding: 5px 14px;
      border-radius: 9999px; background: rgba(37,99,235,0.08);
      border: 1px solid rgba(37,99,235,0.2);
      font-size: 0.72rem; font-weight: 700; color: #2563EB;
      text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 22px;
    }}
    .hero-dot {{
      width: 6px; height: 6px; border-radius: 50%; background: #2563EB;
      display: inline-block; animation: pulse 2s infinite;
    }}
    @keyframes pulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.35;}} }}
    .hero h1 {{
      font-size: clamp(2.4rem, 4.5vw, 3.75rem); font-weight: 700;
      color: #0f172a; line-height: 1.05; letter-spacing: -1.5px; margin-bottom: 20px;
    }}
    .hero h1 span {{ color: #2563EB; }}
    .hero p {{
      font-size: 1.05rem; color: #64748b; line-height: 1.72;
      margin-bottom: 32px; max-width: 500px;
    }}
    .hero-input-row {{ display: flex; gap: 10px; margin-bottom: 28px; flex-wrap: wrap; }}
    .hero-input-wrap {{ flex: 1; min-width: 200px; position: relative; }}
    .hero-input-icon {{
      position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
      color: #94a3b8; font-size: 1rem;
    }}
    .hero-input {{
      width: 100%; padding: 14px 14px 14px 42px; border-radius: 12px;
      border: 1.5px solid #e2e8f0; background: #fff; font-size: 0.95rem;
      font-family: 'DM Sans', sans-serif; outline: none;
      box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }}
    .hero-input:focus {{ border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }}
    .btn-hero {{
      background: #2563EB; color: #fff; border: none; border-radius: 12px;
      padding: 14px 28px; font-size: 1rem; font-weight: 700;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      box-shadow: 0 4px 14px rgba(37,99,235,0.3); transition: all 0.15s;
      white-space: nowrap;
    }}
    .btn-hero:hover {{ background: #1d4ed8; transform: translateY(-1px); }}
    .hero-avatars {{ display: flex; align-items: center; gap: 12px; font-size: 0.875rem; color: #64748b; }}
    .avatar-stack {{ display: flex; }}
    .avatar {{
      width: 32px; height: 32px; border-radius: 50%; border: 2.5px solid #f6f6f8;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.62rem; font-weight: 700; color: #fff; margin-left: -9px;
    }}
    .avatar:first-child {{ margin-left: 0; }}

    /* MOCK */
    .mock-outer {{ position: relative; }}
    .mock-glow {{
      position: absolute; inset: -20px; background: rgba(37,99,235,0.1);
      filter: blur(80px); border-radius: 50%; pointer-events: none;
    }}
    .mock-card {{
      position: relative; background: #fff; border: 1px solid #e2e8f0;
      border-radius: 24px; padding: 8px;
      box-shadow: 0 24px 64px -16px rgba(0,0,0,0.16);
    }}
    .mock-inner {{ background: #f8fafc; border-radius: 18px; border: 1px solid #f1f5f9; padding: 18px; }}
    .mock-topbar {{
      background: #fff; border-radius: 12px; padding: 12px 16px;
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .mock-sync {{
      background: #2563EB; color: #fff; font-size: 0.72rem; font-weight: 700;
      padding: 7px 14px; border-radius: 9px;
    }}
    .mock-stats {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; margin-bottom: 12px; }}
    .mock-stat {{
      background: #fff; border-radius: 14px; padding: 14px;
      border: 1px solid #f1f5f9; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .mock-num {{ font-size: 1.6rem; font-weight: 700; color: #0f172a; line-height: 1; }}
    .mock-lbl {{ font-size: 0.62rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 3px; }}
    .mock-row {{
      background: #fff; border-radius: 14px; padding: 11px 14px;
      display: flex; align-items: center; justify-content: space-between;
      margin-bottom: 8px; border: 1px solid #f1f5f9;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .mock-row:last-child {{ margin-bottom: 0; }}
    .mock-co {{ display: flex; align-items: center; gap: 10px; }}
    .mock-logo {{
      width: 30px; height: 30px; border-radius: 9px; background: #f1f5f9;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.72rem; font-weight: 700; color: #475569;
    }}
    .mock-name {{ font-size: 0.875rem; font-weight: 600; color: #0f172a; }}
    .mock-role {{ font-size: 0.7rem; color: #94a3b8; }}
    .badge-iv {{ background: #fef3c7; color: #d97706; padding: 3px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; }}
    .badge-of {{ background: #dcfce7; color: #15803d; padding: 3px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; }}

    /* PROOF */
    .proof {{ padding: 36px 2.5rem; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; background: rgba(248,250,252,0.7); }}
    .proof-inner {{ max-width: 1280px; margin: 0 auto; text-align: center; }}
    .proof-lbl {{ font-size: 0.7rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 24px; }}
    .proof-logos {{ display: flex; justify-content: center; gap: 28px; flex-wrap: wrap; opacity: 0.3; }}
    .proof-logo {{ width: 88px; height: 26px; background: #94a3b8; border-radius: 4px; }}

    /* FEATURES */
    .features {{ padding: 88px 2.5rem; max-width: 1280px; margin: 0 auto; }}
    .sec-title {{ font-size: clamp(1.9rem, 3vw, 2.6rem); font-weight: 700; color: #0f172a; text-align: center; margin-bottom: 10px; letter-spacing: -0.5px; }}
    .sec-sub {{ font-size: 1rem; color: #64748b; text-align: center; margin-bottom: 52px; line-height: 1.65; max-width: 600px; margin-left: auto; margin-right: auto; }}
    .feat-grid {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 24px; }}
    @media(max-width:768px){{ .feat-grid {{ grid-template-columns: 1fr; }} }}
    .feat-card {{
      background: #fff; border: 1px solid #e2e8f0; border-radius: 20px;
      padding: 34px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); transition: all 0.22s;
    }}
    .feat-card:hover {{ box-shadow: 0 16px 40px -10px rgba(37,99,235,0.1); border-color: rgba(37,99,235,0.28); transform: translateY(-2px); }}
    .feat-icon {{ width: 48px; height: 48px; border-radius: 13px; background: rgba(37,99,235,0.08); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; margin-bottom: 18px; }}
    .feat-title {{ font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 10px; }}
    .feat-desc {{ font-size: 0.875rem; color: #64748b; line-height: 1.65; }}

    /* STATS */
    .stats {{ background: #0f172a; border-radius: 24px; margin: 0 2rem 64px; padding: 64px 2.5rem; }}
    .stats-inner {{ max-width: 1280px; margin: 0 auto; display: grid; grid-template-columns: repeat(4,1fr); gap: 32px; text-align: center; }}
    @media(max-width:768px){{ .stats-inner {{ grid-template-columns: repeat(2,1fr); }} }}
    .stat-big {{ font-size: clamp(2rem, 4vw, 3.2rem); font-weight: 700; color: #fff; line-height: 1; }}
    .stat-lbl {{ font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; }}

    /* CTA */
    .cta {{ background: rgba(37,99,235,0.04); padding: 88px 2.5rem; text-align: center; }}
    .cta-inner {{ max-width: 700px; margin: 0 auto; }}
    .cta h2 {{ font-size: clamp(2rem, 4vw, 3rem); font-weight: 700; color: #0f172a; margin-bottom: 16px; letter-spacing: -1px; }}
    .cta p {{ font-size: 1.05rem; color: #64748b; margin-bottom: 40px; line-height: 1.7; }}
    .cta-btns {{ display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }}
    .btn-cta-primary {{
      background: #2563EB; color: #fff; border: none; border-radius: 12px;
      padding: 14px 32px; font-size: 1rem; font-weight: 700;
      cursor: pointer; font-family: 'DM Sans', sans-serif;
      box-shadow: 0 4px 14px rgba(37,99,235,0.3); transition: all 0.15s;
    }}
    .btn-cta-primary:hover {{ background: #1d4ed8; }}
    .btn-cta-secondary {{
      background: #fff; color: #0f172a; border: 1.5px solid #e2e8f0; border-radius: 12px;
      padding: 14px 32px; font-size: 1rem; font-weight: 700;
      cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s;
    }}
    .btn-cta-secondary:hover {{ background: #f8fafc; }}

    /* FOOTER */
    .footer {{ background: #fff; border-top: 1px solid #e2e8f0; padding: 64px 2.5rem 32px; }}
    .footer-grid {{ max-width: 1280px; margin: 0 auto; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 48px; margin-bottom: 48px; }}
    @media(max-width:768px){{ .footer-grid {{ grid-template-columns: 1fr 1fr; }} }}
    .f-logo {{ display: flex; align-items: center; gap: 8px; font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 14px; }}
    .f-desc {{ font-size: 0.875rem; color: #64748b; line-height: 1.65; max-width: 240px; }}
    .f-col-title {{ font-size: 0.875rem; font-weight: 700; color: #0f172a; margin-bottom: 18px; }}
    .f-links {{ display: flex; flex-direction: column; gap: 11px; }}
    .f-link {{ font-size: 0.875rem; color: #64748b; text-decoration: none; }}
    .f-link:hover {{ color: #2563EB; }}
    .f-bottom {{
      max-width: 1280px; margin: 0 auto; padding-top: 24px;
      border-top: 1px solid #e2e8f0; display: flex;
      justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;
    }}
    .f-copy {{ font-size: 0.8rem; color: #94a3b8; }}
    </style>

    <!-- NAV -->
    <nav class="nav">
      <a class="nav-logo" href="?">
        <span class="nav-logo-icon">⇄</span> CareerSync
      </a>
      <div class="nav-btns">
        <a class="btn-login" href="?nav=login">Log In</a>
        <a class="btn-signup" href="?nav=signup">Get Started Free</a>
      </div>
    </nav>

    <!-- HERO -->
    <section class="hero">
      <div>
        <div class="hero-badge"><span class="hero-dot"></span> AI-Powered Job Hunting</div>
        <h1>Automated Job Application <span>Tracker</span> &amp; Recruiter Research</h1>
        <p>Streamline your job search with CareerSync. Automatically track applications,
          research recruiters, and generate AI-powered outreach emails in one professional dashboard.</p>
        <div class="hero-input-row">
          <div class="hero-input-wrap">
            <span class="hero-input-icon">✉️</span>
            <input class="hero-input" placeholder="Enter your work email" type="email"/>
          </div>
          <a class="btn-hero" href="?nav=signup">Start Tracking</a>
        </div>
        <div class="hero-avatars">
          <div class="avatar-stack">
            <div class="avatar" style="background:#6366f1;">JK</div>
            <div class="avatar" style="background:#0ea5e9;">AM</div>
            <div class="avatar" style="background:#f59e0b;">SR</div>
          </div>
          <span>Joined by 10k+ active job seekers</span>
        </div>
      </div>
      <div class="mock-outer">
        <div class="mock-glow"></div>
        <div class="mock-card">
          <div class="mock-inner">
            <div class="mock-topbar">
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="color:#2563EB;font-weight:700;">⇄</span>
                <span style="font-weight:700;font-size:0.875rem;">CareerSync</span>
              </div>
              <span class="mock-sync">Sync Gmail</span>
            </div>
            <div class="mock-stats">
              <div class="mock-stat"><div class="mock-num">24</div><div class="mock-lbl">Applications</div></div>
              <div class="mock-stat"><div class="mock-num">6</div><div class="mock-lbl">Interviews</div></div>
              <div class="mock-stat"><div class="mock-num">18</div><div class="mock-lbl">Recruiters</div></div>
            </div>
            <div class="mock-row">
              <div class="mock-co">
                <div class="mock-logo">G</div>
                <div><div class="mock-name">Google</div><div class="mock-role">Software Engineer</div></div>
              </div>
              <span class="badge-iv">Interview</span>
            </div>
            <div class="mock-row">
              <div class="mock-co">
                <div class="mock-logo">S</div>
                <div><div class="mock-name">Stripe</div><div class="mock-role">Full Stack Engineer</div></div>
              </div>
              <span class="badge-of">Offer</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SOCIAL PROOF -->
    <div class="proof">
      <div class="proof-inner">
        <div class="proof-lbl">Trusted by candidates hired at</div>
        <div class="proof-logos">
          <div class="proof-logo"></div><div class="proof-logo"></div>
          <div class="proof-logo"></div><div class="proof-logo"></div>
          <div class="proof-logo"></div>
        </div>
      </div>
    </div>

    <!-- FEATURES -->
    <div id="features" class="features">
      <div class="sec-title">Powerful Features for Modern Job Seekers</div>
      <div class="sec-sub">Everything you need to land your next role faster, without the manual spreadsheet maintenance.</div>
      <div class="feat-grid">
        <div class="feat-card">
          <div class="feat-icon">📬</div>
          <div class="feat-title">Gmail Sync</div>
          <div class="feat-desc">Automatically pull job applications directly from your inbox. No manual entry, no missed opportunities.</div>
        </div>
        <div class="feat-card">
          <div class="feat-icon">🧠</div>
          <div class="feat-title">AI Enrichment</div>
          <div class="feat-desc">Get deep insights on companies and recruiters. Know their recent funding, news, and interview style.</div>
        </div>
        <div class="feat-card">
          <div class="feat-icon">✉️</div>
          <div class="feat-title">AI Email Generator</div>
          <div class="feat-desc">Generate personalized, high-conversion outreach emails in seconds tailored to the role and recruiter.</div>
        </div>
      </div>
    </div>

    <!-- STATS -->
    <div class="stats">
      <div class="stats-inner">
        <div><div class="stat-big">10k+</div><div class="stat-lbl">Active Users</div></div>
        <div><div class="stat-big">500k+</div><div class="stat-lbl">Apps Tracked</div></div>
        <div><div class="stat-big">25k+</div><div class="stat-lbl">Interviews</div></div>
        <div><div class="stat-big">94%</div><div class="stat-lbl">Success Rate</div></div>
      </div>
    </div>

    <!-- CTA -->
    <div class="cta">
      <div class="cta-inner">
        <h2>Ready to land your dream role?</h2>
        <p>Stop manually updating spreadsheets. Let CareerSync handle the tracking while you focus on the interview.</p>
        <div class="cta-btns">
          <a class="btn-cta-primary" href="?nav=signup">Get Started for Free</a>
          <a class="btn-cta-secondary" href="?nav=login">View Demo</a>
        </div>
      </div>
    </div>

    <!-- FOOTER -->
    <div class="footer">
      <div class="footer-grid">
        <div>
          <div class="f-logo">⇄ CareerSync</div>
          <div class="f-desc">The modern operating system for your professional career growth and job hunt.</div>
        </div>
        <div>
          <div class="f-col-title">Product</div>
          <div class="f-links">
            <a class="f-link" href="#features">Features</a>
            <a class="f-link" href="#">Pricing</a>
            <a class="f-link" href="#">Integrations</a>
            <a class="f-link" href="#">Updates</a>
          </div>
        </div>
        <div>
          <div class="f-col-title">Resources</div>
          <div class="f-links">
            <a class="f-link" href="#">Blog</a>
            <a class="f-link" href="#">Help Center</a>
            <a class="f-link" href="#">Job Search Tips</a>
            <a class="f-link" href="#">Resume Guide</a>
          </div>
        </div>
        <div>
          <div class="f-col-title">Legal</div>
          <div class="f-links">
            <a class="f-link" href="#">Privacy</a>
            <a class="f-link" href="#">Terms</a>
            <a class="f-link" href="#">Security</a>
          </div>
        </div>
      </div>
      <div class="f-bottom">
        <span class="f-copy">© 2026 CareerSync Inc. All rights reserved.</span>
        <div style="display:flex;gap:20px;">
          <a class="f-link" href="#">Cookies</a>
          <a class="f-link" href="#">Accessibility</a>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "login":
    # Re-enable stButton for login/register pages
    st.markdown("""
    <style>
    .stButton{display:flex!important;}
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
      background:#f6f6f8!important;}
    .block-container{padding:2rem 1rem!important;max-width:460px!important;margin:0 auto!important;}
    div[data-testid="stTextInput"] input{border-radius:8px!important;border:1px solid #cbd5e1!important;
      background:#fff!important;padding:12px 16px!important;color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;
      box-shadow:0 0 0 2px rgba(37,99,235,0.12)!important;}
    div[data-testid="stTextInput"] label{font-size:0.875rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{width:100%!important;border-radius:8px!important;
      background:#2563EB!important;padding:12px!important;font-size:0.9rem!important;
      font-weight:700!important;color:#fff!important;border:none!important;}
    div[data-testid="stFormSubmitButton"] button:hover{background:#1d4ed8!important;}
    div.stButton>button{background:transparent!important;color:#2563EB!important;border:none!important;
      padding:4px!important;font-size:0.875rem!important;font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:40px 0 28px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#2563EB;
          display:flex;align-items:center;justify-content:center;font-size:20px;">💼</div>
        <span style="font-size:1.5rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:20px 0 6px;">Welcome back</h2>
      <p style="font-size:0.875rem;color:#64748b;margin:0;">Please enter your details to sign in</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email    = st.text_input("Email address", placeholder="name@company.com")
        password = st.text_input("Password", placeholder="••••••••", type="password")
        sub      = st.form_submit_button("Sign in", use_container_width=True)

    if sub:
        if not email or not password:
            st.error("Please enter your email and password.")
        elif not supabase_ready():
            st.error("❌ Supabase not configured.")
        else:
            user = login_user(email, password)
            if user:
                _set_login(user)
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error("❌ Invalid email or password.")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _, bc, _ = st.columns([1, 2, 1])
    with bc:
        if st.button("Don't have an account? Sign up →", key="go_reg", use_container_width=True):
            go("register"); st.rerun()
    if st.button("← Back to home", key="back_home"):
        go("landing"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# REGISTER PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "register":
    st.markdown("""
    <style>
    .stButton{display:flex!important;}
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
      background:#f6f6f8!important;}
    .block-container{padding:2rem 1rem!important;max-width:520px!important;margin:0 auto!important;}
    div[data-testid="stTextInput"] input{border-radius:8px!important;border:1px solid #cbd5e1!important;
      background:#fff!important;padding:12px 16px!important;color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;
      box-shadow:0 0 0 2px rgba(37,99,235,.12)!important;}
    div[data-testid="stTextInput"] label{font-size:0.875rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{width:100%!important;border-radius:8px!important;
      background:#2563EB!important;padding:12px!important;font-size:0.9rem!important;
      font-weight:700!important;color:#fff!important;border:none!important;}
    div[data-testid="stFormSubmitButton"] button:hover{background:#1d4ed8!important;}
    div.stButton>button{background:transparent!important;color:#2563EB!important;border:none!important;
      padding:4px!important;font-size:0.875rem!important;font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:32px 0 20px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#2563EB;
          display:flex;align-items:center;justify-content:center;font-size:20px;">💼</div>
        <span style="font-size:1.5rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:16px 0 6px;">Create your account</h2>
      <p style="font-size:0.875rem;color:#64748b;margin:0;">Each account has its own private dashboard synced to your Gmail</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        name  = st.text_input("Full name",     placeholder="John Smith")
        r_em  = st.text_input("Email address", placeholder="name@company.com")
        r_pw  = st.text_input("Password",      placeholder="Create a password (min 6 chars)", type="password")
        r_pw2 = st.text_input("Confirm password", placeholder="Repeat your password", type="password")
        st.markdown("""
        <div style="margin:16px 0 8px;padding-top:16px;border-top:1px solid #f1f5f9;">
          <div style="font-size:0.78rem;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">
            📬 Gmail Sync Credentials</div>
          <p style="font-size:0.78rem;color:#94a3b8;margin:0 0 8px;">
            CareerSync syncs <strong>your</strong> Gmail privately.
            <a href="https://myaccount.google.com/apppasswords" target="_blank"
               style="color:#2563EB;font-weight:600;">Get App Password →</a>
            App: <b>Mail</b> · Device: <b>Other</b> → name it <b>CareerSync</b>
          </p>
        </div>
        """, unsafe_allow_html=True)
        gm_acc  = st.text_input("Your Gmail address", placeholder="yourname@gmail.com")
        gm_pass = st.text_input("Your Gmail App Password",
                                placeholder="e.g. abcd efgh ijkl mnop (16 chars)",
                                type="password")
        sub = st.form_submit_button("Create Account", use_container_width=True)

    if sub:
        if r_pw != r_pw2:
            st.error("❌ Passwords don't match.")
        elif not supabase_ready():
            st.error("❌ Supabase not configured.")
        else:
            ok, msg = register_user(name=name, email=r_em, password=r_pw,
                                    gmail_account=gm_acc, gmail_app_password=gm_pass)
            if ok:
                st.success("✅ Account created! Signing you in...")
                user = login_user(r_em, r_pw)
                if user:
                    _set_login(user)
                    st.switch_page("pages/1_Dashboard.py")
            else:
                st.error(f"❌ {msg}")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _, bc2, _ = st.columns([1, 2, 1])
    with bc2:
        if st.button("Already have an account? Sign in →", key="go_login", use_container_width=True):
            go("login"); st.rerun()
    if st.button("← Back to home", key="back_home_r"):
        go("landing"); st.rerun()
    st.markdown("""
    <div style="text-align:center;padding:20px 0;font-size:0.75rem;color:#94a3b8;">
      © 2026 CareerSync Inc. All rights reserved.</div>
    """, unsafe_allow_html=True)