"""
app.py — CareerSync Landing + Login + Register
Persistent login via browser localStorage (cs_uid key).
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="CareerSync — Automated Job Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from auth import register_user, login_user, supabase_ready, get_user_by_id

# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENT LOGIN — check localStorage via query param
# ══════════════════════════════════════════════════════════════════════════════

def _restore_session():
    """Restore session from ?uid= (set by localStorage JS)."""
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

def _set_login(user: dict):
    st.session_state["user"]    = user
    st.session_state["user_id"] = user["id"]
    st.query_params["uid"]      = user["id"]

def _clear_login():
    for k in ["user", "user_id"]:
        st.session_state.pop(k, None)
    st.query_params.clear()


# ── Inject localStorage → URL bridge (runs on every page load) ────────────────
components.html("""
<script>
(function() {
    try {
        var uid = localStorage.getItem('cs_uid');
        if (uid) {
            var params = new URLSearchParams(window.location.search);
            if (!params.get('uid')) {
                params.set('uid', uid);
                window.location.replace(window.location.pathname + '?' + params.toString());
            }
        }
    } catch(e) {}
})();
</script>
""", height=0, scrolling=False)

# ── Try to restore session ─────────────────────────────────────────────────────
_restore_session()

# ── Redirect if already logged in ─────────────────────────────────────────────
if st.session_state.get("user"):
    # Save uid to localStorage whenever we confirm login
    uid = st.session_state["user"].get("id", "")
    components.html(f"""
    <script>
    try {{ localStorage.setItem('cs_uid', '{uid}'); }} catch(e) {{}}
    </script>
    """, height=0, scrolling=False)
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
# LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.auth_view == "landing":

    st.markdown("""
    <style>
    .cs-nav{background:rgba(246,246,248,0.95);backdrop-filter:blur(12px);
      border-bottom:1px solid #e2e8f0;padding:0 2rem;height:64px;
      display:flex;align-items:center;justify-content:space-between;}
    .cs-nav-logo{display:flex;align-items:center;gap:8px;
      font-size:1.2rem;font-weight:700;color:#0f172a;}
    .hero-section{max-width:860px;margin:0 auto;padding:64px 2rem 40px;text-align:center;}
    .hero-badge{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;
      border-radius:9999px;background:rgba(37,99,235,0.08);border:1px solid rgba(37,99,235,0.2);
      font-size:0.72rem;font-weight:700;color:#2563EB;text-transform:uppercase;
      letter-spacing:0.8px;margin-bottom:24px;}
    .hero-dot{width:6px;height:6px;border-radius:50%;background:#2563EB;
      display:inline-block;animation:pulse 2s infinite;}
    @keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
    .hero-title{font-size:clamp(2rem,5vw,3.2rem);font-weight:700;color:#0f172a;
      line-height:1.1;letter-spacing:-1px;margin-bottom:20px;}
    .hero-title span{color:#2563EB;}
    .hero-sub{font-size:1.05rem;color:#64748b;max-width:580px;
      margin:0 auto 40px;line-height:1.7;}
    .stats-bar{display:flex;justify-content:center;gap:40px;flex-wrap:wrap;
      padding:28px;background:#fff;border-radius:16px;border:1px solid #e2e8f0;
      max-width:680px;margin:24px auto 48px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.04);}
    .stat-item{text-align:center;}
    .stat-num-big{font-size:1.8rem;font-weight:700;color:#0f172a;line-height:1;}
    .stat-label-sm{font-size:0.7rem;color:#64748b;font-weight:600;
      text-transform:uppercase;letter-spacing:0.7px;margin-top:4px;}
    .features-section{max-width:960px;margin:0 auto;padding:0 2rem 48px;}
    .features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;}
    .feature-card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;
      padding:24px;box-shadow:0 1px 3px rgba(0,0,0,0.04);}
    .feature-icon{font-size:1.5rem;margin-bottom:12px;}
    .feature-title{font-size:0.95rem;font-weight:700;color:#0f172a;margin-bottom:6px;}
    .feature-desc{font-size:0.85rem;color:#64748b;line-height:1.6;}
    div.stButton>button{border-radius:10px!important;font-weight:700!important;
      font-family:'DM Sans',sans-serif!important;transition:all 0.2s!important;}
    </style>
    """, unsafe_allow_html=True)

    # Nav
    st.markdown('<div class="cs-nav"><div class="cs-nav-logo">⇄ CareerSync</div></div>',
                unsafe_allow_html=True)
    _, nl, ns = st.columns([6, 1, 1])
    with nl:
        if st.button("Log In", key="nav_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()
    with ns:
        if st.button("Sign Up", key="nav_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()

    # Hero
    st.markdown("""
    <div class="hero-section">
      <div class="hero-badge"><span class="hero-dot"></span> AI-Powered Job Hunting</div>
      <div class="hero-title">Automated Job Application<br><span>Tracker</span> &amp; Recruiter Research</div>
      <div class="hero-sub">Automatically track applications, research recruiters, and generate AI-powered outreach emails in one professional dashboard.</div>
    </div>
    """, unsafe_allow_html=True)

    _, c1, c2, _ = st.columns([2, 1.5, 1.5, 2])
    with c1:
        if st.button("🚀 Start Tracking Free", key="hero_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()
    with c2:
        if st.button("Sign In", key="hero_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()

    st.markdown("""
    <div class="stats-bar">
      <div class="stat-item"><div class="stat-num-big">10k+</div><div class="stat-label-sm">Active Users</div></div>
      <div class="stat-item"><div class="stat-num-big">500k+</div><div class="stat-label-sm">Apps Tracked</div></div>
      <div class="stat-item"><div class="stat-num-big">25k+</div><div class="stat-label-sm">Interviews</div></div>
      <div class="stat-item"><div class="stat-num-big">94%</div><div class="stat-label-sm">Success Rate</div></div>
    </div>
    <div class="features-section">
      <div style="text-align:center;font-size:1.6rem;font-weight:700;color:#0f172a;margin-bottom:6px;">Powerful Features</div>
      <div style="text-align:center;color:#64748b;margin-bottom:28px;">Everything you need to land your next role faster.</div>
      <div class="features-grid">
        <div class="feature-card"><div class="feature-icon">📬</div><div class="feature-title">Gmail Sync</div><div class="feature-desc">Automatically pull job applications from your inbox. No manual entry.</div></div>
        <div class="feature-card"><div class="feature-icon">🧠</div><div class="feature-title">AI Enrichment</div><div class="feature-desc">Find recruiters across 7 sources — LinkedIn, Hunter, Apollo and more.</div></div>
        <div class="feature-card"><div class="feature-icon">✉️</div><div class="feature-title">AI Cold Emails</div><div class="feature-desc">Generate personalized outreach emails to recruiters in seconds.</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""<div style="text-align:center;padding:40px 2rem;background:#0f172a;
      border-radius:20px;margin:0 2rem 40px;">
      <div style="font-size:1.8rem;font-weight:700;color:#fff;margin-bottom:10px;">Ready to land your dream role?</div>
      <div style="font-size:0.95rem;color:#94a3b8;margin-bottom:28px;">Stop manually updating spreadsheets. Let CareerSync handle it.</div>
    </div>""", unsafe_allow_html=True)

    _, b1, b2, _ = st.columns([2, 1.5, 1.5, 2])
    with b1:
        if st.button("Get Started Free", key="bottom_signup", use_container_width=True, type="primary"):
            st.session_state.auth_view = "register"; st.rerun()
    with b2:
        if st.button("Sign In →", key="bottom_login", use_container_width=True):
            st.session_state.auth_view = "login"; st.rerun()

    st.markdown("""<div style="text-align:center;padding:20px 0 32px;font-size:0.75rem;color:#94a3b8;">
      © 2026 CareerSync Inc. All rights reserved. · 🔒 Private cloud database
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "login":
    st.markdown("""
    <style>
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{background:#f6f6f8!important;}
    .block-container{padding:2rem 1rem!important;max-width:460px!important;margin:0 auto!important;}
    div[data-testid="stTextInput"] input{border-radius:8px!important;border:1px solid #cbd5e1!important;
      background:#fff!important;padding:12px 16px!important;color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;box-shadow:0 0 0 2px rgba(37,99,235,0.12)!important;}
    div[data-testid="stTextInput"] label{font-size:0.875rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{width:100%!important;border-radius:8px!important;
      background:#2563EB!important;padding:12px!important;font-size:0.9rem!important;
      font-weight:700!important;color:#fff!important;border:none!important;}
    div.stButton>button{background:transparent!important;color:#2563EB!important;border:none!important;
      padding:4px!important;font-size:0.875rem!important;font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""<div style="text-align:center;padding:40px 0 28px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#2563EB;
                    display:flex;align-items:center;justify-content:center;font-size:20px;">💼</div>
        <span style="font-size:1.5rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:20px 0 6px;">Welcome back</h2>
      <p style="font-size:0.875rem;color:#64748b;margin:0;">Enter your details to sign in</p>
    </div>""", unsafe_allow_html=True)

    with st.form("login_form"):
        email    = st.text_input("Email address", placeholder="name@company.com")
        password = st.text_input("Password",      placeholder="••••••••", type="password")
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
                # Save to localStorage
                components.html(f"""
                <script>
                try {{
                    localStorage.setItem('cs_uid', '{user["id"]}');
                    console.log('CareerSync: login saved to localStorage');
                }} catch(e) {{}}
                </script>
                """, height=0, scrolling=False)
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
# REGISTER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "register":
    st.markdown("""
    <style>
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{background:#f6f6f8!important;}
    .block-container{padding:2rem 1rem!important;max-width:520px!important;margin:0 auto!important;}
    div[data-testid="stTextInput"] input{border-radius:8px!important;border:1px solid #cbd5e1!important;
      background:#fff!important;padding:12px 16px!important;color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;box-shadow:0 0 0 2px rgba(37,99,235,.12)!important;}
    div[data-testid="stTextInput"] label{font-size:0.875rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{width:100%!important;border-radius:8px!important;
      background:#2563EB!important;padding:12px!important;font-size:0.9rem!important;
      font-weight:700!important;color:#fff!important;border:none!important;}
    div.stButton>button{background:transparent!important;color:#2563EB!important;border:none!important;
      padding:4px!important;font-size:0.875rem!important;font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""<div style="text-align:center;padding:32px 0 20px;">
      <div style="display:inline-flex;align-items:center;gap:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:#2563EB;
                    display:flex;align-items:center;justify-content:center;font-size:20px;">💼</div>
        <span style="font-size:1.5rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.4rem;font-weight:700;color:#0f172a;margin:16px 0 6px;">Create your account</h2>
      <p style="font-size:0.875rem;color:#64748b;margin:0;">Each account has its own private dashboard</p>
    </div>""", unsafe_allow_html=True)

    with st.form("register_form"):
        name  = st.text_input("Full name",        placeholder="John Smith")
        r_em  = st.text_input("Email address",    placeholder="name@company.com")
        r_pw  = st.text_input("Password",         placeholder="Create a password (min 6 chars)", type="password")
        r_pw2 = st.text_input("Confirm password", placeholder="Repeat your password",            type="password")
        st.markdown("""<div style="margin:16px 0 8px;padding-top:16px;border-top:1px solid #f1f5f9;">
          <div style="font-size:0.78rem;font-weight:700;color:#374151;text-transform:uppercase;
                      letter-spacing:.06em;margin-bottom:6px;">📬 Gmail Sync Credentials</div>
          <p style="font-size:0.78rem;color:#94a3b8;margin:0 0 8px;">
            CareerSync syncs <strong>your</strong> Gmail privately.
            <a href="https://myaccount.google.com/apppasswords" target="_blank"
               style="color:#2563EB;font-weight:600;">Get App Password →</a>
            App: <b>Mail</b> · Device: <b>Other</b> → name it <b>CareerSync</b>
          </p></div>""", unsafe_allow_html=True)
        gm_acc  = st.text_input("Your Gmail address",      placeholder="yourname@gmail.com")
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
                    components.html(f"""
                    <script>
                    try {{
                        localStorage.setItem('cs_uid', '{user["id"]}');
                    }} catch(e) {{}}
                    </script>
                    """, height=0, scrolling=False)
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