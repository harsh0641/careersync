"""
app.py — CareerSync Landing + Login + Register
Pure Streamlit landing — no iframe, no sandbox issues.
All buttons work. No extra buttons at bottom.
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

_restore_session()

if st.session_state.get("user"):
    st.switch_page("pages/1_Dashboard.py")
    st.stop()

if "auth_view" not in st.session_state:
    st.session_state.auth_view = "landing"

# ── Hide Streamlit chrome ──────────────────────────────────────────────────────
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
}
.block-container{padding:0!important;max-width:100%!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE — pure Streamlit, exact HTML design
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.auth_view == "landing":

    # ── Global landing styles ──────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Nav */
    .cs-header{position:sticky;top:0;z-index:100;background:rgba(246,246,248,0.9);
      backdrop-filter:blur(12px);border-bottom:1px solid #e2e8f0;
      padding:0 2rem;height:64px;display:flex;align-items:center;justify-content:space-between;}
    .cs-logo{display:flex;align-items:center;gap:8px;font-size:1.2rem;font-weight:700;color:#0f172a;}
    .cs-logo-icon{color:#2563EB;font-size:1.6rem;line-height:1;}
    .cs-nav-links{display:flex;align-items:center;gap:32px;}
    .cs-nav-link{font-size:0.875rem;font-weight:500;color:#475569;text-decoration:none;}
    .cs-nav-link:hover{color:#2563EB;}

    /* Hero */
    .hero-wrap{max-width:1280px;margin:0 auto;padding:80px 2rem 48px;
      display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center;}
    @media(max-width:900px){.hero-wrap{grid-template-columns:1fr;}}
    .hero-badge{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;
      border-radius:9999px;background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.2);
      font-size:0.72rem;font-weight:700;color:#2563EB;text-transform:uppercase;
      letter-spacing:0.8px;margin-bottom:20px;}
    .hero-dot{width:6px;height:6px;border-radius:50%;background:#2563EB;
      display:inline-block;animation:pulse 2s infinite;}
    @keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
    .hero-title{font-size:clamp(2.2rem,5vw,3.75rem);font-weight:700;color:#0f172a;
      line-height:1.05;letter-spacing:-1.5px;margin-bottom:20px;}
    .hero-title .accent{color:#2563EB;}
    .hero-sub{font-size:1.1rem;color:#64748b;line-height:1.7;margin-bottom:36px;max-width:520px;}
    .hero-input-row{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap;}
    .hero-input-wrap{flex:1;min-width:200px;position:relative;}
    .hero-input-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);
      color:#94a3b8;font-size:1.2rem;}
    .hero-input{width:100%;padding:14px 14px 14px 44px;border-radius:12px;
      border:1px solid #e2e8f0;background:#fff;font-size:0.95rem;
      font-family:'DM Sans',sans-serif;outline:none;box-sizing:border-box;}
    .hero-input:focus{border-color:#2563EB;box-shadow:0 0 0 3px rgba(37,99,235,0.12);}
    .hero-avatars{display:flex;align-items:center;gap:12px;font-size:0.875rem;color:#64748b;}
    .avatar-stack{display:flex;}
    .avatar{width:32px;height:32px;border-radius:50%;border:2px solid #fff;
      display:flex;align-items:center;justify-content:center;
      font-size:0.68rem;font-weight:700;color:#fff;margin-left:-8px;}
    .avatar:first-child{margin-left:0;}

    /* Mock dashboard */
    .mock-wrap{position:relative;}
    .mock-glow{position:absolute;inset:0;background:rgba(37,99,235,0.15);
      filter:blur(80px);border-radius:50%;pointer-events:none;}
    .mock-card{position:relative;background:#fff;border:1px solid #e2e8f0;
      border-radius:20px;padding:8px;box-shadow:0 25px 50px -12px rgba(0,0,0,0.15);}
    .mock-inner{background:#f8fafc;border-radius:14px;border:1px solid #f1f5f9;padding:16px;}
    .mock-topbar{background:#fff;border-radius:10px;padding:12px 16px;
      display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;
      box-shadow:0 1px 3px rgba(0,0,0,0.06);}
    .mock-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px;}
    .mock-stat{background:#fff;border-radius:12px;padding:12px;
      border:1px solid #f1f5f9;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
    .mock-stat-num{font-size:1.5rem;font-weight:700;color:#0f172a;line-height:1;}
    .mock-stat-label{font-size:0.65rem;color:#94a3b8;font-weight:600;
      text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;}
    .mock-row{background:#fff;border-radius:12px;padding:10px 12px;
      display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;
      border:1px solid #f1f5f9;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
    .mock-row:last-child{margin-bottom:0;}
    .mock-company{display:flex;align-items:center;gap:8px;}
    .mock-logo{width:28px;height:28px;border-radius:8px;background:#f1f5f9;
      display:flex;align-items:center;justify-content:center;
      font-size:0.7rem;font-weight:700;color:#475569;}
    .mock-name{font-size:0.875rem;font-weight:600;color:#0f172a;}
    .mock-role{font-size:0.72rem;color:#94a3b8;}
    .badge-interview{background:#fef3c7;color:#d97706;padding:3px 10px;
      border-radius:20px;font-size:0.68rem;font-weight:700;}
    .badge-offer{background:#dcfce7;color:#15803d;padding:3px 10px;
      border-radius:20px;font-size:0.68rem;font-weight:700;}

    /* Social proof */
    .proof-section{padding:40px 2rem;border-top:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;
      background:rgba(248,250,252,0.5);}
    .proof-inner{max-width:1280px;margin:0 auto;text-align:center;}
    .proof-label{font-size:0.72rem;font-weight:700;color:#94a3b8;
      text-transform:uppercase;letter-spacing:1px;margin-bottom:28px;}
    .proof-logos{display:flex;justify-content:center;gap:32px;flex-wrap:wrap;opacity:0.4;}
    .proof-logo{width:96px;height:28px;background:#94a3b8;border-radius:4px;}

    /* Features */
    .features-section{padding:80px 2rem;max-width:1280px;margin:0 auto;}
    .section-title{font-size:clamp(1.8rem,3vw,2.5rem);font-weight:700;color:#0f172a;
      text-align:center;margin-bottom:12px;}
    .section-sub{font-size:1rem;color:#64748b;text-align:center;margin-bottom:48px;}
    .features-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
    @media(max-width:768px){.features-grid{grid-template-columns:1fr;}}
    .feature-card{background:#fff;border:1px solid #e2e8f0;border-radius:20px;
      padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.04);
      transition:box-shadow 0.2s,border-color 0.2s;}
    .feature-card:hover{box-shadow:0 10px 25px -5px rgba(37,99,235,0.08);border-color:rgba(37,99,235,0.3);}
    .feature-icon-wrap{width:48px;height:48px;border-radius:12px;background:rgba(37,99,235,0.08);
      display:flex;align-items:center;justify-content:center;margin-bottom:20px;font-size:1.4rem;}
    .feature-title{font-size:1.1rem;font-weight:700;color:#0f172a;margin-bottom:10px;}
    .feature-desc{font-size:0.875rem;color:#64748b;line-height:1.65;}

    /* Stats */
    .stats-section{background:#0f172a;border-radius:24px;margin:0 2rem 64px;padding:64px 2rem;}
    .stats-inner{max-width:1280px;margin:0 auto;
      display:grid;grid-template-columns:repeat(4,1fr);gap:32px;text-align:center;}
    @media(max-width:768px){.stats-inner{grid-template-columns:repeat(2,1fr);}}
    .stat-big{font-size:clamp(2rem,4vw,3rem);font-weight:700;color:#fff;line-height:1;}
    .stat-label{font-size:0.72rem;color:#64748b;font-weight:600;text-transform:uppercase;
      letter-spacing:1px;margin-top:8px;}

    /* CTA */
    .cta-section{background:rgba(37,99,235,0.04);padding:80px 2rem;text-align:center;}
    .cta-inner{max-width:800px;margin:0 auto;}
    .cta-title{font-size:clamp(2rem,4vw,3rem);font-weight:700;color:#0f172a;margin-bottom:16px;}
    .cta-sub{font-size:1.1rem;color:#64748b;margin-bottom:40px;line-height:1.7;}
    .cta-btns{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;}

    /* Footer */
    .footer-wrap{background:#fff;border-top:1px solid #e2e8f0;padding:64px 2rem 32px;}
    .footer-inner{max-width:1280px;margin:0 auto;}
    .footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px;}
    @media(max-width:768px){.footer-grid{grid-template-columns:1fr 1fr;}}
    .footer-logo{display:flex;align-items:center;gap:8px;margin-bottom:16px;
      font-size:1.15rem;font-weight:700;color:#0f172a;}
    .footer-desc{font-size:0.875rem;color:#64748b;line-height:1.65;max-width:260px;}
    .footer-col-title{font-size:0.875rem;font-weight:700;color:#0f172a;margin-bottom:20px;}
    .footer-links{display:flex;flex-direction:column;gap:12px;}
    .footer-link{font-size:0.875rem;color:#64748b;text-decoration:none;}
    .footer-link:hover{color:#2563EB;}
    .footer-bottom{padding-top:28px;border-top:1px solid #e2e8f0;
      display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;}
    .footer-copy{font-size:0.8rem;color:#94a3b8;}

    /* Streamlit button overrides for landing */
    div.stButton>button{
      border-radius:12px!important;font-weight:700!important;
      font-family:'DM Sans',sans-serif!important;
      font-size:0.95rem!important;
      transition:all 0.2s!important;
      white-space:nowrap!important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="cs-header">
      <div class="cs-logo">
        <span class="cs-logo-icon">⇄</span> CareerSync
      </div>
      <div class="cs-nav-links">
        <a class="cs-nav-link" href="#features">Features</a>
        <a class="cs-nav-link" href="#how-it-works">How it Works</a>
        <a class="cs-nav-link" href="#pricing">Pricing</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav login/signup buttons
    _, nav_sp, nav_l, nav_s = st.columns([6, 1, 0.8, 1])
    with nav_l:
        if st.button("Log In", key="nav_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()
    with nav_s:
        if st.button("Get Started Free", key="nav_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()

    # ── Hero ────────────────────────────────────────────────────────────────
    hero_left, hero_right = st.columns([1, 1], gap="large")

    with hero_left:
        st.markdown("""
        <div style="padding:48px 0 0 2rem;">
          <div class="hero-badge"><span class="hero-dot"></span> AI-Powered Job Hunting</div>
          <div class="hero-title">
            Automated Job Application
            <span class="accent">Tracker</span> &amp; Recruiter Research
          </div>
          <div class="hero-sub">
            Streamline your job search with CareerSync. Automatically track applications,
            research recruiters, and generate AI-powered outreach emails in one professional dashboard.
          </div>
          <div class="hero-input-row">
            <div class="hero-input-wrap">
              <span class="hero-input-icon">✉️</span>
              <input class="hero-input" placeholder="Enter your work email" type="email"/>
            </div>
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
        """, unsafe_allow_html=True)

        st.markdown("<div style='padding:0 0 0 2rem;margin-top:24px;'>", unsafe_allow_html=True)
        hb1, hb2 = st.columns([1.3, 1])
        with hb1:
            if st.button("Start Tracking", key="hero_start", use_container_width=True, type="primary"):
                st.session_state.auth_view = "register"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with hero_right:
        st.markdown("""
        <div class="mock-wrap" style="padding:48px 2rem 0 0;">
          <div class="mock-glow"></div>
          <div class="mock-card">
            <div class="mock-inner">
              <div class="mock-topbar">
                <div style="display:flex;align-items:center;gap:8px;">
                  <span style="color:#2563EB;font-size:1.1rem;">⇄</span>
                  <span style="font-weight:700;font-size:0.875rem;color:#0f172a;">CareerSync</span>
                </div>
                <span style="background:#2563EB;color:#fff;font-size:0.72rem;font-weight:700;
                  padding:6px 12px;border-radius:8px;">Sync Gmail</span>
              </div>
              <div class="mock-stats">
                <div class="mock-stat">
                  <div class="mock-stat-num">24</div>
                  <div class="mock-stat-label">Applications</div>
                </div>
                <div class="mock-stat">
                  <div class="mock-stat-num">6</div>
                  <div class="mock-stat-label">Interviews</div>
                </div>
                <div class="mock-stat">
                  <div class="mock-stat-num">18</div>
                  <div class="mock-stat-label">Recruiters</div>
                </div>
              </div>
              <div class="mock-row">
                <div class="mock-company">
                  <div class="mock-logo">G</div>
                  <div>
                    <div class="mock-name">Google</div>
                    <div class="mock-role">Software Engineer</div>
                  </div>
                </div>
                <span class="badge-interview">Interview</span>
              </div>
              <div class="mock-row">
                <div class="mock-company">
                  <div class="mock-logo">S</div>
                  <div>
                    <div class="mock-name">Stripe</div>
                    <div class="mock-role">Full Stack Engineer</div>
                  </div>
                </div>
                <span class="badge-offer">Offer</span>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Social Proof ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="proof-section">
      <div class="proof-inner">
        <div class="proof-label">Trusted by candidates hired at</div>
        <div class="proof-logos">
          <div class="proof-logo"></div>
          <div class="proof-logo"></div>
          <div class="proof-logo"></div>
          <div class="proof-logo"></div>
          <div class="proof-logo"></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Features ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div id="features" class="features-section">
      <div class="section-title">Powerful Features for Modern Job Seekers</div>
      <div class="section-sub">Everything you need to land your next role faster, without the manual spreadsheet maintenance.</div>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon-wrap">📬</div>
          <div class="feature-title">Gmail Sync</div>
          <div class="feature-desc">Automatically pull job applications directly from your inbox. No manual entry, no missed opportunities.</div>
        </div>
        <div class="feature-card">
          <div class="feature-icon-wrap">🧠</div>
          <div class="feature-title">AI Enrichment</div>
          <div class="feature-desc">Get deep insights on companies and recruiters. Know their recent funding, news, and interview style.</div>
        </div>
        <div class="feature-card">
          <div class="feature-icon-wrap">✉️</div>
          <div class="feature-title">AI Email Generator</div>
          <div class="feature-desc">Generate personalized, high-conversion outreach emails in seconds tailored to the role and recruiter.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div id="how-it-works" class="stats-section">
      <div class="stats-inner">
        <div><div class="stat-big">10k+</div><div class="stat-label">Active Users</div></div>
        <div><div class="stat-big">500k+</div><div class="stat-label">Apps Tracked</div></div>
        <div><div class="stat-big">25k+</div><div class="stat-label">Interviews</div></div>
        <div><div class="stat-big">94%</div><div class="stat-label">Success Rate</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <div id="pricing" class="cta-section">
      <div class="cta-inner">
        <div class="cta-title">Ready to land your dream role?</div>
        <div class="cta-sub">Stop manually updating spreadsheets. Let CareerSync handle the tracking while you focus on the interview.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, cta1, cta2, _ = st.columns([2, 1.5, 1.5, 2])
    with cta1:
        if st.button("Get Started for Free", key="cta_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()
    with cta2:
        if st.button("View Demo", key="cta_demo", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="footer-wrap">
      <div class="footer-inner">
        <div class="footer-grid">
          <div>
            <div class="footer-logo">⇄ CareerSync</div>
            <div class="footer-desc">The modern operating system for your professional career growth and job hunt.</div>
          </div>
          <div>
            <div class="footer-col-title">Product</div>
            <div class="footer-links">
              <a class="footer-link" href="#features">Features</a>
              <a class="footer-link" href="#pricing">Pricing</a>
              <a class="footer-link" href="#">Integrations</a>
              <a class="footer-link" href="#">Updates</a>
            </div>
          </div>
          <div>
            <div class="footer-col-title">Resources</div>
            <div class="footer-links">
              <a class="footer-link" href="#">Blog</a>
              <a class="footer-link" href="#">Help Center</a>
              <a class="footer-link" href="#">Job Search Tips</a>
              <a class="footer-link" href="#">Resume Guide</a>
            </div>
          </div>
          <div>
            <div class="footer-col-title">Legal</div>
            <div class="footer-links">
              <a class="footer-link" href="#">Privacy</a>
              <a class="footer-link" href="#">Terms</a>
              <a class="footer-link" href="#">Security</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <span class="footer-copy">© 2026 CareerSync Inc. All rights reserved.</span>
          <div style="display:flex;gap:24px;">
            <a class="footer-link" href="#">Cookies</a>
            <a class="footer-link" href="#">Accessibility</a>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "login":
    st.markdown("""
    <style>
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
        password = st.text_input("Password",      placeholder="••••••••", type="password")
        sub      = st.form_submit_button("Sign in", use_container_width=True)

    if sub:
        if not email or not password:
            st.error("Please enter your email and password.")
        elif not supabase_ready():
            st.error("❌ Supabase not configured. Check Streamlit secrets.")
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
            st.session_state.auth_view = "register"; st.rerun()
    if st.button("← Back to home", key="back_home"):
        st.session_state.auth_view = "landing"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# REGISTER PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "register":
    st.markdown("""
    <style>
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
        name  = st.text_input("Full name",        placeholder="John Smith")
        r_em  = st.text_input("Email address",    placeholder="name@company.com")
        r_pw  = st.text_input("Password",         placeholder="Create a password (min 6 chars)", type="password")
        r_pw2 = st.text_input("Confirm password", placeholder="Repeat your password",            type="password")
        st.markdown("""
        <div style="margin:16px 0 8px;padding-top:16px;border-top:1px solid #f1f5f9;">
          <div style="font-size:0.78rem;font-weight:700;color:#374151;text-transform:uppercase;
                      letter-spacing:.06em;margin-bottom:6px;">📬 Gmail Sync Credentials</div>
          <p style="font-size:0.78rem;color:#94a3b8;margin:0 0 8px;">
            CareerSync syncs <strong>your</strong> Gmail privately.
            <a href="https://myaccount.google.com/apppasswords" target="_blank"
               style="color:#2563EB;font-weight:600;">Get App Password →</a>
            App: <b>Mail</b> · Device: <b>Other</b> → name it <b>CareerSync</b>
          </p>
        </div>
        """, unsafe_allow_html=True)
        gm_acc  = st.text_input("Your Gmail address",      placeholder="yourname@gmail.com")
        gm_pass = st.text_input("Your Gmail App Password",
                                placeholder="e.g. abcd efgh ijkl mnop (16 chars)",
                                type="password")
        sub = st.form_submit_button("Create Account", use_container_width=True)

    if sub:
        if r_pw != r_pw2:
            st.error("❌ Passwords don't match.")
        elif not supabase_ready():
            st.error("❌ Supabase not configured. Check Streamlit secrets.")
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
            st.session_state.auth_view = "login"; st.rerun()
    if st.button("← Back to home", key="back_home_r"):
        st.session_state.auth_view = "landing"; st.rerun()
    st.markdown("""<div style="text-align:center;padding:20px 0;font-size:0.75rem;color:#94a3b8;">
      © 2026 CareerSync Inc. All rights reserved.</div>""", unsafe_allow_html=True)