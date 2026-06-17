"""
MedBridge — Doctor Streamlit App (Main Entry Point)

Run with: streamlit run doctor_app/app.py --server.port 8502
"""

import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="MedBridge — Doctor Portal",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load UI styles
from core.styles import load_css
load_css()

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

if "dr_token" not in st.session_state:
    st.session_state.dr_token = None
if "dr_user" not in st.session_state:
    st.session_state.dr_user = None
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = None
if "dr_login_email" not in st.session_state:
    st.session_state.dr_login_email = ""


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

from components.auth import show_auth_page
from components.dashboard import show_dashboard

if st.session_state.dr_token is None:
    show_auth_page()
else:
    show_dashboard()
