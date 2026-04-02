"""
MedBridge — Doctor Streamlit App (Main Entry Point)

Run with: streamlit run doctor_app/app.py --server.port 8502
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

st.set_page_config(
    page_title="MedBridge — Doctor Portal",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Healthcare Design System CSS — Teal Doctor Theme
# ---------------------------------------------------------------------------

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
p, h1, h2, h3, h4, h5, h6, div, span, input, button, textarea { font-family: 'Inter', sans-serif; }
.stApp { background-color: transparent !important; }
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
button[kind="deployButton"] { display: none !important; }
div[data-testid="stSidebarNav"] { display: none !important; }
h1, h2, h3 { color: #0F172A !important; }

.section-header { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #94A3B8; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(226, 232, 240, 0.5); }
.medbridge-card { background: rgba(255,255,255,0.6); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border-radius: 20px; padding: 32px; border: 1px solid rgba(255,255,255,0.5); box-shadow: 0 12px 40px rgba(0,0,0,0.05); margin-bottom: 24px; }
.metric-card { background: rgba(255,255,255,0.6); backdrop-filter: blur(24px); border-radius: 20px; padding: 24px 20px; border: 1px solid rgba(255,255,255,0.5); text-align: center; transition: transform 0.3s; box-shadow: 0 12px 40px rgba(0,0,0,0.05); position: relative; overflow: hidden; }
.metric-card:hover { transform: translateY(-4px); }
.metric-card .metric-value { font-size: 2.2rem; font-weight: 800; color: #0F172A; margin: 8px 0 4px 0; line-height: 1; }
.metric-card .metric-label { font-size: 0.85rem; font-weight: 500; color: #64748B; }
.metric-card .metric-stripe { position: absolute; top: 0; left: 0; right: 0; height: 4px; }

.badge-high { background: #FEE2E2; color: #DC2626; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
.badge-medium { background: #FFF7ED; color: #EA580C; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
.badge-low { background: #DCFCE7; color: #16A34A; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
.badge-info { background: #DBEAFE; color: #2563EB; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }

.alert-danger { background: #FEE2E2; border-left: 4px solid #DC2626; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #991B1B; }
.alert-warning { background: #FFF7ED; border-left: 4px solid #EA580C; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #9A3412; }
.alert-success { background: #DCFCE7; border-left: 4px solid #16A34A; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #166534; }
.alert-info { background: #E0F2FE; border-left: 4px solid #0891B2; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #0E7490; }
.info-box { background: #E0F2FE; border-left: 4px solid #0891B2; padding: 16px 20px; border-radius: 0 12px 12px 0; margin: 12px 0; color: #0E7490; }

.main-header { background: linear-gradient(135deg, #0E7490 0%, #0891B2 60%, #06B6D4 100%); padding: 28px 32px; border-radius: 16px; color: white; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(8,145,178,0.12); position: relative; overflow: hidden; }
.main-header::before { content: ''; position: absolute; top: -50%; right: -10%; width: 180px; height: 180px; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); border-radius: 50%; }
.main-header h1 { color: white !important; margin: 0 !important; font-weight: 800; font-size: 1.7rem; position: relative; z-index: 1; }
.main-header p { color: rgba(255,255,255,0.85) !important; margin: 4px 0 0 0 !important; font-size: 0.95rem; position: relative; z-index: 1; }

.auth-left-panel { background: linear-gradient(160deg, #134E4A 0%, #0E7490 40%, #0891B2 70%, #06B6D4 100%); border-radius: 24px; padding: 48px 36px; color: white; min-height: 92vh; display: flex; flex-direction: column; justify-content: center; position: relative; overflow: hidden; }
.auth-left-panel::before { content: ''; position: absolute; top: -20%; right: -15%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%); border-radius: 50%; }
.auth-left-panel::after { content: ''; position: absolute; bottom: -15%; left: -10%; width: 250px; height: 250px; background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%); border-radius: 50%; }
.auth-left-panel h1 { color: white !important; font-size: 2.5rem; font-weight: 900; margin: 0 0 8px 0 !important; position: relative; z-index: 1; }
.auth-left-panel .tagline { color: rgba(255,255,255,0.8); font-size: 1.05rem; margin-bottom: 36px; position: relative; z-index: 1; }
.auth-feature { display: flex; align-items: center; gap: 14px; padding: 14px 0; border-top: 1px solid rgba(255,255,255,0.1); position: relative; z-index: 1; }
.auth-feature-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.12); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.auth-feature-text h4 { color: white !important; margin: 0 !important; font-size: 0.9rem; font-weight: 600; }
.auth-feature-text p { color: rgba(255,255,255,0.65) !important; margin: 2px 0 0 0 !important; font-size: 0.78rem; }

/* Sidebar */
section[data-testid="stSidebar"] { background: rgba(255,255,255,0.7) !important; backdrop-filter: blur(24px); border-right: 1px solid rgba(255,255,255,0.5); }
section[data-testid="stSidebar"] .stMarkdown { color: #475569; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #0F172A !important; }
/* Hide radio circles, style as clean menu */
section[data-testid="stSidebar"] div.stRadio > div { flex-direction: column; gap: 4px; }
section[data-testid="stSidebar"] div.stRadio label { 
    padding: 12px 16px; border-radius: 12px; cursor: pointer; width: 100%; 
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); border: 1px solid transparent; margin-bottom: 2px;
}
section[data-testid="stSidebar"] div.stRadio label:hover { background: rgba(255,255,255,0.9); transform: translateX(4px); }
section[data-testid="stSidebar"] div.stRadio label > div:first-child { display: none !important; }

/* Inactive Text */
section[data-testid="stSidebar"] div.stRadio label p { color: #64748B !important; font-weight: 500 !important; font-size: 0.95rem; }

/* Active nav (Premium Teal for doctor) */
section[data-testid="stSidebar"] div.stRadio label[data-checked="true"],
section[data-testid="stSidebar"] div.stRadio label:has(input:checked),
section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(input[aria-checked="true"]),
section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(div[aria-checked="true"]) { 
    background: linear-gradient(90deg, #F0FDFA 0%, #CCFBF1 100%) !important; 
    border: 1px solid #99F6E4 !important; border-left: 4px solid #0891B2 !important;
    box-shadow: 0 4px 12px rgba(8, 145, 178, 0.08) !important; transform: translateX(4px);
}
section[data-testid="stSidebar"] div.stRadio label[data-checked="true"] p, section[data-testid="stSidebar"] div.stRadio label:has(input:checked) p, section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(input[aria-checked="true"]) p, section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(div[aria-checked="true"]) p { color: #0E7490 !important; font-weight: 800 !important; }

/* Sign out red hover */
section[data-testid="stSidebar"] .stButton > button:hover { background: #FEF2F2 !important; color: #DC2626 !important; border-color: #FECACA !important; }

/* Animated Moving Border Buttons */
.stButton > button, .stFormSubmitButton > button { 
    border-radius: 12px !important; font-weight: 600 !important; 
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important; 
    position: relative !important; overflow: hidden !important;
    background: transparent !important; padding: 3px !important; border: none !important;
}
.stButton > button[kind="secondary"]::after { background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); }
.stButton > button[kind="secondary"]:hover::after { background: white; }
.stButton > button[kind="primary"], .stFormSubmitButton > button { box-shadow: 0 12px 24px rgba(8,145,178,0.2) !important; }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px); box-shadow: 0 16px 36px rgba(8,145,178,0.3) !important; }

.stButton > button[kind="primary"]::before, .stFormSubmitButton > button::before {
    content: ''; position: absolute; top: -100%; left: -100%; right: -100%; bottom: -100%;
    background: conic-gradient(from 0deg, transparent 60%, rgba(8, 145, 178, 1) 85%, transparent 100%);
    animation: borderSpin 4s linear infinite; z-index: 0;
}
.stButton > button[kind="primary"]::after, .stFormSubmitButton > button::after {
    content: ''; position: absolute; inset: 3px; border-radius: 9px;
    background: #0891B2; z-index: 1;
}
.stButton > button[kind="primary"] p, .stFormSubmitButton > button p { position: relative; z-index: 2; color: white !important; }
@keyframes borderSpin { 100% { transform: rotate(360deg); } }

.stTextInput > div > div > input, .stSelectbox > div > div > div { background: #FFFFFF !important; border: 1.5px solid #CBD5E1 !important; border-radius: 12px !important; color: #0F172A !important; box-shadow: inset 0 2px 4px rgba(0,0,0,0.04) !important; transition: all 0.2s ease !important; }
.stTextInput > div > div > input:hover, .stSelectbox > div > div > div:hover { border-color: #94A3B8 !important; background: #FAFBFC !important; }
.stTextInput > div > div > input:focus { border-color: #0891B2 !important; box-shadow: inset 0 2px 4px rgba(0,0,0,0.04), 0 0 0 3px rgba(8,145,178,0.12) !important; background: #FFFFFF !important; }
.stTextInput > label, .stSelectbox > label { color: #334155 !important; font-weight: 600 !important; font-size: 0.85rem !important; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; }

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: rgba(255,255,255,0.4); backdrop-filter: blur(12px); padding: 4px; border-radius: 12px; border: none; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 20px; font-weight: 500; color: #64748B; background: transparent; border: none; }
.stTabs [aria-selected="true"] { background: white !important; color: #0891B2 !important; font-weight: 700 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"] { display: none; }

.streamlit-expanderHeader { background: rgba(255,255,255,0.6) !important; border-radius: 12px !important; color: #0F172A !important; border: 1px solid rgba(255,255,255,0.5) !important; }
.streamlit-expanderHeader:hover { background: rgba(255,255,255,0.9) !important; }
div[data-testid="stExpanderDetails"] { background: rgba(255,255,255,0.4) !important; border-radius: 0 0 12px 12px !important; padding: 16px !important; border: 1px solid rgba(255,255,255,0.5); border-top: none; }

[data-testid="stChatMessage"] { background: rgba(255,255,255,0.6); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.5); border-radius: 16px; padding: 16px; margin-bottom: 8px; }
[data-testid="stChatInput"] { background: rgba(255,255,255,0.7) !important; backdrop-filter: blur(12px); border: 1.5px solid rgba(255,255,255,0.5) !important; border-radius: 12px !important; }
[data-testid="stChatInput"] textarea { color: #0F172A !important; }
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { background: transparent !important; }

/* Hide 'Press Enter to submit form' hint but keep the button visible */
div[data-testid="stFormSubmitButton"] > div {
    display: none !important;
}

.patient-card-light { background: white; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px 18px; margin: 6px 0; transition: all 0.2s; }
.patient-card-light:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.risk-bar-bg { background: #F1F5F9; border-radius: 6px; height: 8px; width: 100%; overflow: hidden; }
.risk-bar-fill { height: 100%; border-radius: 6px; transition: width 0.8s ease; }

/* Chat empty state */
.chat-empty-state { text-align: center; padding: 60px 24px; }
.chat-empty-state .icon { font-size: 3rem; opacity: 0.2; margin-bottom: 16px; }
.chat-empty-state .title { font-weight: 700; color: #94A3B8; font-size: 1.1rem; margin-bottom: 6px; }
.chat-empty-state .subtitle { color: #CBD5E1; font-size: 0.9rem; }

.stDivider { border-color: #E2E8F0 !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F8FAFC; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
[data-baseweb="popover"] { background: white !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; }
[data-baseweb="menu"] { background: white !important; }
[data-baseweb="menu"] li { color: #0F172A !important; }
[data-baseweb="menu"] li:hover { background: #E0F2FE !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #E2E8F0 !important; border-radius: 16px !important; background: white; }

/* ── Mobile Android Responsive Tweaks ── */
@media screen and (max-width: 768px) {
    .main-header { padding: 20px 16px; margin: 0 -10px 16px -10px; border-radius: 12px; }
    .main-header h1 { font-size: 1.3rem; }
    .auth-left-panel { padding: 32px 20px; min-height: auto; margin-bottom: 24px; border-radius: 16px; }
    .auth-left-panel h1 { font-size: 1.8rem; }
    .auth-feature { flex-direction: column; align-items: flex-start; gap: 8px; }
    .metric-card { padding: 16px 12px; }
    .metric-card .metric-value { font-size: 1.6rem; margin: 4px 0; }
    .metric-card .metric-label { font-size: 0.75rem; }
    .stTabs [data-baseweb="tab"] { padding: 8px 12px; font-size: 0.8rem; }
    div[data-testid="stSidebarNav"] { display: block !important; }
/* Aurora Animation overlay injected strictly in CSS via st.markdown */
.aurora-bg {
    position: fixed; inset: -40%; z-index: -9999;
    background: 
        radial-gradient(circle at 50% 50%, rgba(10, 132, 255, 0.15) 0%, transparent 60%),
        radial-gradient(circle at 80% 20%, rgba(14, 116, 144, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 20% 80%, rgba(59, 130, 246, 0.12) 0%, transparent 50%),
        radial-gradient(circle at 50% 0%, rgba(94, 92, 230, 0.1) 0%, transparent 60%);
    filter: blur(80px);
    animation: auroraSpin 35s linear infinite, auroraBreathe 15s ease-in-out infinite alternate;
    pointer-events: none;
}
@keyframes auroraBreathe { 0% { opacity: 0.8; } 100% { opacity: 1; transform: scale(1.1); } }
</style>
<div class="aurora-bg"></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State & API
# ---------------------------------------------------------------------------

if "dr_token" not in st.session_state:
    st.session_state.dr_token = None
if "dr_user" not in st.session_state:
    st.session_state.dr_user = None
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "dr_login_email" not in st.session_state:
    st.session_state.dr_login_email = ""


def _config_value(name: str, default: str = "") -> str:
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


API_BASE = _config_value("BACKEND_URL", "http://127.0.0.1:8000")

import requests


def api_headers():
    return {"Authorization": f"Bearer {st.session_state.dr_token}"}


def login(email, password):
    r = requests.post(f"{API_BASE}/api/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        st.session_state.dr_token = r.json()["access_token"]
        me = requests.get(f"{API_BASE}/api/auth/me", headers=api_headers())
        if me.status_code == 200:
            user = me.json()
            if user["role"] != "doctor":
                st.session_state.dr_token = None
                return False, f"Access Denied: Account registered as '{user['role'].capitalize()}'. Doctor portal access is strictly prohibited."
            st.session_state.dr_user = user
            return True, "Login successful!"
    return False, "Invalid email or password"


def register(email, password, full_name, **kwargs):
    data = {"email": email, "password": password, "full_name": full_name, "role": "doctor", **kwargs}
    r = requests.post(f"{API_BASE}/api/auth/register", json=data)
    if r.status_code == 201:
        return True, "Account created! Please login."
    return False, r.json().get("detail", "Registration failed")


def logout():
    st.session_state.dr_token = None
    st.session_state.dr_user = None
    st.session_state.selected_patient = None


# ---------------------------------------------------------------------------
# Auth Page — Split Layout (Teal)
# ---------------------------------------------------------------------------

def show_auth_page():
    st.markdown("""<style>
        [data-testid="collapsedControl"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
    </style>""", unsafe_allow_html=True)

    col_brand, col_form = st.columns([2, 3], gap="large")

    with col_brand:
        st.markdown("""
        <div class="auth-left-panel">
            <h1>🩺 MedBridge</h1>
            <p class="tagline">Clinical intelligence at your fingertips.</p>
            <div class="auth-feature">
                <div class="auth-feature-icon">📊</div>
                <div class="auth-feature-text">
                    <h4>Risk Assessment</h4>
                    <p>Automated cardiovascular, diabetes & kidney risk scoring</p>
                </div>
            </div>
            <div class="auth-feature">
                <div class="auth-feature-icon">🤖</div>
                <div class="auth-feature-text">
                    <h4>Clinical AI Chat</h4>
                    <p>AI-powered analysis scoped to patient records</p>
                </div>
            </div>
            <div class="auth-feature">
                <div class="auth-feature-icon">📋</div>
                <div class="auth-feature-text">
                    <h4>Follow-up Management</h4>
                    <p>Track and manage patient follow-up items</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_form:
        st.markdown("<div style='padding: 48px 20px 20px 20px;'>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            st.markdown('<h2 style="margin-bottom:4px;">Doctor Login</h2>', unsafe_allow_html=True)
            st.markdown('<p style="color:#64748B; margin-bottom:20px;">Access your clinical dashboard</p>', unsafe_allow_html=True)
            with st.form("dr_login"):
                email = st.text_input("Email", placeholder="doctor@hospital.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
                if submitted:
                    ok, msg = login(email, password)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with tab_register:
            st.markdown('<h2 style="margin-bottom:4px;">Create Account</h2>', unsafe_allow_html=True)
            st.markdown('<p style="color:#64748B; margin-bottom:20px;">Register as a healthcare provider</p>', unsafe_allow_html=True)
            with st.form("dr_register"):
                full_name = st.text_input("Full Name (e.g., Dr. Jane Smith)")
                email = st.text_input("Email", key="dr_reg_email")
                password = st.text_input("Password", type="password", key="dr_reg_pass")
                specialty = st.selectbox("Specialty", [
                    "General Practice", "Cardiology", "Neurology", "Oncology",
                    "Orthopedics", "Pediatrics", "Psychiatry", "Dermatology",
                    "Emergency Medicine", "Internal Medicine", "Surgery", "Other",
                ])
                license_num = st.text_input("Medical License Number")
                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                if submitted:
                    kwargs = {"specialty": specialty}
                    if license_num:
                        kwargs["license_number"] = license_num
                    ok, msg = register(email, password, full_name, **kwargs)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Dashboard
# ---------------------------------------------------------------------------

def show_dashboard():
    user = st.session_state.dr_user

    with st.sidebar:
        st.markdown(f"### 🩺 {user['full_name']}")
        st.caption(f"{user.get('specialty', '')} • {user['email']}")
        st.divider()
        page = st.radio(
            "Navigate",
            ["👥 My Patients", "🔑 Enter Access Code", "📊 Dashboard", "💬 Clinical Chat"],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    if page == "📊 Dashboard":
        show_dashboard_page()
    elif page == "🔑 Enter Access Code":
        show_access_code_page()
    elif page == "👥 My Patients":
        from doctor_app.pages.patient_list import show_patient_list
        show_patient_list(API_BASE, api_headers)
    elif page == "💬 Clinical Chat":
        from doctor_app.pages.clinical_chat import show_clinical_chat
        show_clinical_chat(API_BASE, api_headers)


def show_dashboard_page():
    user = st.session_state.dr_user

    st.markdown("""
    <div class="main-header">
        <h1>Welcome, {name}! 👋</h1>
        <p>Population Analytics Dashboard — MedBridge</p>
    </div>
    """.format(name=user["full_name"]), unsafe_allow_html=True)
    
    # Quick Actions Row
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("👥 View All Patients", use_container_width=True):
            st.session_state["_dr_nav_override"] = "👥 My Patients"
            st.rerun()
    with qa2:
        if st.button("🔑 Enter Access Code", use_container_width=True, key="qa_code"):
            st.session_state["_dr_nav_override"] = "🔑 Enter Access Code"
            st.rerun()
    with qa3:
        # Trigger FHIR ZIP download
        r_zip = requests.get(f"{API_BASE}/api/doctor/fhir-export-all", headers=api_headers())
        if r_zip.status_code == 200:
            st.download_button("📊 Export All Data as FHIR", data=r_zip.content, file_name=r_zip.headers.get("Content-Disposition", "fhir.zip").split("filename=")[-1], mime="application/zip", use_container_width=True)
        else:
            st.button("📊 Export All Data as FHIR", use_container_width=True, disabled=True, help="No patients available for export")

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch Analytics
    try:
        r = requests.get(f"{API_BASE}/api/doctor/analytics", headers=api_headers())
        analytics = r.json() if r.status_code == 200 else {}
    except Exception:
        analytics = {}
        
    if not analytics or analytics.get("total_patients", 0) == 0:
        st.info("No patients linked yet. Enter an Access Code to build your patient panel.")
        return

    # SECTION 1 - Top Stats Row
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #0891B2;"></div>
            <div class="metric-value" style="color:#0891B2;">{analytics.get('total_patients', 0)}</div>
            <div class="metric-label">👥 Total Patients</div></div>""", unsafe_allow_html=True)
    with s2:
        hi_risk = analytics.get('high_risk_patients', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-value" style="color:#DC2626;">{hi_risk}</div>
            <div class="metric-label">⚠️ High Risk Patients</div></div>""", unsafe_allow_html=True)
    with s3:
        due = analytics.get('followups_due_week', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #EA580C;"></div>
            <div class="metric-value" style="color:#EA580C;">{due}</div>
            <div class="metric-label">📅 Follow-ups Due This Week</div></div>""", unsafe_allow_html=True)
    with s4:
        overdue = analytics.get('overdue_followups', 0)
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-value" style="color:#DC2626;">{overdue}</div>
            <div class="metric-label">⏰ Overdue Follow-ups</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts & Patients Needing Attention Row
    col_charts, col_attention = st.columns([2, 1], gap="large")
    
    with col_charts:
        # SECTION 3 & 4 - Condition & Risk Charts
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:10px;">📊 Condition Prevalence</p>', unsafe_allow_html=True)
            cond = analytics.get("condition_dist", {})
            if cond:
                df_cond = pd.DataFrame(list(cond.items()), columns=["Condition", "Count"]).sort_values("Count", ascending=True)
                fig_cond = px.bar(df_cond, x="Count", y="Condition", orientation='h', text="Count", color_discrete_sequence=["#3B82F6"])
                fig_cond.update_layout(margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white", xaxis=dict(showgrid=False, visible=False), yaxis=dict(title="", tickfont=dict(size=12, color="#475569")))
                fig_cond.update_traces(textposition='outside', textfont=dict(size=14, color="#0F172A", weight="bold"), marker_line_width=0, opacity=0.9)
                st.plotly_chart(fig_cond, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No condition data available yet.")
                
        with c2:
            st.markdown('<p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:10px;">🛡️ Patient Risk Distribution</p>', unsafe_allow_html=True)
            risk = analytics.get("risk_dist", {})
            if risk:
                df_risk = pd.DataFrame(list(risk.items()), columns=["Risk Level", "Count"])
                df_risk = df_risk[df_risk["Count"] > 0]
                color_map = {"High Risk": "#EF4444", "Medium Risk": "#F59E0B", "Low Risk": "#10B981", "No Data": "#CBD5E1"}
                fig_risk = px.pie(df_risk, values="Count", names="Risk Level", hole=0.5, color="Risk Level", color_discrete_map=color_map)
                fig_risk.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=True, paper_bgcolor="white", legend=dict(orientation="h", y=-0.1, font=dict(color="#475569")))
                fig_risk.update_traces(textinfo='percent', textfont_size=14, hoverinfo='label+percent+value', marker=dict(line=dict(color='#FFFFFF', width=2)))
                st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("No risk data available yet.")
                
        # SECTION 5 - Follow-up Compliance Timeline
        st.markdown('<br><hr><p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:10px;">📈 Follow-up Compliance Trends (6 Months)</p>', unsafe_allow_html=True)
        timeline = analytics.get("compliance_timeline", {})
        if timeline and (sum(timeline.get("completed", [])) > 0 or sum(timeline.get("missed", [])) > 0):
            df_line = pd.DataFrame({
                "Month": timeline["months"],
                "Completed On Time": timeline["completed"],
                "Overdue or Missed": timeline["missed"]
            })
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=df_line["Month"], y=df_line["Completed On Time"], mode='lines+markers', name='Completed On Time', line=dict(color='#10B981', width=4), marker=dict(size=8)))
            fig_line.add_trace(go.Scatter(x=df_line["Month"], y=df_line["Overdue or Missed"], mode='lines+markers', name='Overdue or Missed', line=dict(color='#EF4444', width=4), marker=dict(size=8)))
            fig_line.update_layout(
                margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", paper_bgcolor="white",
                yaxis=dict(gridcolor="#F1F5F9", title="Count"), xaxis=dict(gridcolor="#F1F5F9"),
                legend=dict(orientation="h", y=-0.2), hovermode="x unified"
            )
            st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough data yet — complete more follow-ups to see trends here.")
            
    with col_attention:
        # SECTION 2 - Patients Needing Attention
        st.markdown('<div style="background:linear-gradient(135deg, #0F172A, #1E293B); color:white; border-radius:14px 14px 0 0; padding:16px 20px;"><p style="font-weight:700; font-size:1.05rem; margin:0;">🚨 Attention Needed</p><p style="font-size:0.8rem; color:#94A3B8; margin:0;">Overdue and high urgency</p></div>', unsafe_allow_html=True)
        st.markdown('<div style="background:white; border:1px solid #E2E8F0; border-top:none; border-radius:0 0 14px 14px; padding:16px; margin-bottom:24px; box-shadow:0 4px 12px rgba(0,0,0,0.03);">', unsafe_allow_html=True)
        attention = analytics.get("attention_needed", [])
        if attention:
            for p in attention:
                tags_html = ""
                for t in p["tags"]:
                    color = "#DC2626" if "High" in t or "Overdue" in t else "#EA580C" if "New" in t else "#0891B2"
                    bg = "#FEF2F2" if color=="#DC2626" else "#FFF7ED" if color=="#EA580C" else "#ECFEFF"
                    tags_html += f'<span style="background:{bg}; color:{color}; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:600; display:inline-block; margin-bottom:4px;">{t}</span><br>'
                    
                st.markdown(f"""
<div style="background:white; border:1px solid #E2E8F0; border-radius:14px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,0.02); transition:all 0.2s;">
    <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:40px;height:40px;border-radius:10px;background:#F8FAFC;color:#0F172A;border:1px solid #E2E8F0;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:0.9rem;">
                {p['initials']}
            </div>
            <div>
                <div style="font-weight:700; color:#0F172A; font-size:1rem;">{p['name']}</div>
                <div style="color:#64748B; font-size:0.8rem;">Last active: {p['last_active']}</div>
            </div>
        </div>
    </div>
    <div>{tags_html}</div>
</div>
""", unsafe_allow_html=True)
            if st.button("View All Patients ➔", use_container_width=True, key="view_all_attn"):
                st.session_state["_dr_nav_override"] = "👥 My Patients"
                st.rerun()
        else:
            st.success("All patients are up to date ✅")
        st.markdown('</div>', unsafe_allow_html=True)
            
        # SECTION 6 - Recent Activity Feed
        st.markdown('<br><div style="background:white; border:1px solid #E2E8F0; border-radius:16px; padding:24px;"><p style="font-weight:700; color:#0F172A; font-size:1.1rem; margin-bottom:16px;">⏱️ Recent Patient Activity</p>', unsafe_allow_html=True)
        recent = analytics.get("recent_activity", [])
        if recent:
            feed_html = '<div style="border-left: 2px solid #E2E8F0; margin-left:12px; padding-left:24px;">'
            for act in recent:
                feed_html += f"""
<div style="position:relative; margin-bottom:24px;">
    <div style="position:absolute; left:-31px; top:4px; width:14px; height:14px; border-radius:50%; background:#2563EB; border:3px solid white; box-shadow:0 0 0 1px #E2E8F0;"></div>
    <div style="font-size:0.8rem; font-weight:600; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">{act['time_ago']}</div>
    <div style="font-size:0.95rem; color:#1E293B; line-height:1.5;">
        <strong style="color:#0F172A;">{act['patient_name']}</strong> {act['action']}
    </div>
</div>"""
            feed_html += '</div></div>'
            st.markdown(feed_html, unsafe_allow_html=True)
        else:
            st.info("No recent activity.")


def show_access_code_page():
    st.markdown("""
    <div class="main-header">
        <h1>🔑 Enter Access Code</h1>
        <p>Enter a code shared by your patient to access their records</p>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ How to get an access code</strong><br>
        Ask your patient to open MedBridge, go to <strong>Share Records</strong>,
        and generate an access code. They will share this code with you directly.
    </div>
    """, unsafe_allow_html=True)

    with st.form("verify_code"):
        code = st.text_input("Access Code", placeholder="MB-XXXXXX", label_visibility="collapsed", help="Enter the 8-character code your patient shared with you")
        submitted = st.form_submit_button("🔓 Verify & Connect", use_container_width=True, type="primary")

        if submitted and code:
            r = requests.post(
                f"{API_BASE}/api/doctor/verify-code",
                json={"code": code.strip()},
                headers=api_headers(),
            )
            if r.status_code == 200:
                data = r.json()
                st.success(f"✅ Access granted! Patient ID: {data['patient_id']}")
                st.balloons()
            else:
                detail = r.json().get("detail", "Verification failed")
                st.error(f"❌ {detail}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if st.session_state.dr_token is None:
    show_auth_page()
else:
    show_dashboard()
