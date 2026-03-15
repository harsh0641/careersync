"""
app.py — CareerSync Landing + Login + Register
Matches reference image 2 exactly:
- Clean minimal navbar: Features | How it Works | Pricing | Log In | Get Started Free
- Simple professional design
- No floating buttons
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
# AUTH
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

# Route from HTML anchor clicks
_nav = st.query_params.get("nav", "")
if _nav == "login":
    st.query_params.clear()
    go("login")
elif _nav == "signup":
    st.query_params.clear()
    go("register")

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
  background:#f0f2f5!important;
  font-family:'DM Sans',sans-serif!important;
  margin:0!important;padding:0!important;
}
.block-container{padding:0!important;max-width:100%!important;margin:0!important;}
[data-testid="stVerticalBlock"]{gap:0!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LANDING
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.auth_view == "landing":

    st.markdown("""
    <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{font-family:'DM Sans',sans-serif;background:#f0f2f5;color:#0f172a;}

    /* ── NAVBAR — matches image 2 exactly ── */
    .nav{
      width:100%;background:#fff;
      border-bottom:1px solid #e8eaf0;
      height:60px;display:flex;align-items:center;
      justify-content:space-between;padding:0 2.5rem;
      position:sticky;top:0;z-index:999;
    }
    .nav-logo{
      display:flex;align-items:center;gap:8px;
      font-size:1.05rem;font-weight:700;color:#0f172a;text-decoration:none;
    }
    .nav-logo-svg{color:#2563EB;}
    .nav-links{display:flex;align-items:center;gap:28px;}
    .nav-link{
      font-size:0.85rem;font-weight:500;color:#64748b;
      text-decoration:none;transition:color 0.15s;
    }
    .nav-link:hover{color:#0f172a;}
    .nav-login{
      font-size:0.85rem;font-weight:500;color:#64748b;
      text-decoration:none;transition:color 0.15s;
    }
    .nav-login:hover{color:#0f172a;}
    .nav-cta{
      background:#2563EB;color:#fff;border:none;border-radius:8px;
      padding:8px 18px;font-size:0.85rem;font-weight:600;
      cursor:pointer;text-decoration:none;display:inline-block;
      font-family:'DM Sans',sans-serif;transition:background 0.15s;
    }
    .nav-cta:hover{background:#1d4ed8;}

    /* ── HERO ── */
    .hero{
      max-width:1200px;margin:0 auto;padding:72px 2.5rem 56px;
      display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center;
    }
    @media(max-width:860px){.hero{grid-template-columns:1fr;padding:40px 1.5rem;}}

    .badge{
      display:inline-flex;align-items:center;gap:6px;
      padding:4px 12px;border-radius:9999px;
      background:rgba(37,99,235,0.07);border:1px solid rgba(37,99,235,0.15);
      font-size:0.68rem;font-weight:700;color:#2563EB;
      text-transform:uppercase;letter-spacing:0.8px;margin-bottom:18px;
    }
    .badge-dot{
      width:5px;height:5px;border-radius:50%;background:#2563EB;
      display:inline-block;animation:blink 2s infinite;
    }
    @keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}

    .hero h1{
      font-size:clamp(2rem,4vw,3.5rem);font-weight:700;
      color:#0d1b2a;line-height:1.08;letter-spacing:-1px;margin-bottom:16px;
    }
    .hero h1 .blue{color:#2563EB;}

    .hero-desc{
      font-size:0.95rem;color:#64748b;line-height:1.7;
      margin-bottom:28px;max-width:460px;
    }

    .email-row{display:flex;gap:8px;margin-bottom:22px;flex-wrap:wrap;}
    .email-wrap{flex:1;min-width:180px;position:relative;}
    .email-icon{
      position:absolute;left:12px;top:50%;transform:translateY(-50%);
      font-size:0.85rem;color:#94a3b8;
    }
    .email-input{
      width:100%;padding:12px 12px 12px 36px;
      border-radius:10px;border:1.5px solid #e2e8f0;
      background:#fff;font-size:0.875rem;
      font-family:'DM Sans',sans-serif;outline:none;
      box-shadow:0 1px 3px rgba(0,0,0,0.04);
    }
    .email-input:focus{
      border-color:#2563EB;
      box-shadow:0 0 0 3px rgba(37,99,235,0.08);
    }
    .btn-start{
      background:#2563EB;color:#fff;border:none;border-radius:10px;
      padding:12px 22px;font-size:0.875rem;font-weight:700;
      cursor:pointer;font-family:'DM Sans',sans-serif;
      white-space:nowrap;text-decoration:none;display:inline-block;
      box-shadow:0 2px 8px rgba(37,99,235,0.25);transition:all 0.15s;
    }
    .btn-start:hover{background:#1d4ed8;}

    .social-row{display:flex;align-items:center;gap:10px;font-size:0.82rem;color:#64748b;}
    .avatars{display:flex;}
    .av{
      width:28px;height:28px;border-radius:50%;
      border:2px solid #f0f2f5;
      display:flex;align-items:center;justify-content:center;
      font-size:0.58rem;font-weight:700;color:#fff;margin-left:-7px;
    }
    .av:first-child{margin-left:0;}

    /* ── MOCK DASHBOARD ── */
    .mock-outer{position:relative;}
    .mock-glow{
      position:absolute;inset:-30px;
      background:radial-gradient(circle,rgba(37,99,235,0.08) 0%,transparent 70%);
      pointer-events:none;
    }
    .mock-card{
      position:relative;background:#fff;
      border:1px solid #e2e8f0;border-radius:20px;
      padding:6px;box-shadow:0 16px 48px -12px rgba(0,0,0,0.14);
    }
    .mock-inner{
      background:#f8fafc;border-radius:16px;
      border:1px solid #f0f2f5;padding:16px;
    }
    .mock-bar{
      background:#fff;border-radius:10px;padding:10px 14px;
      display:flex;align-items:center;justify-content:space-between;
      margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05);
    }
    .mock-bar-left{display:flex;align-items:center;gap:6px;font-weight:700;font-size:0.82rem;color:#0f172a;}
    .mock-sync-btn{
      background:#2563EB;color:#fff;font-size:0.68rem;font-weight:700;
      padding:6px 12px;border-radius:7px;
    }
    .mock-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:10px;}
    .mock-stat{
      background:#fff;border-radius:10px;padding:12px;
      border:1px solid #f0f2f5;box-shadow:0 1px 2px rgba(0,0,0,0.03);
    }
    .mock-num{font-size:1.4rem;font-weight:700;color:#0f172a;line-height:1;}
    .mock-lbl{font-size:0.58rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-top:3px;}
    .mock-row{
      background:#fff;border-radius:10px;padding:10px 12px;
      display:flex;align-items:center;justify-content:space-between;
      margin-bottom:7px;border:1px solid #f0f2f5;
    }
    .mock-row:last-child{margin-bottom:0;}
    .mock-co{display:flex;align-items:center;gap:9px;}
    .mock-logo{
      width:28px;height:28px;border-radius:8px;background:#f0f2f5;
      display:flex;align-items:center;justify-content:center;
      font-size:0.68rem;font-weight:700;color:#475569;
    }
    .mock-co-name{font-size:0.82rem;font-weight:600;color:#0f172a;}
    .mock-co-role{font-size:0.68rem;color:#94a3b8;}
    .b-iv{background:#fef9c3;color:#ca8a04;padding:2px 9px;border-radius:20px;font-size:0.65rem;font-weight:700;}
    .b-of{background:#dcfce7;color:#16a34a;padding:2px 9px;border-radius:20px;font-size:0.65rem;font-weight:700;}

    /* ── SOCIAL PROOF ── */
    .proof{
      padding:28px 2.5rem;
      border-top:1px solid #e8eaf0;border-bottom:1px solid #e8eaf0;
      background:#fff;
    }
    .proof-inner{max-width:1200px;margin:0 auto;text-align:center;}
    .proof-lbl{font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:18px;}
    .proof-logos{display:flex;justify-content:center;gap:24px;flex-wrap:wrap;opacity:0.25;}
    .proof-logo{width:76px;height:22px;background:#94a3b8;border-radius:3px;}

    /* ── FEATURES ── */
    .features-wrap{background:#fff;padding:72px 2.5rem;}
    .features{max-width:1200px;margin:0 auto;}
    .sec-title{font-size:clamp(1.6rem,2.5vw,2.2rem);font-weight:700;color:#0d1b2a;text-align:center;margin-bottom:8px;letter-spacing:-0.3px;}
    .sec-sub{font-size:0.9rem;color:#64748b;text-align:center;margin-bottom:44px;line-height:1.65;max-width:540px;margin-left:auto;margin-right:auto;}
    .feat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;}
    @media(max-width:768px){.feat-grid{grid-template-columns:1fr;}}
    .feat-card{
      background:#f8fafc;border:1px solid #e8eaf0;border-radius:14px;
      padding:28px;transition:all 0.2s;
    }
    .feat-card:hover{background:#fff;box-shadow:0 8px 24px -6px rgba(37,99,235,0.08);border-color:rgba(37,99,235,0.2);}
    .feat-icon{width:40px;height:40px;border-radius:10px;background:rgba(37,99,235,0.08);display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:14px;}
    .feat-title{font-size:0.95rem;font-weight:700;color:#0d1b2a;margin-bottom:8px;}
    .feat-desc{font-size:0.82rem;color:#64748b;line-height:1.6;}

    /* ── STATS ── */
    .stats-wrap{padding:0 2rem;margin-bottom:0;}
    .stats{
      max-width:1200px;margin:0 auto;
      background:#0d1b2a;border-radius:18px;
      padding:52px 3rem;margin-bottom:0;
    }
    .stats-inner{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;text-align:center;}
    @media(max-width:768px){.stats-inner{grid-template-columns:repeat(2,1fr);}}
    .stat-big{font-size:clamp(1.8rem,3.5vw,2.8rem);font-weight:700;color:#fff;line-height:1;}
    .stat-lbl{font-size:0.65rem;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-top:8px;}

    /* ── CTA ── */
    .cta-wrap{background:rgba(37,99,235,0.03);padding:72px 2.5rem;}
    .cta{max-width:600px;margin:0 auto;text-align:center;}
    .cta h2{font-size:clamp(1.7rem,3.5vw,2.6rem);font-weight:700;color:#0d1b2a;margin-bottom:12px;letter-spacing:-0.5px;}
    .cta p{font-size:0.95rem;color:#64748b;margin-bottom:32px;line-height:1.7;}
    .cta-btns{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;}
    .btn-cta-p{
      background:#2563EB;color:#fff;border:none;border-radius:9px;
      padding:12px 26px;font-size:0.9rem;font-weight:700;
      cursor:pointer;font-family:'DM Sans',sans-serif;text-decoration:none;
      box-shadow:0 2px 8px rgba(37,99,235,0.25);transition:all 0.15s;display:inline-block;
    }
    .btn-cta-p:hover{background:#1d4ed8;}
    .btn-cta-s{
      background:#fff;color:#0f172a;border:1.5px solid #e2e8f0;border-radius:9px;
      padding:12px 26px;font-size:0.9rem;font-weight:600;
      cursor:pointer;font-family:'DM Sans',sans-serif;text-decoration:none;
      transition:all 0.15s;display:inline-block;
    }
    .btn-cta-s:hover{border-color:#94a3b8;}

    /* ── FOOTER ── */
    .footer{background:#fff;border-top:1px solid #e8eaf0;padding:52px 2.5rem 24px;}
    .footer-grid{max-width:1200px;margin:0 auto;display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:36px;margin-bottom:36px;}
    @media(max-width:768px){.footer-grid{grid-template-columns:1fr 1fr;}}
    .f-logo{display:flex;align-items:center;gap:7px;font-size:0.95rem;font-weight:700;color:#0f172a;margin-bottom:10px;}
    .f-desc{font-size:0.82rem;color:#64748b;line-height:1.6;max-width:210px;}
    .f-col-title{font-size:0.8rem;font-weight:700;color:#0f172a;margin-bottom:14px;text-transform:uppercase;letter-spacing:0.4px;}
    .f-links{display:flex;flex-direction:column;gap:9px;}
    .f-link{font-size:0.82rem;color:#64748b;text-decoration:none;}
    .f-link:hover{color:#2563EB;}
    .f-bottom{max-width:1200px;margin:0 auto;padding-top:20px;border-top:1px solid #e8eaf0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;}
    .f-copy{font-size:0.75rem;color:#94a3b8;}
    </style>

    <!-- NAVBAR -->
    <nav class="nav">
      <a class="nav-logo" href="/">
        <svg class="nav-logo-svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 16V4m0 0L3 8m4-4l4 4"/><path d="M17 8v12m0 0l4-4m-4 4l-4-4"/>
        </svg>
        CareerSync
      </a>
      <div class="nav-links">
        <a class="nav-link" href="#features">Features</a>
        <a class="nav-link" href="#how-it-works">How it Works</a>
        <a class="nav-link" href="#pricing">Pricing</a>
        <a class="nav-login" href="/?nav=login">Log In</a>
        <a class="nav-cta"   href="/?nav=signup">Get Started Free</a>
      </div>
    </nav>

    <!-- HERO -->
    <section class="hero">
      <div>
        <div class="badge"><span class="badge-dot"></span> AI-Powered Job Hunting</div>
        <h1>Automated Job Application <span class="blue">Tracker</span> &amp; Recruiter Research</h1>
        <p class="hero-desc">Streamline your job search with CareerSync. Automatically track applications, research recruiters, and generate AI-powered outreach emails in one professional dashboard.</p>
        <div class="email-row">
          <div class="email-wrap">
            <span class="email-icon">✉️</span>
            <input class="email-input" placeholder="Enter your work email" type="email"/>
          </div>
          <a class="btn-start" href="/?nav=signup">Start Tracking</a>
        </div>
        <div class="social-row">
          <div class="avatars">
            <div class="av" style="background:#818cf8;">JK</div>
            <div class="av" style="background:#38bdf8;">AM</div>
            <div class="av" style="background:#94a3b8;">SR</div>
          </div>
          <span>Joined by 10k+ active job seekers</span>
        </div>
      </div>
      <div class="mock-outer">
        <div class="mock-glow"></div>
        <div class="mock-card">
          <div class="mock-inner">
            <div class="mock-bar">
              <div class="mock-bar-left">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M7 16V4m0 0L3 8m4-4l4 4"/><path d="M17 8v12m0 0l4-4m-4 4l-4-4"/>
                </svg>
                CareerSync
              </div>
              <span class="mock-sync-btn">Sync Gmail</span>
            </div>
            <div class="mock-stats">
              <div class="mock-stat"><div class="mock-num">24</div><div class="mock-lbl">Applications</div></div>
              <div class="mock-stat"><div class="mock-num">6</div><div class="mock-lbl">Interviews</div></div>
              <div class="mock-stat"><div class="mock-num">18</div><div class="mock-lbl">Recruiters</div></div>
            </div>
            <div class="mock-row">
              <div class="mock-co">
                <div class="mock-logo">G</div>
                <div><div class="mock-co-name">Google</div><div class="mock-co-role">Software Engineer</div></div>
              </div>
              <span class="b-iv">Interview</span>
            </div>
            <div class="mock-row">
              <div class="mock-co">
                <div class="mock-logo">S</div>
                <div><div class="mock-co-name">Stripe</div><div class="mock-co-role">Full Stack Engineer</div></div>
              </div>
              <span class="b-of">Offer</span>
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
    <div id="features" class="features-wrap">
      <div class="features">
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
    </div>

    <!-- STATS -->
    <div id="how-it-works" style="background:#f0f2f5;padding:48px 2rem;">
      <div class="stats">
        <div class="stats-inner">
          <div><div class="stat-big">10k+</div><div class="stat-lbl">Active Users</div></div>
          <div><div class="stat-big">500k+</div><div class="stat-lbl">Apps Tracked</div></div>
          <div><div class="stat-big">25k+</div><div class="stat-lbl">Interviews</div></div>
          <div><div class="stat-big">94%</div><div class="stat-lbl">Success Rate</div></div>
        </div>
      </div>
    </div>

    <!-- CTA -->
    <div id="pricing" class="cta-wrap">
      <div class="cta">
        <h2>Ready to land your dream role?</h2>
        <p>Stop manually updating spreadsheets. Let CareerSync handle the tracking while you focus on the interview.</p>
        <div class="cta-btns">
          <a class="btn-cta-p" href="/?nav=signup">Get Started for Free</a>
          <a class="btn-cta-s" href="/?nav=login">View Demo</a>
        </div>
      </div>
    </div>

    <!-- FOOTER -->
    <div class="footer">
      <div class="footer-grid">
        <div>
          <div class="f-logo">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 16V4m0 0L3 8m4-4l4 4"/><path d="M17 8v12m0 0l4-4m-4 4l-4-4"/>
            </svg>
            CareerSync
          </div>
          <div class="f-desc">The modern operating system for your professional career growth and job hunt.</div>
        </div>
        <div>
          <div class="f-col-title">Product</div>
          <div class="f-links">
            <a class="f-link" href="#features">Features</a>
            <a class="f-link" href="#pricing">Pricing</a>
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
        <div style="display:flex;gap:16px;">
          <a class="f-link" href="#">Cookies</a>
          <a class="f-link" href="#">Accessibility</a>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "login":
    st.markdown("""
    <style>
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{background:#f0f2f5!important;}
    .block-container{padding:2rem 1rem!important;max-width:420px!important;margin:0 auto!important;}
    div[data-testid="stTextInput"] input{border-radius:8px!important;border:1.5px solid #e2e8f0!important;
      background:#fff!important;padding:11px 14px!important;color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;
      box-shadow:0 0 0 3px rgba(37,99,235,0.08)!important;}
    div[data-testid="stTextInput"] label{font-size:0.85rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{width:100%!important;border-radius:8px!important;
      background:#2563EB!important;padding:11px!important;font-size:0.875rem!important;
      font-weight:700!important;color:#fff!important;border:none!important;}
    div[data-testid="stFormSubmitButton"] button:hover{background:#1d4ed8!important;}
    div.stButton>button{background:transparent!important;color:#2563EB!important;border:none!important;
      padding:4px!important;font-size:0.85rem!important;font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:48px 0 28px;">
      <div style="display:inline-flex;align-items:center;gap:7px;margin-bottom:22px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 16V4m0 0L3 8m4-4l4 4"/><path d="M17 8v12m0 0l4-4m-4 4l-4-4"/>
        </svg>
        <span style="font-size:1.1rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.25rem;font-weight:700;color:#0f172a;margin-bottom:6px;">Welcome back</h2>
      <p style="font-size:0.85rem;color:#64748b;">Enter your details to sign in</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email    = st.text_input("Email address", placeholder="name@company.com")
        password = st.text_input("Password", placeholder="••••••••", type="password")
        sub      = st.form_submit_button("Sign in", use_container_width=True)

    if sub:
        if not email or not password:
            st.error("Please fill in all fields.")
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
# REGISTER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.auth_view == "register":
    st.markdown("""
    <style>
    body,.stApp,[data-testid="stAppViewContainer"],section.main,[data-testid="stMain"]{background:#f0f2f5!important;}
    .block-container{padding:2rem 1rem!important;max-width:480px!important;margin:0 auto!important;}
    div[data-testid="stTextInput"] input{border-radius:8px!important;border:1.5px solid #e2e8f0!important;
      background:#fff!important;padding:11px 14px!important;color:#0f172a!important;font-size:0.875rem!important;}
    div[data-testid="stTextInput"] input:focus{border-color:#2563EB!important;
      box-shadow:0 0 0 3px rgba(37,99,235,0.08)!important;}
    div[data-testid="stTextInput"] label{font-size:0.85rem!important;font-weight:500!important;color:#374151!important;}
    div[data-testid="stFormSubmitButton"] button{width:100%!important;border-radius:8px!important;
      background:#2563EB!important;padding:11px!important;font-size:0.875rem!important;
      font-weight:700!important;color:#fff!important;border:none!important;}
    div[data-testid="stFormSubmitButton"] button:hover{background:#1d4ed8!important;}
    div.stButton>button{background:transparent!important;color:#2563EB!important;border:none!important;
      padding:4px!important;font-size:0.85rem!important;font-weight:600!important;box-shadow:none!important;}
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:36px 0 22px;">
      <div style="display:inline-flex;align-items:center;gap:7px;margin-bottom:20px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 16V4m0 0L3 8m4-4l4 4"/><path d="M17 8v12m0 0l4-4m-4 4l-4-4"/>
        </svg>
        <span style="font-size:1.1rem;font-weight:700;color:#0f172a;">CareerSync</span>
      </div>
      <h2 style="font-size:1.25rem;font-weight:700;color:#0f172a;margin-bottom:6px;">Create your account</h2>
      <p style="font-size:0.85rem;color:#64748b;">Your own private dashboard synced to Gmail</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("register_form"):
        name  = st.text_input("Full name",        placeholder="John Smith")
        r_em  = st.text_input("Email address",    placeholder="name@company.com")
        r_pw  = st.text_input("Password",         placeholder="Min 6 characters", type="password")
        r_pw2 = st.text_input("Confirm password", placeholder="Repeat password",  type="password")
        st.markdown("""
        <div style="margin:12px 0 6px;padding-top:12px;border-top:1px solid #f1f5f9;">
          <p style="font-size:0.75rem;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px;">📬 Gmail Sync</p>
          <p style="font-size:0.75rem;color:#94a3b8;margin:0 0 6px;">
            <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color:#2563EB;font-weight:600;">Get App Password →</a>
            App: Mail · Device: Other · Name: CareerSync
          </p>
        </div>
        """, unsafe_allow_html=True)
        gm_acc  = st.text_input("Your Gmail address",  placeholder="yourname@gmail.com")
        gm_pass = st.text_input("Gmail App Password",  placeholder="abcd efgh ijkl mnop", type="password")
        sub     = st.form_submit_button("Create Account", use_container_width=True)

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
    <div style="text-align:center;padding:16px 0;font-size:0.72rem;color:#94a3b8;">
      © 2026 CareerSync Inc. All rights reserved.</div>
    """, unsafe_allow_html=True)