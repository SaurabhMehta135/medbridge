"""
MedBridge — Unified Streamlit App

Single entry point for both patients and doctors.
Run with: streamlit run patient_app/app.py --server.port 8501
"""

import streamlit as st
import requests
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MedBridge",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Healthcare Design System CSS
# ---------------------------------------------------------------------------

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
p, h1, h2, h3, h4, h5, h6, div, span, input, button, textarea { font-family: 'Inter', sans-serif; }
.stApp { background-color: transparent !important; }
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
button[kind="deployButton"] { display: none !important; }
div[data-testid="stDecoration"] { display: none; }
div[data-testid="stSidebarNav"] { display: none; }
h1, h2, h3 { color: #0F172A !important; }

/* ── Section Header ── */
.section-header { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #94A3B8; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(226, 232, 240, 0.5); }

/* ── Glass Cards (Bento Aesthetic) ── */
.medbridge-card { background: rgba(255,255,255,0.6); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border-radius: 20px; padding: 32px; border: 1px solid rgba(255,255,255,0.5); box-shadow: 0 12px 40px rgba(0,0,0,0.05); margin-bottom: 24px; }
.metric-card { background: rgba(255,255,255,0.6); backdrop-filter: blur(24px); border-radius: 20px; padding: 24px 20px; border: 1px solid rgba(255,255,255,0.5); text-align: center; transition: transform 0.3s; box-shadow: 0 12px 40px rgba(0,0,0,0.05); position: relative; overflow: hidden; }
.metric-card:hover { transform: translateY(-4px); }
.metric-card .metric-value { font-size: 2.2rem; font-weight: 800; color: #0F172A; margin: 8px 0 4px 0; line-height: 1; }
.metric-card .metric-label { font-size: 0.85rem; font-weight: 500; color: #64748B; }
.metric-card .metric-icon { font-size: 1.5rem; }
.metric-card .metric-stripe { position: absolute; top: 0; left: 0; right: 0; height: 4px; }

/* ── Patient Left Rail ── */
.patient-shell { align-items: flex-start; }
#patient-rail-anchor { display: none; }
div[data-testid="column"]:has(#patient-rail-anchor) {
    background: #FFFFFF;
    border-right: 1px solid #F1F5F9;
    padding: 28px 20px 22px 28px;
    min-height: calc(100vh - 120px);
    position: sticky;
    top: 12px;
    display: flex;
    flex-direction: column;
}
div[data-testid="column"]:has(#patient-rail-anchor) > div {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    padding-left: 8px;
}
.patient-rail-profile {
    padding: 24px 8px 14px 8px;
}
.patient-rail-name {
    font-size: 1rem;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 6px;
    word-break: break-word;
}
.patient-rail-email {
    font-size: 0.82rem;
    color: #60A5FA;
    word-break: break-word;
    text-decoration: underline;
}
.patient-rail-divider {
    height: 1px;
    background: rgba(148, 163, 184, 0.18);
    margin: 14px 0;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton {
    margin-bottom: 4px;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button {
    justify-content: flex-start !important;
    text-align: left !important;
    min-height: 42px !important;
    padding: 8px 14px !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button p {
    font-size: 0.95rem !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="secondary"] {
    background: transparent !important;
    padding: 0 !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="secondary"]::before {
    display: none !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="secondary"]::after {
    inset: 0 !important;
    border-radius: 10px !important;
    background: transparent !important;
    backdrop-filter: none !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="secondary"]:hover::after {
    background: #F1F5F9 !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="secondary"] p {
    color: #334155 !important;
    font-weight: 500 !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="primary"] {
    padding: 0 !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="primary"]::after {
    inset: 0 !important;
    border-radius: 10px !important;
    background: #0EA5E9 !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .stButton > button[kind="primary"] p {
    font-weight: 700 !important;
}
.patient-rail-signout-gap {
    margin-top: auto;
    padding-top: 20px;
}
div[data-testid="column"]:has(#patient-rail-anchor) .patient-signout .stButton > button {
    justify-content: center !important;
    border: 1px solid #E2E8F0 !important;
    background: transparent !important;
    padding: 0 !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .patient-signout .stButton > button::before {
    display: none !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .patient-signout .stButton > button::after {
    inset: 0 !important;
    border-radius: 10px !important;
    background: white !important;
}
div[data-testid="column"]:has(#patient-rail-anchor) .patient-signout .stButton > button p {
    color: #0F172A !important;
    font-weight: 500 !important;
}

/* ── Badges ── */
.badge-high { background: #FEE2E2; color: #DC2626; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
.badge-medium { background: #FFF7ED; color: #EA580C; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
.badge-low { background: #DCFCE7; color: #16A34A; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }
.badge-info { background: #DBEAFE; color: #2563EB; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; }

/* ── Alerts ── */
.alert-danger { background: #FEE2E2; border-left: 4px solid #DC2626; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #991B1B; }
.alert-warning { background: #FFF7ED; border-left: 4px solid #EA580C; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #9A3412; }
.alert-success { background: #DCFCE7; border-left: 4px solid #16A34A; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #166534; }
.alert-info { background: #DBEAFE; border-left: 4px solid #2563EB; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 8px 0; color: #1E40AF; }
.info-box { background: #DBEAFE; border-left: 4px solid #2563EB; padding: 16px 20px; border-radius: 0 12px 12px 0; margin: 12px 0; color: #1E40AF; }

/* ── Page Headers ── */
.page-header { background: linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%); padding: 32px 36px; border-radius: 20px; color: white; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(37,99,235,0.15); position: relative; overflow: hidden; }
.page-header::before { content: ''; position: absolute; top: -50%; right: -10%; width: 200px; height: 200px; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); border-radius: 50%; }
.page-header h1 { color: white !important; margin: 0 !important; font-weight: 800; font-size: 1.8rem; position: relative; z-index: 1; }
.page-header p { color: rgba(255,255,255,0.85) !important; margin: 6px 0 0 0 !important; font-size: 1rem; position: relative; z-index: 1; }

.page-header-teal { background: linear-gradient(135deg, #0E7490 0%, #0891B2 60%, #06B6D4 100%); padding: 32px 36px; border-radius: 20px; color: white; margin-bottom: 28px; box-shadow: 0 4px 20px rgba(8,145,178,0.15); position: relative; overflow: hidden; }
.page-header-teal::before { content: ''; position: absolute; top: -50%; right: -10%; width: 200px; height: 200px; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); border-radius: 50%; }
.page-header-teal h1 { color: white !important; margin: 0 !important; font-weight: 800; font-size: 1.8rem; position: relative; z-index: 1; }
.page-header-teal p { color: rgba(255,255,255,0.85) !important; margin: 6px 0 0 0 !important; font-size: 1rem; position: relative; z-index: 1; }

/* Sub-page header (used by upload, chat, share, followups, emergency) */
.main-header { background: linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%); padding: 28px 32px; border-radius: 16px; color: white; margin-bottom: 24px; box-shadow: 0 4px 16px rgba(37,99,235,0.12); position: relative; overflow: hidden; }
.main-header::before { content: ''; position: absolute; top: -50%; right: -10%; width: 180px; height: 180px; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); border-radius: 50%; }
.main-header h1 { color: white !important; margin: 0 !important; font-weight: 800; font-size: 1.7rem; position: relative; z-index: 1; }
.main-header p { color: rgba(255,255,255,0.85) !important; margin: 4px 0 0 0 !important; font-size: 0.95rem; position: relative; z-index: 1; }

/* ── Auth ── */
.auth-left-panel { background: linear-gradient(160deg, #1E3A8A 0%, #1E40AF 30%, #2563EB 70%, #3B82F6 100%); border-radius: 24px; padding: 48px 36px; color: white; min-height: 75vh; display: flex; flex-direction: column; justify-content: center; position: relative; overflow: hidden; }
.auth-left-panel::before { content: ''; position: absolute; top: -20%; right: -15%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%); border-radius: 50%; }
.auth-left-panel::after { content: ''; position: absolute; bottom: -15%; left: -10%; width: 250px; height: 250px; background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%); border-radius: 50%; }
.auth-left-panel h1 { color: white !important; font-size: 2.5rem; font-weight: 900; margin: 0 0 8px 0 !important; position: relative; z-index: 1; letter-spacing: -1px; }
.auth-left-panel .tagline { color: rgba(255,255,255,0.8); font-size: 1.05rem; margin-bottom: 36px; position: relative; z-index: 1; line-height: 1.5; }
.auth-feature { display: flex; align-items: center; gap: 14px; padding: 14px 0; border-top: 1px solid rgba(255,255,255,0.1); position: relative; z-index: 1; }
.auth-feature-icon { width: 40px; height: 40px; background: rgba(255,255,255,0.12); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.auth-feature-text h4 { color: white !important; margin: 0 !important; font-size: 0.9rem; font-weight: 600; }
.auth-feature-text p { color: rgba(255,255,255,0.65) !important; margin: 2px 0 0 0 !important; font-size: 0.78rem; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: rgba(255,255,255,0.7) !important; backdrop-filter: blur(24px); border-right: 1px solid rgba(255,255,255,0.5); }
section[data-testid="stSidebar"] .stMarkdown { color: #475569; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #0F172A !important; }
/* Hide radio button circles, style as clean menu */
section[data-testid="stSidebar"] div.stRadio > div { flex-direction: column; gap: 4px; }
section[data-testid="stSidebar"] div.stRadio label { 
    padding: 12px 16px; 
    border-radius: 12px; 
    cursor: pointer; 
    width: 100%; 
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); 
    border: 1px solid transparent;
    margin-bottom: 2px;
}
section[data-testid="stSidebar"] div.stRadio label:hover { 
    background: #F8FAFC; 
    transform: translateX(4px);
}
section[data-testid="stSidebar"] div.stRadio label > div:first-child { display: none !important; }

/* Inactive Text */
section[data-testid="stSidebar"] div.stRadio label p { color: #64748B !important; font-weight: 500 !important; font-size: 0.95rem; }

/* Active nav item highlight (Premium Blue for patient) */
section[data-testid="stSidebar"] div.stRadio label[data-checked="true"],
section[data-testid="stSidebar"] div.stRadio label:has(input:checked),
section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(input[aria-checked="true"]),
section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(div[aria-checked="true"]) { 
    background: linear-gradient(90deg, #F0F9FF 0%, #E0F2FE 100%) !important; 
    border: 1px solid #BAE6FD !important;
    border-left: 4px solid #0284C7 !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.08) !important;
    transform: translateX(4px);
}
/* Active Text */
section[data-testid="stSidebar"] div.stRadio label[data-checked="true"] p,
section[data-testid="stSidebar"] div.stRadio label:has(input:checked) p,
section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(input[aria-checked="true"]) p,
section[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label:has(div[aria-checked="true"]) p { 
    color: #0369A1 !important; 
    font-weight: 800 !important; 
}
/* Sign out button red hover */
section[data-testid="stSidebar"] .stButton > button:hover { background: #FEF2F2 !important; color: #DC2626 !important; border-color: #FECACA !important; }

/* Animated Moving Border Buttons */
.stButton > button, .stFormSubmitButton > button { 
    border-radius: 12px !important; 
    font-weight: 600 !important; 
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important; 
    position: relative !important;
    overflow: hidden !important;
    background: transparent !important;
    padding: 3px !important;
    border: none !important;
}
.stButton > button[kind="secondary"]::after { background: rgba(255,255,255,0.7); backdrop-filter: blur(10px); }
.stButton > button[kind="secondary"]:hover::after { background: white; }
.stButton > button[kind="primary"], .stFormSubmitButton > button { box-shadow: 0 12px 24px rgba(2,132,199,0.2) !important; }
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px); box-shadow: 0 16px 36px rgba(2,132,199,0.3) !important; }

.stButton > button[kind="primary"]::before, .stFormSubmitButton > button::before {
    content: ''; position: absolute; top: -100%; left: -100%; right: -100%; bottom: -100%;
    background: conic-gradient(from 0deg, transparent 60%, rgba(2, 132, 199, 1) 85%, transparent 100%);
    animation: borderSpin 4s linear infinite; z-index: 0;
}
.stButton > button[kind="primary"]::after, .stFormSubmitButton > button::after {
    content: ''; position: absolute; inset: 3px; border-radius: 9px;
    background: #0284C7; z-index: 1;
}
.stButton > button[kind="primary"] p, .stFormSubmitButton > button p { position: relative; z-index: 2; color: white !important; }
@keyframes borderSpin { 100% { transform: rotate(360deg); } }

/* Inputs */
.stTextInput > div > div > input, .stSelectbox > div > div > div { background: rgba(255,255,255,0.7) !important; backdrop-filter: blur(12px); border: 1.5px solid rgba(255,255,255,0.5) !important; border-radius: 12px !important; color: #0F172A !important; }
.stTextInput > div > div > input:focus { border-color: #0284C7 !important; box-shadow: 0 0 0 3px rgba(2,132,199,0.12) !important; }
.stTextInput > label, .stSelectbox > label { color: #475569 !important; font-weight: 600 !important; font-size: 0.85rem !important; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: rgba(255,255,255,0.4); backdrop-filter: blur(12px); padding: 4px; border-radius: 12px; border: none; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 20px; font-weight: 500; color: #64748B; background: transparent; border: none; }
.stTabs [aria-selected="true"] { background: white !important; color: #0284C7 !important; font-weight: 700 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"] { display: none; }

.streamlit-expanderHeader { background: rgba(255,255,255,0.6) !important; border-radius: 12px !important; color: #0F172A !important; border: 1px solid rgba(255,255,255,0.5) !important; }
.streamlit-expanderHeader:hover { background: rgba(255,255,255,0.9) !important; }
div[data-testid="stExpanderDetails"] { background: rgba(255,255,255,0.4) !important; border-radius: 0 0 12px 12px !important; padding: 16px !important; border: 1px solid rgba(255,255,255,0.5); border-top: none; }

[data-testid="stChatMessage"] { background: rgba(255,255,255,0.6); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.5); border-radius: 16px; padding: 16px; margin-bottom: 8px; }
[data-testid="stChatInput"] { background: rgba(255,255,255,0.7) !important; backdrop-filter: blur(12px); border: 1.5px solid rgba(255,255,255,0.5) !important; border-radius: 16px !important; }
[data-testid="stChatInput"] textarea { color: #0F172A !important; }
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { background: transparent !important; }

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

/* ── File Uploader ── */
[data-testid="stFileUploader"] { background: white; border: 2px dashed #CBD5E1; border-radius: 16px; padding: 20px; transition: all 0.3s; }
[data-testid="stFileUploader"]:hover { border-color: #2563EB; background: #EFF6FF; }

/* Hide 'Press Enter to submit form' hint but keep the button visible */
div[data-testid="stFormSubmitButton"] > div {
    display: none !important;
}

/* ── Misc ── */
.stDivider { border-color: #E2E8F0 !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F8FAFC; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
[data-baseweb="popover"] { background: white !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; }
[data-baseweb="menu"] { background: white !important; }
[data-baseweb="menu"] li { color: #0F172A !important; }
[data-baseweb="menu"] li:hover { background: #EFF6FF !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #E2E8F0 !important; border-radius: 16px !important; background: white; }
.stDateInput > div > div > input { background: white !important; border: 1.5px solid #E2E8F0 !important; border-radius: 10px !important; color: #0F172A !important; }

/* ── Emergency Card ── */
.emergency-card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; max-width: 600px; margin: 0 auto; }
.emergency-card-header { background: linear-gradient(135deg, #DC2626, #EF4444); padding: 20px 28px; display: flex; align-items: center; justify-content: space-between; }
.emergency-card-header h3 { color: white !important; margin: 0 !important; font-weight: 800; letter-spacing: 1px; font-size: 0.95rem; }
.emergency-card-body { padding: 28px; }
.emergency-card-field { padding: 10px 0; border-bottom: 1px solid #F1F5F9; }
.emergency-card-field .label { font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; }
.emergency-card-field .value { font-size: 0.95rem; font-weight: 600; color: #0F172A; margin-top: 2px; }

/* ── Access Code ── */
.access-code-display { background: linear-gradient(135deg, #1E40AF, #2563EB); border-radius: 16px; padding: 32px; text-align: center; color: white; margin: 16px 0; box-shadow: 0 8px 24px rgba(37,99,235,0.2); }
.access-code-display .code { font-size: 2.8rem; font-weight: 900; letter-spacing: 6px; margin: 12px 0; }

/* ── Patient Card ── */
.patient-card-light { background: white; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 22px; margin: 8px 0; transition: all 0.2s; }
.patient-card-light:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); border-color: #CBD5E1; }

/* ── Risk Bar ── */
.risk-bar-bg { background: #F1F5F9; border-radius: 6px; height: 8px; width: 100%; overflow: hidden; }
.risk-bar-fill { height: 100%; border-radius: 6px; transition: width 0.8s ease; }

/* ── Risk Card Grid ── */
.risk-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 8px; }
.risk-card-equal { background: white; border-radius: 16px; padding: 24px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); min-height: 220px; display: flex; flex-direction: column; justify-content: center; }
.risk-card-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; flex: 1; }
.risk-card-empty .empty-icon { font-size: 2rem; opacity: 0.3; margin-bottom: 8px; }
.risk-card-empty .empty-title { font-weight: 600; color: #94A3B8; font-size: 0.9rem; margin-bottom: 4px; }
.risk-card-empty .empty-subtitle { color: #CBD5E1; font-size: 0.8rem; }

/* Document card for list items */
.doc-list-card { background: white; border: 1px solid #E2E8F0; border-radius: 14px; padding: 16px 20px; margin-bottom: 8px; transition: all 0.2s; cursor: pointer; }
.doc-list-card:hover { background: #FAFBFC; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.doc-icon-circle { width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }

/* Chat empty state */
.chat-empty-state { text-align: center; padding: 60px 24px; }
.chat-empty-state .icon { font-size: 3rem; opacity: 0.2; margin-bottom: 16px; }
.chat-empty-state .title { font-weight: 700; color: #94A3B8; font-size: 1.1rem; margin-bottom: 6px; }
.chat-empty-state .subtitle { color: #CBD5E1; font-size: 0.9rem; }

/* Suggested question pills */
.suggest-pill { background: #DBEAFE; border: 1px solid #93C5FD; color: #2563EB; border-radius: 20px; padding: 10px 18px; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all 0.2s; display: inline-block; text-align: center; }
.suggest-pill:hover { background: #BFDBFE; border-color: #60A5FA; }
.suggest-pill-teal { background: #CCFBF1; border: 1px solid #99F6E4; color: #0891B2; border-radius: 20px; padding: 10px 18px; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: all 0.2s; display: inline-block; text-align: center; }
.suggest-pill-teal:hover { background: #A7F3D0; border-color: #5EEAD4; }

/* Filter pill (disabled state) */
.filter-pill { background: #F1F5F9; color: #94A3B8; border-radius: 20px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; display: inline-block; margin-right: 6px; border: 1px solid #E2E8F0; }

/* Access code card */
.code-card { background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; margin-bottom: 12px; }
.code-card .code-text { font-size: 1.8rem; font-weight: 900; letter-spacing: 4px; color: #2563EB; text-align: center; background: #EFF6FF; padding: 16px; border-radius: 12px; margin-bottom: 12px; }

/* Hide slider value display above track */
.stSlider [data-testid="stTickBarMin"], .stSlider [data-testid="stTickBarMax"] { display: none; }
.stSlider [data-testid="stThumbValue"] { display: none; }

/* ── Section Spacing ── */
.section-spacer { margin-bottom: 28px; }

/* ── Summary Card ── */
.summary-card { background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; margin-bottom: 10px; transition: all 0.2s; }
.summary-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.summary-card .doc-name { font-weight: 700; color: #0F172A; font-size: 0.9rem; margin-bottom: 4px; }
.summary-card .doc-preview { color: #64748B; font-size: 0.82rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.summary-card .doc-meta { font-size: 0.75rem; color: #94A3B8; margin-top: 8px; }

/* ── Follow-up Empty State ── */
.followup-empty { background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 40px 24px; text-align: center; }
.followup-empty .check-icon { font-size: 2.5rem; margin-bottom: 12px; }
.followup-empty .title { font-weight: 700; color: #16A34A; font-size: 1.1rem; margin-bottom: 4px; }
.followup-empty .subtitle { color: #94A3B8; font-size: 0.85rem; }

/* ── Mobile Android Responsive Tweaks ── */
@media screen and (max-width: 768px) {
    .patient-shell { display: block; }
    div[data-testid="column"]:has(#patient-rail-anchor) {
        position: static;
        min-height: auto;
        border-radius: 18px;
        margin-bottom: 18px;
        padding: 20px 14px;
    }
    .main-header { padding: 20px 16px; margin: 0 -10px 16px -10px; border-radius: 12px; }
    .main-header h1 { font-size: 1.3rem; }
    .auth-left-panel { padding: 32px 20px; min-height: auto; margin-bottom: 24px; border-radius: 16px; }
    .auth-left-panel h1 { font-size: 1.8rem; }
    .auth-feature { flex-direction: column; align-items: flex-start; gap: 8px; }
    .risk-grid { grid-template-columns: 1fr; gap: 12px; }
    .risk-card-equal { padding: 16px; min-height: auto; }
    .metric-card .metric-value { font-size: 1.6rem; }
    .stTabs [data-baseweb="tab"] { padding: 8px 12px; font-size: 0.8rem; }
    .emergency-card-body { padding: 16px; }
    div[data-testid="stSidebarNav"] { display: block !important; } /* Let them use sidebar on mobile */
}
</style>
<div class="aurora-bg"></div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "reg_role" not in st.session_state:
    st.session_state.reg_role = "patient"
if "login_step" not in st.session_state:
    st.session_state.login_step = "email"
if "login_email" not in st.session_state:
    st.session_state.login_email = ""
if "patient_page" not in st.session_state:
    st.session_state.patient_page = "🏠 Dashboard"


def _config_value(name: str, default: str = "") -> str:
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


API_BASE = _config_value("BACKEND_URL", "http://127.0.0.1:8000")
DOCTOR_PORTAL_URL = _config_value("DOCTOR_PORTAL_URL", "http://localhost:8502")


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

def api_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def do_login(email, password):
    r = requests.post(f"{API_BASE}/api/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        st.session_state.token = r.json()["access_token"]
        me = requests.get(f"{API_BASE}/api/auth/me", headers=api_headers())
        if me.status_code == 200:
            user = me.json()
            if user.get("role") == "doctor":
                st.session_state.token = None
                return False, f"Access Denied: Account registered as '{user.get('role').capitalize()}'. Patient portal access is strictly prohibited."
            st.session_state.user = user
            return True, "Welcome back!"
    return False, "Invalid email or password"


def do_register(data):
    r = requests.post(f"{API_BASE}/api/auth/register", json=data)
    if r.status_code == 201:
        return True, "Account created successfully! You can now log in."
    return False, r.json().get("detail", "Registration failed")


def do_reset_password(email, new_password):
    r = requests.post(f"{API_BASE}/api/auth/reset-password", json={"email": email, "new_password": new_password})
    if r.status_code == 200:
        return True, r.json().get("message", "Password reset successfully!")
    return False, r.json().get("detail", "Reset failed")


def logout():
    st.session_state.token = None
    st.session_state.user = None


# ---------------------------------------------------------------------------
# Auth Page — Split Layout
# ---------------------------------------------------------------------------

def show_auth_page():
    st.markdown("""<style>
        [data-testid="collapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>""", unsafe_allow_html=True)

    col_brand, col_form = st.columns([2, 3], gap="large")

    # ── Left Brand Panel ──
    with col_brand:
        st.markdown("""
        <div class="auth-left-panel">
            <h1>🏥 MedBridge</h1>
            <p class="tagline">Your complete health story, in one place.</p>
            <div class="auth-feature">
                <div class="auth-feature-icon">🔒</div>
                <div class="auth-feature-text">
                    <h4>Secure & Private</h4>
                    <p>Healthcare-grade encryption for all your records</p>
                </div>
            </div>
            <div class="auth-feature">
                <div class="auth-feature-icon">🤖</div>
                <div class="auth-feature-text">
                    <h4>AI-Powered Analysis</h4>
                    <p>Instant plain-English summaries of complex reports</p>
                </div>
            </div>
            <div class="auth-feature">
                <div class="auth-feature-icon">📅</div>
                <div class="auth-feature-text">
                    <h4>Smart Follow-ups</h4>
                    <p>Never miss an appointment or test again</p>
                </div>
            </div>
            <div class="auth-feature">
                <div class="auth-feature-icon">🔗</div>
                <div class="auth-feature-text">
                    <h4>Share with Doctors</h4>
                    <p>Secure time-limited access codes for your physicians</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Right Form Panel ──
    with col_form:
        st.markdown("<div style='padding: 48px 20px 20px 20px; max-width: 420px;'>", unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["  Sign In  ", "  Create Account  "])

        # ── LOGIN TAB ──
        with tab_login:
            login_step = st.session_state.login_step

            if login_step == "email":
                st.markdown('<h2 style="color:#0F172A; margin-bottom:4px;">Sign in</h2>', unsafe_allow_html=True)
                st.markdown('<p style="color:#64748B; margin-bottom:20px;">to continue to MedBridge</p>', unsafe_allow_html=True)

                with st.form("login_email_form"):
                    email = st.text_input("Email or phone number", placeholder="you@example.com or 555-0100")
                    submitted = st.form_submit_button("Next", type="primary", use_container_width=True)
                    if submitted:
                        if not email:
                            st.error("Please enter your email")
                        else:
                            st.session_state.login_email = email
                            st.session_state.login_step = "password"
                            st.rerun()

            elif login_step == "password":
                st.markdown('<h2 style="color:#0F172A; margin-bottom:4px;">Welcome back</h2>', unsafe_allow_html=True)
                st.markdown(f'<p style="color:#64748B; margin-bottom:20px;">📧 {st.session_state.login_email}</p>', unsafe_allow_html=True)

                with st.form("login_pass_form"):
                    password = st.text_input("Enter your password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                    if submitted:
                        if not password:
                            st.error("Please enter your password")
                        else:
                            ok, msg = do_login(st.session_state.login_email, password)
                            if ok:
                                st.success(msg)
                                st.session_state.login_step = "email"
                                st.session_state.login_email = ""
                                st.rerun()
                            else:
                                st.error(msg)

                col_back, col_forgot = st.columns([1, 1])
                with col_back:
                    if st.button("← Back", key="back_to_email", type="secondary"):
                        st.session_state.login_step = "email"
                        st.rerun()
                with col_forgot:
                    if st.button("Forgot password?", key="forgot_pw_btn", type="secondary"):
                        st.session_state.login_step = "reset"
                        st.rerun()

            elif login_step == "reset":
                st.markdown('<h2 style="color:#0F172A; margin-bottom:4px;">Reset password</h2>', unsafe_allow_html=True)
                st.markdown('<p style="color:#64748B; margin-bottom:20px;">Enter your email and choose a new password</p>', unsafe_allow_html=True)

                with st.form("reset_form"):
                    reset_email = st.text_input("Email address", value=st.session_state.login_email, placeholder="you@example.com", key="reset_email")
                    new_pass = st.text_input("New Password", type="password", placeholder="Min 6 characters", key="reset_pass")
                    confirm_pass = st.text_input("Confirm New Password", type="password", placeholder="Re-enter password", key="reset_confirm")
                    st.markdown("")
                    submitted = st.form_submit_button("Reset Password", type="primary")
                    if submitted:
                        if not reset_email or not new_pass or not confirm_pass:
                            st.error("Please fill in all fields")
                        elif len(new_pass) < 6:
                            st.error("Password must be at least 6 characters")
                        elif new_pass != confirm_pass:
                            st.error("Passwords do not match")
                        else:
                            ok, msg = do_reset_password(reset_email, new_pass)
                            if ok:
                                st.success(msg)
                                st.session_state.login_step = "email"
                                st.rerun()
                            else:
                                st.error(msg)

                if st.button("← Back to Sign In", key="back_login_btn", type="secondary"):
                    st.session_state.login_step = "email"
                    st.rerun()

        # ── REGISTER TAB ──
        with tab_register:
            st.markdown("")
            with st.form("register_form"):
                name_col1, name_col2 = st.columns(2)
                with name_col1:
                    first_name = st.text_input("First Name", placeholder="Alice")
                with name_col2:
                    last_name = st.text_input("Last Name", placeholder="Johnson")
                email = st.text_input("Email address", placeholder="alice@example.com", key="reg_email_p")
                phone = st.text_input("Phone Number", placeholder="555-0100", key="reg_phone_p")
                password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="reg_pass_p")

                st.markdown("")
                submitted = st.form_submit_button("Create Patient Account", type="primary")
                if submitted:
                    if not first_name or not last_name or not email or not password or not phone:
                        st.error("Please fill in all fields")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        data = {
                            "full_name": f"{first_name.strip()} {last_name.strip()}",
                            "email": email, "password": password, "role": "patient",
                            "phone_number": phone.strip(),
                        }
                        ok, msg = do_register(data)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

        st.markdown('</div>', unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <p style="text-align:center; color:#94A3B8; font-size:0.75rem; margin-top:32px;">
            🔒 Your data is encrypted and HIPAA-compliant.<br>MedBridge © 2026
        </p>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dashboard (Logged In)
# ---------------------------------------------------------------------------

def show_dashboard():
    user = st.session_state.user
    st.markdown("""<style>
        header[data-testid="stHeader"] {
            visibility: visible !important;
            height: auto !important;
        }
        header[data-testid="stHeader"] > div {
            background: transparent !important;
        }
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
        }
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            min-width: 260px !important;
        }
        @media screen and (min-width: 769px) {
            section[data-testid="stSidebar"] {
                width: 260px !important;
            }
        }
    </style>""", unsafe_allow_html=True)

    if user["role"] == "patient":
        _show_patient_view(user)
    else:
        _show_doctor_view(user)


def _show_patient_view(user):
    nav_items = [
        "🏠 Dashboard",
        "📄 My Documents",
        "💬 Health Assistant",
        "📅 Follow-ups",
        "🔗 Share Records",
        "🚨 Emergency Card",
    ]

    if st.session_state.patient_page not in nav_items:
        st.session_state.patient_page = "🏠 Dashboard"

    rail_col, content_col = st.columns([1.08, 4.35], gap="large")
    with rail_col:
        st.markdown('<div id="patient-rail-anchor"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="patient-rail-profile">
            <div class="patient-rail-name">👤 {user['full_name']}</div>
            <div class="patient-rail-email">{user["email"]}</div>
        </div>
        <div class="patient-rail-divider"></div>
        """, unsafe_allow_html=True)

        for idx, item in enumerate(nav_items):
            button_type = "primary" if st.session_state.patient_page == item else "secondary"
            if st.button(item, key=f"patient_nav_left_{idx}", use_container_width=True, type=button_type):
                st.session_state.patient_page = item
                st.rerun()

        st.markdown('<div class="patient-rail-signout-gap"></div><div class="patient-rail-divider"></div><div class="patient-signout">', unsafe_allow_html=True)
        if st.button("🚪 Sign Out", key="patient_signout_left", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    page = st.session_state.patient_page

    with content_col:
        if page == "🏠 Dashboard":
            _patient_dashboard(user)
        elif page == "📅 Follow-ups":
            from patient_app.pages.followups import show_followup_page
            show_followup_page(API_BASE, api_headers)
        elif page == "📄 My Documents":
            from patient_app.pages.upload import show_upload_page
            show_upload_page(API_BASE, api_headers)
        elif page == "💬 Health Assistant":
            from patient_app.pages.chat import show_chat_page
            show_chat_page(API_BASE, api_headers)
        elif page == "🔗 Share Records":
            from patient_app.pages.share import show_share_page
            show_share_page(API_BASE, api_headers)
        elif page == "🚨 Emergency Card":
            from patient_app.pages.emergency_card import show_emergency_card
            show_emergency_card()


def _patient_dashboard(user):
    # Greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    st.markdown(f"""
    <div class="page-header">
        <h1>{greeting}, {user["full_name"].split()[0]}! 👋</h1>
        <p>Here's your health overview for today</p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch data
    try:
        docs = requests.get(f"{API_BASE}/api/patient/documents", headers=api_headers()).json()
        codes = requests.get(f"{API_BASE}/api/patient/access-codes", headers=api_headers()).json()
        alerts = requests.get(f"{API_BASE}/api/alerts/{user['id']}", headers=api_headers()).json()
        risk_data = requests.get(f"{API_BASE}/api/patient/risk-score", headers=api_headers()).json()
    except Exception:
        docs, codes, alerts, risk_data = [], [], [], {}

    # Metric Cards
    try:
        fups = requests.get(f"{API_BASE}/api/patient/followups", headers=api_headers()).json()
    except Exception:
        fups = []

    today = datetime.now().date()
    overdue_num = sum(1 for f in fups if f["status"] == "pending" and f.get("due_date") and datetime.strptime(f["due_date"], "%Y-%m-%d").date() < today)
    meds_text = user.get("medications") or ""
    med_count = len([m for m in meds_text.split(",") if m.strip()]) if meds_text else 0
    allergy_text = user.get("allergies") or ""
    allergy_count = len([a for a in allergy_text.split(",") if a.strip()]) if allergy_text else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #2563EB;"></div>
            <div class="metric-icon">📄</div><div class="metric-value">{len(docs)}</div>
            <div class="metric-label">Documents</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #7C3AED;"></div>
            <div class="metric-icon">💊</div><div class="metric-value">{med_count}</div>
            <div class="metric-label">Medications</div></div>""", unsafe_allow_html=True)
    with col3:
        fup_badge = f' <span class="badge-high">{overdue_num} overdue</span>' if overdue_num > 0 else ""
        pending_fups = sum(1 for f in fups if f["status"] in ("pending", "overdue"))
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #EA580C;"></div>
            <div class="metric-icon">📅</div><div class="metric-value">{pending_fups}</div>
            <div class="metric-label">Follow-ups{fup_badge}</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-icon">⚠️</div><div class="metric-value">{allergy_count}</div>
            <div class="metric-label">Allergies</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    # Health Risk Assessment
    if risk_data:
        st.markdown('<p class="section-header">🛡️ Health Risk Assessment</p>', unsafe_allow_html=True)
        has_data = any(risk_data.get(d, {}).get("status") == "CALCULATED" for d in ["cardiovascular", "diabetes", "kidney"])
        if not has_data:
            st.markdown('<div class="alert-info">📊 Upload your lab reports to see your personalized health risk assessment.</div>', unsafe_allow_html=True)
        else:
            # Build all 3 risk cards as equal-width HTML grid
            dims = [("Cardiovascular", "cardiovascular", "❤️"), ("Diabetes", "diabetes", "🩸"), ("Kidney Function", "kidney", "🫘")]
            cards_html = '<div class="risk-grid">'
            for title, key, icon in dims:
                data = risk_data.get(key, {})
                if data.get("status") == "INSUFFICIENT_DATA" or data.get("status") != "CALCULATED":
                    cards_html += f'''
                    <div class="risk-card-equal" style="border-left: 4px solid #E2E8F0;">
                        <div class="risk-card-empty">
                            <div class="empty-icon">{icon}</div>
                            <div class="empty-title">{title}</div>
                            <div class="empty-subtitle">Not enough data</div>
                        </div>
                    </div>'''
                else:
                    score = data["score"]
                    lvl = data["level"]
                    color = "#DC2626" if lvl == "HIGH" else "#EA580C" if lvl == "MEDIUM" else "#16A34A"
                    badge_cls = "badge-high" if lvl == "HIGH" else "badge-medium" if lvl == "MEDIUM" else "badge-low"
                    cards_html += f'''
                    <div class="risk-card-equal" style="border-left: 4px solid {color};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#0F172A;">{icon} {title}</strong>
                            <span class="{badge_cls}">{lvl}</span>
                        </div>
                        <h2 style="margin:12px 0 8px 0; color:{color}; font-size:2rem;">{score}%</h2>
                        <div class="risk-bar-bg"><div class="risk-bar-fill" style="width:{score}%; background:{color};"></div></div>
                    </div>'''
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)

            # Expander details below the grid for cards that have data
            detail_cols = st.columns(3)
            for col, (title, key, icon) in zip(detail_cols, dims):
                with col:
                    data = risk_data.get(key, {})
                    if data.get("status") != "CALCULATED":
                        continue
                    with st.expander(f"What this means"):
                        for rf in data["risk_factors"]:
                            st.markdown(f"⚠️ **{rf['factor']}**: {rf['value']}")
                        for pf in data["protective_factors"]:
                            st.markdown(f"✅ **{pf['factor']}**: {pf['value']}")
                        if data["discuss"]:
                            st.markdown("**Discuss with your doctor:**")
                            for i, d_item in enumerate(data["discuss"], 1):
                                st.markdown(f"{i}. {d_item}")

            st.caption("⚠️ *This is an automated assessment. Always consult a healthcare professional.*")

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # Two-column: Summaries + Follow-ups
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<p class="section-header">📝 Recent Report Summaries</p>', unsafe_allow_html=True)
        summarized_docs = [d for d in docs if d.get("patient_summary")]
        if summarized_docs:
            for doc in summarized_docs[:3]:
                doc_icon = {"lab_report": "🔬", "prescription": "💊", "discharge_summary": "🏥", "imaging": "📸", "pathology": "🧫", "consultation_note": "📝", "vaccination": "💉"}.get(doc.get("doc_type", ""), "📄")
                preview = (doc["patient_summary"][:120] + "...") if len(doc["patient_summary"]) > 120 else doc["patient_summary"]
                uploaded = doc.get("uploaded_at", "")
                if uploaded:
                    uploaded = uploaded.split("T")[0]
                st.markdown(f'''
                <div class="summary-card">
                    <div style="display:flex; align-items:flex-start; gap:12px;">
                        <div style="font-size:1.5rem; flex-shrink:0; margin-top:2px;">{doc_icon}</div>
                        <div style="flex:1; min-width:0;">
                            <div class="doc-name">{doc["original_filename"]}</div>
                            <div class="doc-preview">{preview}</div>
                            <div class="doc-meta">{uploaded}</div>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                with st.expander(f"View Full Summary — {doc['original_filename']}"):
                    st.info(doc["patient_summary"])
                    if st.button("🔄 Regenerate", key=f"dash_regen_{doc['id']}"):
                        with st.spinner("Analyzing your report..."):
                            r_regen = requests.post(f"{API_BASE}/api/patient/documents/{doc['id']}/regenerate-summary", headers=api_headers())
                            if r_regen.status_code == 200:
                                st.success("Summary Regenerated!")
                                st.rerun()
        else:
            st.markdown('<div class="alert-info">No summaries yet. Upload a document to get started.</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<p class="section-header">📅 Follow-up Tracker</p>', unsafe_allow_html=True)
        upcoming_num = sum(1 for f in fups if f["status"] == "pending" and f.get("due_date") and 0 <= (datetime.strptime(f["due_date"], "%Y-%m-%d").date() - today).days <= 28)
        comp_num = sum(1 for f in fups if f["status"] == "completed")

        if overdue_num > 0:
            st.markdown(f'<div class="alert-danger"><strong>🔴 {overdue_num} Overdue</strong> — Please schedule these items.</div>', unsafe_allow_html=True)
        if upcoming_num > 0:
            st.markdown(f'<div class="alert-warning"><strong>🟡 {upcoming_num} Upcoming</strong> — Due within 4 weeks.</div>', unsafe_allow_html=True)
        if comp_num > 0:
            st.markdown(f'<div class="alert-success"><strong>✅ {comp_num} Completed</strong></div>', unsafe_allow_html=True)
        if not fups:
            st.markdown('''
            <div class="followup-empty">
                <div class="check-icon">✅</div>
                <div class="title">You're all caught up!</div>
                <div class="subtitle">No pending follow-ups</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # Alerts
    if alerts:
        st.markdown('<p class="section-header">⚠️ Health Alerts</p>', unsafe_allow_html=True)
        for alert in alerts:
            severity = alert["severity"]
            cls = "alert-danger" if severity == "critical" else "alert-warning" if severity == "warning" else "alert-info"
            icon = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "ℹ️"
            with st.expander(f"{icon} {alert['title']}", expanded=(severity == "critical")):
                st.write(alert["description"])
                if alert.get("related_drugs"):
                    st.caption(f"Related: {', '.join(alert['related_drugs'])}")

    # Profile
    st.markdown('<p class="section-header">📋 Profile Summary</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Blood Type:** {user.get('blood_type') or 'Not set'}")
        st.markdown(f"**Allergies:** {user.get('allergies') or 'None recorded'}")
    with col2:
        st.markdown(f"**Medications:** {user.get('medications') or 'None recorded'}")
        st.markdown(f"**Emergency Contact:** {user.get('emergency_contact_name') or 'Not set'}")


# ---------------------------------------------------------------------------
# Doctor Views
# ---------------------------------------------------------------------------

def _show_doctor_view(user):
    st.markdown("""
    <div class="page-header-teal">
        <h1>Incorrect Portal</h1>
    </div>
    """, unsafe_allow_html=True)
    st.error(f"Hello Doctor! You are currently logged into the Patient Portal. Please visit **{DOCTOR_PORTAL_URL}** to access the advanced Doctor Analytics Dashboard.")
    if st.button("🚪 Sign Out", type="primary", use_container_width=True):
        logout()
        st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if st.session_state.token is None:
    show_auth_page()
else:
    show_dashboard()
