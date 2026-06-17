import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.icons import icon, icon_label
from core.api_client import api_client

def login_handler(email, password):
    try:
        data = api_client.login(email, password)
        st.session_state.dr_token = data["access_token"]
        user = api_client.get_me()
        if user["role"] != "doctor":
            st.session_state.dr_token = None
            return False, f"Access Denied: Account registered as '{user['role'].capitalize()}'. Doctor portal access is strictly prohibited."
        st.session_state.dr_user = user
        return True, "Login successful!"
    except Exception as e:
        st.session_state.dr_token = None
        detail = "Invalid email or password"
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = e.response.json().get("detail", detail)
            except:
                pass
        return False, detail

def register_handler(email, password, full_name, **kwargs):
    try:
        data = {"email": email, "password": password, "full_name": full_name, "role": "doctor", **kwargs}
        api_client.register(data)
        return True, "Account created! Please login."
    except Exception as e:
        detail = "Registration failed"
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = e.response.json().get("detail", detail)
            except:
                pass
        return False, detail

def logout():
    st.session_state.dr_token = None
    st.session_state.dr_user = None
    st.session_state.selected_patient = None

def show_auth_page():
    st.markdown("""<style>
        [data-testid="collapsedControl"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
    </style>""", unsafe_allow_html=True)

    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="font-size: 2.5rem !important; color: #0891B2 !important;">Doctor Portal</h1>
            <p class="subtitle">Secure clinical dashboard for healthcare professionals</p>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("dr_login"):
            email = st.text_input("Email", placeholder="doctor@hospital.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            if submitted:
                ok, msg = login_handler(email, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_register:
        with st.form("dr_register"):
            full_name = st.text_input("Full Name (e.g., Dr. Jane Smith)")
            email = st.text_input("Email", key="dr_reg_email")
            phone_number = st.text_input("Phone Number", placeholder="555-0100", key="dr_reg_phone")
            password = st.text_input("Password", type="password", key="dr_reg_pass")
            specialty = st.selectbox("Specialty", [
                "General Practice", "Cardiology", "Neurology", "Oncology",
                "Orthopedics", "Pediatrics", "Psychiatry", "Dermatology",
                "Emergency Medicine", "Internal Medicine", "Surgery", "Other",
            ])
            license_num = st.text_input("Medical License Number")
            submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            if submitted:
                kwargs = {"specialty": specialty, "phone_number": phone_number}
                if license_num:
                    kwargs["license_number"] = license_num
                ok, msg = register_handler(email, password, full_name, **kwargs)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.markdown('</div></div>', unsafe_allow_html=True)
