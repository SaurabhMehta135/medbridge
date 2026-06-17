import streamlit as st
from datetime import datetime
from core.api_client import api_client
from components.auth import logout
from core.config import config
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.icons import icon, icon_label, doc_type_icon_circle, status_icon

def show_dashboard():
    user = st.session_state.user
    if not user:
        logout()
        st.rerun()

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
        "Dashboard",
        "My Documents",
        "Health Assistant",
        "Follow-ups",
        "Share Records",
        "Emergency Card",
    ]

    if st.session_state.patient_page not in nav_items:
        st.session_state.patient_page = "Dashboard"

    # ── Sidebar Navigation ──
    with st.sidebar:
        st.markdown(f"""
        <div class="patient-rail-profile">
            <div class="patient-rail-name">{icon('user', size=16, color='#0891B2')} {user['full_name']}</div>
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
        if st.button("Sign Out", key="patient_signout_left", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Main Content ──
    page = st.session_state.patient_page

    def dummy_header():
        return api_client._get_headers()

    if page == "Dashboard":
        _patient_dashboard(user)
    elif page == "Follow-ups":
        from pages.followups import show_followup_page
        show_followup_page(config.API_BASE, dummy_header)
    elif page == "My Documents":
        from pages.upload import show_upload_page
        show_upload_page(config.API_BASE, dummy_header)
    elif page == "Health Assistant":
        from pages.chat import show_chat_page
        show_chat_page(config.API_BASE, dummy_header)
    elif page == "Share Records":
        from pages.share import show_share_page
        show_share_page(config.API_BASE, dummy_header)
    elif page == "Emergency Card":
        from pages.emergency_card import show_emergency_card
        show_emergency_card()

def _patient_dashboard(user):
    # Greeting
    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    st.markdown(f"""
    <div class="page-header">
        <h1 style="color:#0F172A; font-weight:800; margin:0;">{greeting}, {user["full_name"].split()[0]}!</h1>
        <p style="color:#64748B; margin:4px 0 0 0;">Here's your health overview for today</p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch data
    try:
        docs = api_client.get_documents()
        alerts = api_client.get_alerts(user['id'])
        risk_data = api_client.get_patient_risk_score()
    except Exception:
        docs, alerts, risk_data = [], [], {}

    # Metric Cards
    try:
        fups = api_client.get_patient_followups()
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
            <div class="metric-icon">{icon('file-text', size=22, color='#2563EB')}</div><div class="metric-value">{len(docs)}</div>
            <div class="metric-label">Documents</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #7C3AED;"></div>
            <div class="metric-icon">{icon('pill', size=22, color='#7C3AED')}</div><div class="metric-value">{med_count}</div>
            <div class="metric-label">Medications</div></div>""", unsafe_allow_html=True)
    with col3:
        fup_badge = f' <span class="badge-high">{overdue_num} overdue</span>' if overdue_num > 0 else ""
        pending_fups = sum(1 for f in fups if f["status"] in ("pending", "overdue"))
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #EA580C;"></div>
            <div class="metric-icon">{icon('calendar', size=22, color='#EA580C')}</div><div class="metric-value">{pending_fups}</div>
            <div class="metric-label">Follow-ups{fup_badge}</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-stripe" style="background: #DC2626;"></div>
            <div class="metric-icon">{icon('triangle-alert', size=22, color='#DC2626')}</div><div class="metric-value">{allergy_count}</div>
            <div class="metric-label">Allergies</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    # Health Risk Assessment
    if risk_data:
        st.markdown(f'<p class="section-header">{icon_label("shield", "Health Risk Assessment", size=16, color="#0891B2")}</p>', unsafe_allow_html=True)
        has_data = any(risk_data.get(d, {}).get("status") == "CALCULATED" for d in ["cardiovascular", "diabetes", "kidney"])
        if not has_data:
            st.markdown(f'<div class="alert-info">{icon("bar-chart-3", size=16, color="#0891B2")} Upload your lab reports to see your personalized health risk assessment.</div>', unsafe_allow_html=True)
        else:
            # Build all 3 risk cards as equal-width HTML grid
            dims = [
                ("Cardiovascular", "cardiovascular", "heart-pulse", "#DC2626"),
                ("Diabetes", "diabetes", "droplets", "#EA580C"),
                ("Kidney Function", "kidney", "activity", "#16A34A"),
            ]
            cards_html = '<div class="risk-grid">'
            for title, key, dim_icon, dim_color in dims:
                data = risk_data.get(key, {})
                if data.get("status") == "INSUFFICIENT_DATA" or data.get("status") != "CALCULATED":
                    cards_html += f'''
                    <div class="risk-card-equal" style="border-left: 4px solid #E2E8F0;">
                        <div class="risk-card-empty">
                            <div class="empty-icon">{icon(dim_icon, size=28, color="#CBD5E1")}</div>
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
                            <strong style="color:#0F172A;">{icon(dim_icon, size=18, color=color)} {title}</strong>
                            <span class="{badge_cls}">{lvl}</span>
                        </div>
                        <h2 style="margin:12px 0 8px 0; color:{color}; font-size:2rem;">{score}%</h2>
                        <div class="risk-bar-bg"><div class="risk-bar-fill" style="width:{score}%; background:{color};"></div></div>
                    </div>'''
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)

            # Expander details below the grid for cards that have data
            detail_cols = st.columns(3)
            for col, (title, key, dim_icon, dim_color) in zip(detail_cols, dims):
                with col:
                    data = risk_data.get(key, {})
                    if data.get("status") != "CALCULATED":
                        continue
                    with st.expander(f"What this means"):
                        for rf in data["risk_factors"]:
                            st.markdown(f"{icon('triangle-alert', size=14, color='#EA580C')} **{rf['factor']}**: {rf['value']}", unsafe_allow_html=True)
                        for pf in data["protective_factors"]:
                            st.markdown(f"{icon('circle-check', size=14, color='#16A34A')} **{pf['factor']}**: {pf['value']}", unsafe_allow_html=True)
                        if data["discuss"]:
                            st.markdown("**Discuss with your doctor:**")
                            for i, d_item in enumerate(data["discuss"], 1):
                                st.markdown(f"{i}. {d_item}")

            st.caption(f"{icon('triangle-alert', size=12, color='#EA580C')} *This is an automated assessment. Always consult a healthcare professional.*", unsafe_allow_html=True)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # Two-column: Summaries + Follow-ups
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f'<p class="section-header">{icon_label("notebook-pen", "Recent Report Summaries", size=16, color="#0891B2")}</p>', unsafe_allow_html=True)
        summarized_docs = [d for d in docs if d.get("patient_summary")]
        if summarized_docs:
            for doc in summarized_docs[:3]:
                doc_icon_html = doc_type_icon_circle(doc.get("doc_type", ""), size=40)
                preview = (doc["patient_summary"][:120] + "...") if len(doc["patient_summary"]) > 120 else doc["patient_summary"]
                uploaded = doc.get("uploaded_at", "")
                if uploaded:
                    uploaded = uploaded.split("T")[0]
                st.markdown(f'''
                <div class="summary-card">
                    <div style="display:flex; align-items:flex-start; gap:12px;">
                        {doc_icon_html}
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
                    if st.button("Regenerate", key=f"dash_regen_{doc['id']}"):
                        with st.spinner("Analyzing your report..."):
                            try:
                                api_client.regenerate_document_summary(doc['id'])
                                st.success("Summary Regenerated!")
                                st.rerun()
                            except Exception:
                                st.error("Failed to regenerate summary")
        else:
            st.markdown('<div class="alert-info">No summaries yet. Upload a document to get started.</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown(f'<p class="section-header">{icon_label("calendar", "Follow-up Tracker", size=16, color="#0891B2")}</p>', unsafe_allow_html=True)
        upcoming_num = sum(1 for f in fups if f["status"] == "pending" and f.get("due_date") and 0 <= (datetime.strptime(f["due_date"], "%Y-%m-%d").date() - today).days <= 28)
        comp_num = sum(1 for f in fups if f["status"] == "completed")

        if overdue_num > 0:
            st.markdown(f'<div class="alert-danger"><strong>{status_icon("overdue", size=14)} {overdue_num} Overdue</strong> — Please schedule these items.</div>', unsafe_allow_html=True)
        if upcoming_num > 0:
            st.markdown(f'<div class="alert-warning"><strong>{status_icon("upcoming", size=14)} {upcoming_num} Upcoming</strong> — Due within 4 weeks.</div>', unsafe_allow_html=True)
        if comp_num > 0:
            st.markdown(f'<div class="alert-success"><strong>{status_icon("completed", size=14)} {comp_num} Completed</strong></div>', unsafe_allow_html=True)
        if not fups:
            st.markdown(f'''
            <div class="followup-empty">
                <div class="check-icon">{icon('circle-check', size=36, color='#16A34A')}</div>
                <div class="title">You're all caught up!</div>
                <div class="subtitle">No pending follow-ups</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # Alerts
    if alerts:
        st.markdown(f'<p class="section-header">{icon_label("triangle-alert", "Health Alerts", size=16, color="#EA580C")}</p>', unsafe_allow_html=True)
        for alert in alerts:
            severity = alert["severity"]
            cls = "alert-danger" if severity == "critical" else "alert-warning" if severity == "warning" else "alert-info"
            alert_label = "Critical" if severity == "critical" else "Warning" if severity == "warning" else "Info"
            with st.expander(f"{alert_label}: {alert['title']}", expanded=(severity == "critical")):
                st.write(alert["description"])
                if alert.get("related_drugs"):
                    st.caption(f"Related: {', '.join(alert['related_drugs'])}")

    # Profile
    st.markdown(f'<p class="section-header">{icon_label("clipboard", "Profile Summary", size=16, color="#0891B2")}</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Blood Type:** {user.get('blood_type') or 'Not set'}")
        st.markdown(f"**Allergies:** {user.get('allergies') or 'None recorded'}")
    with col2:
        st.markdown(f"**Medications:** {user.get('medications') or 'None recorded'}")
        st.markdown(f"**Emergency Contact:** {user.get('emergency_contact_name') or 'Not set'}")

def _show_doctor_view(user):
    st.markdown("""
    <div class="page-header-teal">
        <h1>Incorrect Portal</h1>
    </div>
    """, unsafe_allow_html=True)
    st.error(f"Hello Doctor! You are currently logged into the Patient Portal. Please visit **{config.DOCTOR_PORTAL_URL}** to access the advanced Doctor Analytics Dashboard.")
    if st.button("Sign Out", type="primary", use_container_width=True):
        logout()
        st.rerun()
