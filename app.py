"""
app.py — CareerSync Landing + Login + Register
Pure Streamlit — no iframe, no postMessage issues.
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

from auth import register_user, login_user, supabase_ready

# ── Persist login across refresh ───────────────────────────────────────────────
if "user_id" in st.session_state and "user" not in st.session_state:
    from auth import get_user_by_id
    user = get_user_by_id(st.session_state["user_id"])
    if user:
        st.session_state["user"] = user

# ── Redirect if already logged in ─────────────────────────────────────────────
if st.session_state.get("user"):
    st.switch_page("pages/1_Dashboard.py")
    st.stop()

if "auth_view" not in st.session_state:
    st.session_state.auth_view = "landing"

# ── Hide Streamlit chrome ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
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
# LANDING PAGE — pure Streamlit, no iframe
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.auth_view == "landing":

    st.markdown("""
    <style>
    /* Nav bar */
    .cs-nav{
      position:sticky;top:0;z-index:100;
      background:rgba(246,246,248,0.9);backdrop-filter:blur(12px);
      border-bottom:1px solid #e2e8f0;
      padding:0 2rem;height:64px;
      display:flex;align-items:center;justify-content:space-between;
    }
    .cs-nav-logo{display:flex;align-items:center;gap:8px;
      font-size:1.2rem;font-weight:700;color:#0f172a;}
    .cs-nav-logo-icon{color:#2563EB;font-size:1.5rem;}

    /* Hero */
    .hero-section{
      max-width:900px;margin:0 auto;
      padding:64px 2rem 48px;text-align:center;
    }
    .hero-badge{
      display:inline-flex;align-items:center;gap:6px;
      padding:6px 14px;border-radius:9999px;
      background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.2);
      font-size:0.72rem;font-weight:700;color:#2563EB;
      text-transform:uppercase;letter-spacing:0.8px;margin-bottom:24px;
    }
    .hero-dot{width:6px;height:6px;border-radius:50%;
      background:#2563EB;display:inline-block;animation:pulse 2s infinite;}
    @keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
    .hero-title{
      font-size:clamp(2rem,5vw,3.5rem);font-weight:700;
      color:#0f172a;line-height:1.1;letter-spacing:-1px;margin-bottom:20px;
    }
    .hero-title span{color:#2563EB;}
    .hero-sub{font-size:1.1rem;color:#64748b;max-width:600px;
      margin:0 auto 40px;line-height:1.7;}

    /* CTA buttons */
    .cta-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:48px;}

    /* Stats bar */
    .stats-bar{
      display:flex;justify-content:center;gap:48px;flex-wrap:wrap;
      padding:32px;background:#fff;border-radius:16px;
      border:1px solid #e2e8f0;max-width:700px;margin:0 auto 64px;
      box-shadow:0 4px 6px -1px rgba(0,0,0,0.04);
    }
    .stat-item{text-align:center;}
    .stat-num-big{font-size:2rem;font-weight:700;color:#0f172a;line-height:1;}
    .stat-label-sm{font-size:0.72rem;color:#64748b;font-weight:600;
      text-transform:uppercase;letter-spacing:0.7px;margin-top:4px;}

    /* Features */
    .features-section{max-width:1000px;margin:0 auto;padding:0 2rem 64px;}
    .features-title{text-align:center;font-size:1.8rem;font-weight:700;
      color:#0f172a;margin-bottom:8px;}
    .features-sub{text-align:center;color:#64748b;margin-bottom:40px;}
    .features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;}
    .feature-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;
      padding:28px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
    .feature-icon{width:44px;height:44px;background:rgba(37,99,235,0.08);
      border-radius:10px;display:flex;align-items:center;justify-content:center;
      font-size:1.3rem;margin-bottom:16px;}
    .feature-title{font-size:1rem;font-weight:700;color:#0f172a;margin-bottom:8px;}
    .feature-desc{font-size:0.875rem;color:#64748b;line-height:1.6;}

    /* Streamlit button overrides for landing */
    div.stButton>button{
      border-radius:12px!important;font-weight:700!important;
      font-family:'DM Sans',sans-serif!important;
      font-size:1rem!important;padding:14px 32px!important;
      transition:all 0.2s!important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Nav bar ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="cs-nav">
      <div class="cs-nav-logo">
        <span class="cs-nav-logo-icon">⇄</span>
        CareerSync
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav buttons — top right using columns trick
    nav_spacer, nav_login, nav_signup = st.columns([6, 1, 1])
    with nav_login:
        if st.button("Log In", key="nav_login_btn", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()
    with nav_signup:
        if st.button("Sign Up", key="nav_signup_btn", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()

    # ── Hero ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-section">
      <div class="hero-badge">
        <span class="hero-dot"></span>
        AI-Powered Job Hunting
      </div>
      <div class="hero-title">
        Automated Job Application<br>
        <span>Tracker</span> &amp; Recruiter Research
      </div>
      <div class="hero-sub">
        Streamline your job search with CareerSync. Automatically track applications,
        research recruiters, and generate AI-powered outreach emails in one professional dashboard.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA buttons ────────────────────────────────────────────────────────────
    _, cta1, cta2, _ = st.columns([2, 1.5, 1.5, 2])
    with cta1:
        if st.button("🚀 Start Tracking Free", key="hero_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()
    with cta2:
        if st.button("Sign In", key="hero_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()

    # ── Stats ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="max-width:700px;margin:32px auto;">
    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-num-big">10k+</div>
        <div class="stat-label-sm">Active Users</div>
      </div>
      <div class="stat-item">
        <div class="stat-num-big">500k+</div>
        <div class="stat-label-sm">Apps Tracked</div>
      </div>
      <div class="stat-item">
        <div class="stat-num-big">25k+</div>
        <div class="stat-label-sm">Interviews</div>
      </div>
      <div class="stat-item">
        <div class="stat-num-big">94%</div>
        <div class="stat-label-sm">Success Rate</div>
      </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Features ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="features-section">
      <div class="features-title">Powerful Features for Modern Job Seekers</div>
      <div class="features-sub">Everything you need to land your next role faster.</div>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">📬</div>
          <div class="feature-title">Gmail Sync</div>
          <div class="feature-desc">Automatically pull job applications from your inbox. No manual entry ever.</div>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🧠</div>
          <div class="feature-title">AI Enrichment</div>
          <div class="feature-desc">Deep insights on companies and recruiters found automatically across 7 sources.</div>
        </div>
        <div class="feature-card">
          <div class="feature-icon">✉️</div>
          <div class="feature-title">AI Email Generator</div>
          <div class="feature-desc">Generate personalized cold outreach emails to recruiters in seconds with Groq AI.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bottom CTA ─────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:48px 2rem;background:#0f172a;
                border-radius:24px;margin:0 2rem 48px;">
      <div style="font-size:2rem;font-weight:700;color:#fff;margin-bottom:12px;">
        Ready to land your dream role?
      </div>
      <div style="font-size:1rem;color:#94a3b8;margin-bottom:32px;">
        Stop manually updating spreadsheets. Let CareerSync handle the tracking.
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, b1, b2, _ = st.columns([2, 1.5, 1.5, 2])
    with b1:
        if st.button("Get Started for Free", key="bottom_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()
    with b2:
        if st.button("Sign In →", key="bottom_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()

    st.markdown("""
    <div style="text-align:center;padding:24px 0;font-size:0.75rem;color:#94a3b8;">
      © 2026 CareerSync Inc. All rights reserved. ·
      🔒 Cloud database · Share your link · Everyone gets their own private dashboard
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
    div[data-testid="stTextInput"] input{
      border-radius:8px!important;border:1px solid #cbd5e1!important;
      background:#fff!important;padding:12px 16px!important;
      color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{
      border-color:#2563EB!important;box-shadow:0 0 0 2px rgba(37,99,235,0.12)!important;}
    div[data-testid="stTextInput"] label{
      font-size:0.875rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{
      width:100%!important;border-radius:8px!important;background:#2563EB!important;
      padding:12px!important;font-size:0.9rem!important;font-weight:700!important;
      color:#fff!important;border:none!important;}
    div[data-testid="stFormSubmitButton"] button:hover{background:#1d4ed8!important;}
    div.stButton>button{
      background:transparent!important;color:#2563EB!important;
      border:none!important;padding:4px!important;font-size:0.875rem!important;
      font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:40px 0 28px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#2563EB;
                    display:flex;align-items:center;justify-content:center;font-size:20px;">💼</div>
        <span style="font-size:1.5rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.5rem;font-weight:700;color:#0f172a;margin:20px 0 6px;">Welcome back</h2>
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
                st.session_state.user    = user
                st.session_state.user_id = user["id"]
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error("❌ Invalid email or password.")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _, bc, _ = st.columns([1, 2, 1])
    with bc:
        if st.button("Don't have an account? Sign up →", key="go_reg", use_container_width=True):
            st.session_state.auth_view = "register"; st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
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
    div[data-testid="stTextInput"] input{
      border-radius:8px!important;border:1px solid #cbd5e1!important;
      background:#fff!important;padding:12px 16px!important;
      color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{
      border-color:#2563EB!important;box-shadow:0 0 0 2px rgba(37,99,235,.12)!important;}
    div[data-testid="stTextInput"] label{
      font-size:0.875rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{
      width:100%!important;border-radius:8px!important;background:#2563EB!important;
      padding:12px!important;font-size:0.9rem!important;font-weight:700!important;
      color:#fff!important;border:none!important;}
    div[data-testid="stFormSubmitButton"] button:hover{background:#1d4ed8!important;}
    div.stButton>button{
      background:transparent!important;color:#2563EB!important;
      border:none!important;padding:4px!important;font-size:0.875rem!important;
      font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:32px 0 20px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#2563EB;
                    display:flex;align-items:center;justify-content:center;font-size:20px;">💼</div>
        <span style="font-size:1.5rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.5rem;font-weight:700;color:#0f172a;margin:16px 0 6px;">Create your account</h2>
      <p style="font-size:0.875rem;color:#64748b;margin:0;">
        Each account has its own private dashboard synced to your Gmail
      </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        name  = st.text_input("Full name",        placeholder="John Smith")
        r_em  = st.text_input("Email address",    placeholder="name@company.com")
        r_pw  = st.text_input("Password",         placeholder="Create a password (min 6 chars)", type="password")
        r_pw2 = st.text_input("Confirm password", placeholder="Repeat your password",            type="password")

        st.markdown("""
        <div style="margin:16px 0 8px;padding-top:16px;border-top:1px solid #f1f5f9;">
          <div style="font-size:0.78rem;font-weight:700;color:#374151;
                      text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">
            📬 Gmail Sync Credentials
          </div>
          <p style="font-size:0.78rem;color:#94a3b8;margin:0 0 8px;">
            CareerSync syncs <strong>your</strong> Gmail privately.
            <a href="https://myaccount.google.com/apppasswords" target="_blank"
               style="color:#2563EB;font-weight:600;">Get App Password →</a>
            &nbsp;App: <b>Mail</b> · Device: <b>Other</b> → name it <b>CareerSync</b>
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
                    st.session_state.user    = user
                    st.session_state.user_id = user["id"]
                    st.switch_page("pages/1_Dashboard.py")
            else:
                st.error(f"❌ {msg}")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _, bc2, _ = st.columns([1, 2, 1])
    with bc2:
        if st.button("Already have an account? Sign in →", key="go_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("← Back to home", key="back_home_r"):
        st.session_state.auth_view = "landing"; st.rerun()

    st.markdown("""
    <div style="text-align:center;padding:20px 0;font-size:0.75rem;color:#94a3b8;">
      © 2026 CareerSync Inc. All rights reserved.
    </div>
    """, unsafe_allow_html=True)