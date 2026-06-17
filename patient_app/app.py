"""
MedBridge — Patient Streamlit App (Main Entry Point)

Run with: streamlit run patient_app/app.py --server.port 8501
"""

import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="MedBridge",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.styles import load_css
load_css()


# ---------------------------------------------------------------------------
# Session State Initialization
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
    st.session_state.patient_page = "Dashboard"

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

from components.auth import show_auth_page
from components.dashboard import show_dashboard

if st.session_state.token is None:
    show_auth_page()
else:
    show_dashboard()
