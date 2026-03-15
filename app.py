"""
app.py — CareerSync Landing + Login + Register
Landing page matches exact HTML UI design.
Buttons work via window.top.location.href redirect.
No extra Streamlit buttons below the iframe.
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

# Handle action from iframe button clicks
action = st.query_params.get("action", "")
if action == "login":
    st.query_params.clear()
    st.session_state.auth_view = "login"
    st.rerun()
elif action == "signup":
    st.query_params.clear()
    st.session_state.auth_view = "register"
    st.rerun()

# Redirect if already logged in
if st.session_state.get("user"):
    st.switch_page("pages/1_Dashboard.py")
    st.stop()

if "auth_view" not in st.session_state:
    st.session_state.auth_view = "landing"

# ── Hide Streamlit chrome ──────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="stSidebar"],
[data-testid="collapsedControl"],[data-testid="stHeader"]{display:none!important;}
.block-container{padding:0!important;max-width:100%!important;}
body,.stApp,[data-testid="stAppViewContainer"],
section.main,[data-testid="stMain"]{background:#f6f6f8!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE — exact HTML design, all buttons clickable
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.auth_view == "landing":

    LANDING_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>CareerSync</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script>
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {"primary": "#2563EB", "background-light": "#f6f6f8"},
      fontFamily: {"display": ["DM Sans", "sans-serif"]},
      borderRadius: {"DEFAULT": "0.25rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"},
    },
  },
}
</script>
<style>body { font-family: 'DM Sans', sans-serif; }</style>
</head>
<body class="bg-background-light text-slate-900">

<!-- Top Navigation -->
<header class="sticky top-0 z-50 w-full border-b border-slate-200 bg-background-light/80 backdrop-blur-md">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
<div class="flex h-16 items-center justify-between">
  <div class="flex items-center gap-2">
    <div class="text-primary flex items-center justify-center">
      <span class="material-symbols-outlined text-3xl">sync_alt</span>
    </div>
    <span class="text-xl font-bold tracking-tight text-slate-900">CareerSync</span>
  </div>
  <nav class="hidden md:flex items-center gap-8">
    <a class="text-sm font-medium text-slate-600 hover:text-primary transition-colors" href="#features">Features</a>
    <a class="text-sm font-medium text-slate-600 hover:text-primary transition-colors" href="#how-it-works">How it Works</a>
    <a class="text-sm font-medium text-slate-600 hover:text-primary transition-colors" href="#pricing">Pricing</a>
    <a class="text-sm font-medium text-slate-600 hover:text-primary transition-colors cursor-pointer" id="nav-login">Log In</a>
    <button id="nav-signup" class="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-lg text-sm font-bold transition-all shadow-sm">
      Get Started Free
    </button>
  </nav>
  <div class="md:hidden flex gap-3">
    <button id="mob-login" class="text-sm font-semibold text-primary border border-primary px-4 py-2 rounded-lg">Log In</button>
    <button id="mob-signup" class="bg-primary text-white text-sm font-bold px-4 py-2 rounded-lg">Sign Up</button>
  </div>
</div>
</div>
</header>

<main>
<!-- Hero Section -->
<section class="relative pt-16 pb-20 lg:pt-24 lg:pb-32 overflow-hidden">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
<div class="grid lg:grid-cols-2 gap-12 items-center">
  <div class="flex flex-col gap-8">
    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 w-fit">
      <span class="flex h-2 w-2 rounded-full bg-primary animate-pulse"></span>
      <span class="text-xs font-bold text-primary tracking-wide uppercase">AI-Powered Job Hunting</span>
    </div>
    <h1 class="text-4xl lg:text-6xl font-bold leading-[1.1] text-slate-900 tracking-tight">
      Automated Job Application <span class="text-primary">Tracker</span> &amp; Recruiter Research
    </h1>
    <p class="text-lg text-slate-600 leading-relaxed max-w-xl">
      Streamline your job search with CareerSync. Automatically track applications, research recruiters, and generate AI-powered outreach emails in one professional dashboard.
    </p>
    <div class="flex flex-col sm:flex-row gap-4">
      <label class="flex-1 max-w-md">
        <div class="relative flex items-center group">
          <div class="absolute left-4 text-slate-400 group-focus-within:text-primary transition-colors">
            <span class="material-symbols-outlined">mail</span>
          </div>
          <input class="w-full pl-12 pr-4 py-4 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-primary focus:border-primary transition-all shadow-sm outline-none" placeholder="Enter your work email" type="email" id="hero-email"/>
        </div>
      </label>
      <button id="btn-start" class="bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg shadow-primary/20 cursor-pointer">
        Start Tracking
      </button>
    </div>
    <div class="flex items-center gap-4 text-sm text-slate-500">
      <div class="flex -space-x-2">
        <div class="h-8 w-8 rounded-full border-2 border-white bg-indigo-400 flex items-center justify-center text-white text-xs font-bold">JK</div>
        <div class="h-8 w-8 rounded-full border-2 border-white bg-sky-400 flex items-center justify-center text-white text-xs font-bold">AM</div>
        <div class="h-8 w-8 rounded-full border-2 border-white bg-amber-400 flex items-center justify-center text-white text-xs font-bold">SR</div>
      </div>
      <span>Joined by 10k+ active job seekers</span>
    </div>
  </div>
  <div class="relative">
    <div class="absolute inset-0 bg-primary/20 blur-[120px] rounded-full pointer-events-none"></div>
    <div class="relative rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl">
      <div class="rounded-xl bg-slate-50 border border-slate-100 p-4">
        <div class="bg-white rounded-lg px-4 py-3 flex items-center justify-between mb-3 shadow-sm">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-xl">sync_alt</span>
            <span class="font-bold text-slate-900 text-sm">CareerSync</span>
          </div>
          <span class="bg-primary text-white text-xs font-bold px-3 py-1.5 rounded-lg">Sync Gmail</span>
        </div>
        <div class="grid grid-cols-3 gap-2 mb-3">
          <div class="bg-white rounded-xl p-3 border border-slate-100 shadow-sm">
            <div class="text-2xl font-bold text-slate-900">24</div>
            <div class="text-xs text-slate-500 font-semibold uppercase tracking-wide mt-0.5">Applications</div>
          </div>
          <div class="bg-white rounded-xl p-3 border border-slate-100 shadow-sm">
            <div class="text-2xl font-bold text-slate-900">6</div>
            <div class="text-xs text-slate-500 font-semibold uppercase tracking-wide mt-0.5">Interviews</div>
          </div>
          <div class="bg-white rounded-xl p-3 border border-slate-100 shadow-sm">
            <div class="text-2xl font-bold text-slate-900">18</div>
            <div class="text-xs text-slate-500 font-semibold uppercase tracking-wide mt-0.5">Recruiters</div>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <div class="bg-white rounded-xl px-3 py-2.5 border border-slate-100 flex items-center justify-between shadow-sm">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500">G</div>
              <div>
                <div class="text-sm font-semibold">Google</div>
                <div class="text-xs text-slate-400">Software Engineer</div>
              </div>
            </div>
            <span class="text-xs font-bold px-2 py-1 rounded-full bg-amber-100 text-amber-700">Interview</span>
          </div>
          <div class="bg-white rounded-xl px-3 py-2.5 border border-slate-100 flex items-center justify-between shadow-sm">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-xs font-bold text-slate-500">S</div>
              <div>
                <div class="text-sm font-semibold">Stripe</div>
                <div class="text-xs text-slate-400">Full Stack Engineer</div>
              </div>
            </div>
            <span class="text-xs font-bold px-2 py-1 rounded-full bg-green-100 text-green-700">Offer</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</div>
</section>

<!-- Social Proof -->
<section class="py-12 border-y border-slate-200 bg-slate-50/50">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <p class="text-center text-sm font-semibold text-slate-400 uppercase tracking-widest mb-8">Trusted by candidates hired at</p>
  <div class="flex flex-wrap justify-center gap-8 md:gap-16 opacity-50 grayscale">
    <div class="h-8 w-24 bg-slate-400 rounded"></div>
    <div class="h-8 w-24 bg-slate-400 rounded"></div>
    <div class="h-8 w-24 bg-slate-400 rounded"></div>
    <div class="h-8 w-24 bg-slate-400 rounded"></div>
    <div class="h-8 w-24 bg-slate-400 rounded"></div>
  </div>
</div>
</section>

<!-- Features Grid -->
<section class="py-20 lg:py-32" id="features">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="text-center max-w-3xl mx-auto mb-16 flex flex-col gap-4">
    <h2 class="text-3xl lg:text-4xl font-bold tracking-tight text-slate-900">Powerful Features for Modern Job Seekers</h2>
    <p class="text-slate-600 text-lg">Everything you need to land your next role faster, without the manual spreadsheet maintenance.</p>
  </div>
  <div class="grid md:grid-cols-3 gap-8">
    <div class="group p-8 rounded-2xl border border-slate-200 bg-white hover:border-primary/50 transition-all shadow-sm hover:shadow-xl hover:shadow-primary/5">
      <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
        <span class="material-symbols-outlined">sync_disabled</span>
      </div>
      <h3 class="text-xl font-bold text-slate-900 mb-3">Gmail Sync</h3>
      <p class="text-slate-600 leading-relaxed">Automatically pull job applications directly from your inbox. No manual entry, no missed opportunities.</p>
    </div>
    <div class="group p-8 rounded-2xl border border-slate-200 bg-white hover:border-primary/50 transition-all shadow-sm hover:shadow-xl hover:shadow-primary/5">
      <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
        <span class="material-symbols-outlined">psychology</span>
      </div>
      <h3 class="text-xl font-bold text-slate-900 mb-3">AI Enrichment</h3>
      <p class="text-slate-600 leading-relaxed">Get deep insights on companies and recruiters. Know their recent funding, news, and interview style.</p>
    </div>
    <div class="group p-8 rounded-2xl border border-slate-200 bg-white hover:border-primary/50 transition-all shadow-sm hover:shadow-xl hover:shadow-primary/5">
      <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
        <span class="material-symbols-outlined">magic_button</span>
      </div>
      <h3 class="text-xl font-bold text-slate-900 mb-3">AI Email Generator</h3>
      <p class="text-slate-600 leading-relaxed">Generate personalized, high-conversion outreach emails in seconds tailored to the role and recruiter.</p>
    </div>
  </div>
</div>
</section>

<!-- Stats -->
<section class="py-20 bg-slate-900 text-white rounded-[2rem] mx-4 sm:mx-8 mb-20" id="how-it-works">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
    <div class="flex flex-col gap-2"><span class="text-4xl lg:text-5xl font-bold">10k+</span><span class="text-slate-400 text-sm font-medium uppercase tracking-widest">Active Users</span></div>
    <div class="flex flex-col gap-2"><span class="text-4xl lg:text-5xl font-bold">500k+</span><span class="text-slate-400 text-sm font-medium uppercase tracking-widest">Apps Tracked</span></div>
    <div class="flex flex-col gap-2"><span class="text-4xl lg:text-5xl font-bold">25k+</span><span class="text-slate-400 text-sm font-medium uppercase tracking-widest">Interviews</span></div>
    <div class="flex flex-col gap-2"><span class="text-4xl lg:text-5xl font-bold">94%</span><span class="text-slate-400 text-sm font-medium uppercase tracking-widest">Success Rate</span></div>
  </div>
</div>
</section>

<!-- CTA Section -->
<section class="py-20 lg:py-32 bg-primary/5" id="pricing">
<div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
  <h2 class="text-3xl lg:text-5xl font-bold text-slate-900 mb-6">Ready to land your dream role?</h2>
  <p class="text-xl text-slate-600 mb-10 max-w-2xl mx-auto">
    Stop manually updating spreadsheets. Let CareerSync handle the tracking while you focus on the interview.
  </p>
  <div class="flex flex-col sm:flex-row justify-center gap-4">
    <button id="btn-getstarted" class="bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg shadow-primary/25 cursor-pointer">
      Get Started for Free
    </button>
    <button id="btn-demo" class="bg-white text-slate-900 px-8 py-4 rounded-xl font-bold text-lg border border-slate-200 hover:bg-slate-50 transition-all cursor-pointer">
      View Demo
    </button>
  </div>
</div>
</section>
</main>

<!-- Footer -->
<footer class="bg-white border-t border-slate-200 pt-16 pb-8">
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-16">
    <div class="col-span-2 flex flex-col gap-6">
      <div class="flex items-center gap-2">
        <div class="text-primary"><span class="material-symbols-outlined text-3xl">sync_alt</span></div>
        <span class="text-xl font-bold tracking-tight text-slate-900">CareerSync</span>
      </div>
      <p class="text-slate-500 max-w-xs leading-relaxed">The modern operating system for your professional career growth and job hunt.</p>
      <div class="flex gap-4">
        <a class="text-slate-400 hover:text-primary transition-colors" href="#"><span class="material-symbols-outlined">public</span></a>
        <a class="text-slate-400 hover:text-primary transition-colors" href="#"><span class="material-symbols-outlined">group</span></a>
        <a class="text-slate-400 hover:text-primary transition-colors" href="#"><span class="material-symbols-outlined">alternate_email</span></a>
      </div>
    </div>
    <div>
      <h4 class="font-bold text-slate-900 mb-6">Product</h4>
      <ul class="flex flex-col gap-4 text-slate-500 text-sm">
        <li><a class="hover:text-primary transition-colors" href="#features">Features</a></li>
        <li><a class="hover:text-primary transition-colors" href="#pricing">Pricing</a></li>
        <li><a class="hover:text-primary transition-colors" href="#how-it-works">Integrations</a></li>
        <li><a class="hover:text-primary transition-colors" href="#">Updates</a></li>
      </ul>
    </div>
    <div>
      <h4 class="font-bold text-slate-900 mb-6">Resources</h4>
      <ul class="flex flex-col gap-4 text-slate-500 text-sm">
        <li><a class="hover:text-primary transition-colors" href="#">Blog</a></li>
        <li><a class="hover:text-primary transition-colors" href="#">Help Center</a></li>
        <li><a class="hover:text-primary transition-colors" href="#">Job Search Tips</a></li>
        <li><a class="hover:text-primary transition-colors" href="#">Resume Guide</a></li>
      </ul>
    </div>
    <div>
      <h4 class="font-bold text-slate-900 mb-6">Legal</h4>
      <ul class="flex flex-col gap-4 text-slate-500 text-sm">
        <li><a class="hover:text-primary transition-colors" href="#">Privacy</a></li>
        <li><a class="hover:text-primary transition-colors" href="#">Terms</a></li>
        <li><a class="hover:text-primary transition-colors" href="#">Security</a></li>
      </ul>
    </div>
  </div>
  <div class="pt-8 border-t border-slate-200 flex flex-col md:flex-row justify-between gap-4 text-sm text-slate-500">
    <p>© 2026 CareerSync Inc. All rights reserved.</p>
    <div class="flex gap-6">
      <a class="hover:text-slate-900 transition-colors" href="#">Cookies</a>
      <a class="hover:text-slate-900 transition-colors" href="#">Accessibility</a>
    </div>
  </div>
</div>
</footer>

<script>
// Use window.top.location.href to change the parent Streamlit URL
function goLogin()  {
    window.top.location.href = window.top.location.pathname + '?action=login';
}
function goSignup() {
    window.top.location.href = window.top.location.pathname + '?action=signup';
}

document.getElementById("nav-login")?.addEventListener("click",      function(e){e.preventDefault();goLogin();});
document.getElementById("nav-signup")?.addEventListener("click",     goSignup);
document.getElementById("mob-login")?.addEventListener("click",      goLogin);
document.getElementById("mob-signup")?.addEventListener("click",     goSignup);
document.getElementById("btn-start")?.addEventListener("click",      goSignup);
document.getElementById("btn-getstarted")?.addEventListener("click", goSignup);
document.getElementById("btn-demo")?.addEventListener("click",       goLogin);
</script>
</body></html>"""

    components.html(LANDING_HTML, height=3400, scrolling=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "login":
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
      background:#f6f6f8!important;font-family:'DM Sans',sans-serif!important;}
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
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{
      background:#f6f6f8!important;font-family:'DM Sans',sans-serif!important;}
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