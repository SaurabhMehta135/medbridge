"""Patient App — Record Sharing Page"""

import streamlit as st
from datetime import datetime
from core.api_client import api_client
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.icons import icon, icon_label


def show_share_page(api_base, api_headers_fn):
    st.markdown(f"""
    <div class="main-header">
        <h1>{icon('share-2', size=28, color='#0891B2')} Share Your Records</h1>
        <p>Generate time-limited access codes for your doctors</p>
    </div>
    """, unsafe_allow_html=True)

    # Create new access code
    st.markdown(f'<p class="section-header">{icon_label("plus-circle", "Generate Access Code", color="#94A3B8")}</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        hours = st.slider(
            "Access duration",
            min_value=1, max_value=720, value=24,
            help="How long should the doctor have access? (1 hour to 30 days)",
            label_visibility="collapsed",
        )
        if hours < 24:
            duration_text = f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = hours // 24
            duration_text = f"{days} day{'s' if days > 1 else ''} ({hours} hours)"
        st.markdown(f'<span style="font-size:0.85rem; color:#64748B;">{icon("timer", size=14, color="#64748B")} Duration: {duration_text}</span>', unsafe_allow_html=True)

    with col2:
        st.write("")
        st.write("")
        if st.button("Generate Code", use_container_width=True, type="primary"):
            try:
                # The API expects days, let's round hours up to days
                days = max(1, hours // 24)
                data = api_client.generate_access_code(days)
                st.session_state.last_code = data["code"]
                st.rerun()
            except Exception:
                st.error("Failed to generate code")

    # Show last generated code
    if "last_code" in st.session_state:
        st.markdown(f"""
        <div class="access-code-display">
            <p style="font-size: 0.9rem; margin: 0; opacity: 0.85;">Your Access Code</p>
            <div class="code">{st.session_state.last_code}</div>
            <p style="font-size: 0.85rem; margin: 0; opacity: 0.75;">Share this code with your doctor</p>
        </div>
        """, unsafe_allow_html=True)

    # How to share instructions
    st.markdown(f"""
    <div class="info-box">
        <strong>{icon('info', size=16, color='#0E7490')} How to share</strong><br>
        Generate a code and share it with your doctor.
        They will enter this code in their portal to access your records.
        Codes expire automatically after the selected duration.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # Active codes list
    st.markdown(f'<p class="section-header">{icon_label("clipboard", "Your Access Codes", color="#94A3B8")}</p>', unsafe_allow_html=True)

    try:
        codes = api_client.get_access_codes()
    except Exception:
        codes = []

    if not codes:
        st.markdown('<div class="alert-info">No access codes generated yet. Create one above to share your records with a doctor.</div>', unsafe_allow_html=True)
        return

    for code_data in codes:
        is_revoked = code_data.get("is_revoked", False)
        expires_at = code_data.get("expires_at", "")

        try:
            exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            is_expired = exp_dt < datetime.now(exp_dt.tzinfo)
            remaining = exp_dt - datetime.now(exp_dt.tzinfo)
            if remaining.total_seconds() > 3600:
                exp_text = f"Expires in {remaining.days}d {remaining.seconds // 3600}h"
            elif remaining.total_seconds() > 0:
                exp_text = f"Expires in {remaining.seconds // 60} minutes"
            else:
                exp_text = "Expired"
        except Exception:
            is_expired = False
            exp_text = "Unknown"

        if is_revoked:
            status_badge = '<span class="badge-high">Revoked</span>'
        elif is_expired:
            status_badge = '<span class="badge-medium">Expired</span>'
        else:
            status_badge = '<span class="badge-low">Active</span>'

        doctor_text = f"Doctor #{code_data.get('doctor_id')}" if code_data.get("doctor_id") else "Not claimed"

        # Styled code card
        st.markdown(f"""
        <div class="code-card">
            <div class="code-text">{code_data['code']}</div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    {status_badge}
                    <span style="margin-left:12px; font-size:0.8rem; color:#64748B;">{exp_text} · {doctor_text}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_revoked and not is_expired:
            if st.button("Revoke Access", key=f"revoke_{code_data['id']}"):
                try:
                    api_client.revoke_access_code(code_data['id'])
                    st.success("Access revoked!")
                    st.rerun()
                except Exception:
                    st.error("Failed to revoke access")
