import streamlit as st
from core.api_client import api_client
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.icons import icon

def login_handler(email, password):
    try:
        data = api_client.login(email, password)
        st.session_state.token = data["access_token"]
        user = api_client.get_me()
        if user.get("role") == "doctor":
            st.session_state.token = None
            return False, f"Access Denied: Account registered as '{user.get('role').capitalize()}'. Patient portal access is strictly prohibited."
        st.session_state.user = user
        return True, "Welcome back!"
    except Exception as e:
        st.session_state.token = None
        detail = "Invalid email or password"
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = e.response.json().get("detail", detail)
            except:
                pass
        return False, detail

def register_handler(data):
    try:
        api_client.register(data)
        return True, "Account created successfully! You can now log in."
    except Exception as e:
        detail = "Registration failed"
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = e.response.json().get("detail", detail)
            except:
                pass
        return False, detail

def reset_password_handler(email, new_password):
    try:
        data = api_client.reset_password(email, new_password)
        return True, data.get("message", "Password reset successfully!")
    except Exception as e:
        detail = "Reset failed"
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = e.response.json().get("detail", detail)
            except:
                pass
        return False, detail

def logout():
    st.session_state.token = None
    st.session_state.user = None

def show_auth_page():
    st.markdown("""<style>
        [data-testid="collapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="font-size: 2.5rem !important; color: #0F172A;">Patient Portal</h1>
                <p class="subtitle">Your health story, securely illuminated</p>
            </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["  Sign In  ", "  Create Account  "])

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
                st.markdown(f'<p style="color:#64748B; margin-bottom:20px;">{icon("mail", size=16, color="#64748B")} {st.session_state.login_email}</p>', unsafe_allow_html=True)

                with st.form("login_pass_form"):
                    password = st.text_input("Enter your password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                    if submitted:
                        if not password:
                            st.error("Please enter your password")
                        else:
                            ok, msg = login_handler(st.session_state.login_email, password)
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
                            ok, msg = reset_password_handler(reset_email, new_pass)
                            if ok:
                                st.success(msg)
                                st.session_state.login_step = "email"
                                st.rerun()
                            else:
                                st.error(msg)

                if st.button("← Back to Sign In", key="back_login_btn", type="secondary"):
                    st.session_state.login_step = "email"
                    st.rerun()

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
                        ok, msg = register_handler(data)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
        st.markdown(f"""
        <p style="text-align:center; color:#94A3B8; font-size:0.75rem; margin-top:32px;">
            {icon("lock", size=14, color="#94A3B8")} Your data is encrypted and HIPAA-compliant.<br>MedBridge © 2026
        </p>
        """, unsafe_allow_html=True)
