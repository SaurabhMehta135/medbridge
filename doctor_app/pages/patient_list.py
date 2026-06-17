"""Doctor App — Patient List Page"""

import streamlit as st
import requests

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.icons import icon, icon_label, doc_type_icon, doc_type_icon_circle, status_icon

from core.api_client import api_client

def show_patient_list(api_base, api_headers_fn):
    st.markdown("""
    <div class="main-header">
        <h1>My Patients</h1>
        <p>Patients who have shared their records with you</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        patients = api_client.get_patients()
    except Exception:
        patients = []
        st.error("Failed to connect to the server")

    if not patients:
        st.markdown("""
        <div class="info-box">
            <strong>No patients yet.</strong> Ask your patient for an access code,
            then enter it in the "Enter Access Code" section.
        </div>
        """, unsafe_allow_html=True)
        return

    search_query = st.text_input("Search patients", "", placeholder="Search by name or email...", label_visibility="collapsed")

    if search_query:
        patients = [
            p for p in patients
            if search_query.lower() in p.get("full_name", "").lower() or
               search_query.lower() in p.get("email", "").lower()
        ]
        if not patients:
            st.markdown('<div class="alert-info">No patients found matching your search.</div>', unsafe_allow_html=True)
            return

    for patient in patients:
        initials = "".join(w[0] for w in patient["full_name"].split()[:2]).upper()
        blood = patient.get('blood_type', 'N/A')
        allergies = patient.get('allergies', 'None')

        # Styled patient card header
        st.markdown(f"""
        <div class="patient-card-light" style="border-left: 4px solid #0891B2;">
            <div style="display:flex; align-items:center; gap:14px;">
                <div style="width:46px;height:46px;border-radius:50%;background:#0891B2;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:1rem;flex-shrink:0;">{initials}</div>
                <div style="flex:1; min-width:0;">
                    <div style="font-weight:700; color:#0F172A; font-size:1rem;">{patient['full_name']}</div>
                    <div style="margin-top:4px;">
                        <span class="badge-info" style="font-size:11px;">{blood}</span>
                        <span class="badge-medium" style="font-size:11px; margin-left:4px;">{allergies}</span>
                    </div>
                    <div style="font-size:0.75rem; color:#94A3B8; margin-top:4px;">{patient.get('email', '')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Details — {patient['full_name']}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Date of Birth:** {patient.get('date_of_birth', 'N/A')}")
                st.markdown(f"**Blood Type:** {patient.get('blood_type', 'N/A')}")
                st.markdown(f"**Allergies:** {patient.get('allergies', 'None recorded')}")
                st.markdown(f"**Current Medications:** {patient.get('medications', 'None recorded')}")
                st.markdown(f"**Emergency Contact:** {patient.get('emergency_contact_name', 'N/A')} — {patient.get('emergency_contact_phone', 'N/A')}")

            with col2:
                if st.button("View Documents", key=f"docs_{patient['id']}", use_container_width=True):
                    st.session_state.selected_patient = patient
                    st.rerun()

                if st.button("View Alerts", key=f"alerts_{patient['id']}", use_container_width=True):
                    try:
                        alerts = api_client.get_alerts(patient['id'])
                    except Exception:
                        alerts = []

                    if alerts:
                        for alert in alerts:
                            sev = alert["severity"]
                            cls = "alert-danger" if sev == "critical" else "alert-warning" if sev == "warning" else "alert-info"
                            sev_icon = status_icon(sev)
                            st.markdown(f'<div class="{cls}">{sev_icon} <strong>{alert["title"]}</strong><br><span style="font-size:0.85rem;">{alert["description"]}</span></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="alert-success">{status_icon("success")} No alerts for this patient</div>', unsafe_allow_html=True)

            # Show documents if this patient is selected
            selected = st.session_state.get("selected_patient") or {}
            if selected.get("id") == patient["id"]:
                st.divider()

                tab_summary, tab_fups, tab_docs, tab_export = st.tabs(["Summary & Risks", "Follow-ups", "Patient Documents", "Export"])

                with tab_summary:
                    st.markdown(f'<p class="section-header">{icon_label("shield", "Clinical Risk Assessment", color="#94A3B8")}</p>', unsafe_allow_html=True)
                    try:
                        risk_data = api_client.get_patient_risk_score(patient['id'])
                    except Exception:
                        risk_data = {}

                    if not risk_data:
                        st.markdown('<div class="alert-info">Risk assessment not available.</div>', unsafe_allow_html=True)
                    else:
                        has_data = any(risk_data.get(d, {}).get("status") == "CALCULATED" for d in ["cardiovascular", "diabetes", "kidney"])
                        if not has_data:
                            st.markdown('<div class="alert-info">Insufficient patient data to generate clinical risk assessment.</div>', unsafe_allow_html=True)
                        else:
                            st.caption(f"Calculated: {risk_data.get('last_updated')}")

                            dim_cols = st.columns(3)
                            dims = [("Cardiovascular", "cardiovascular", "heart-pulse"), ("Diabetes", "diabetes", "droplets"), ("Kidney Function", "kidney", "activity")]

                            for col, (title, key, icon_name) in zip(dim_cols, dims):
                                with col:
                                    data = risk_data[key]
                                    if data["status"] == "INSUFFICIENT_DATA":
                                        st.markdown(f"**{title}**")
                                        st.caption("Not enough data")
                                        continue

                                    score = data["score"]
                                    lvl = data["level"]
                                    color = "#DC2626" if lvl == "HIGH" else "#EA580C" if lvl == "MEDIUM" else "#16A34A"
                                    badge_cls = "badge-high" if lvl == "HIGH" else "badge-medium" if lvl == "MEDIUM" else "badge-low"

                                    st.markdown(f"""
                                    <div class="medbridge-card" style="border-left: 4px solid {color};">
                                        <div style="display:flex; justify-content:space-between; align-items:center;">
                                            <strong style="color:#0F172A;">{icon(icon_name, size=18, color=color)} {title}</strong>
                                            <span class="{badge_cls}">{lvl}</span>
                                        </div>
                                        <h2 style="margin:12px 0 8px 0; color:{color}; font-size:2rem;">{score}%</h2>
                                        <div class="risk-bar-bg"><div class="risk-bar-fill" style="width:{score}%; background:{color};"></div></div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    if data['risk_factors'] or data['protective_factors']:
                                        with st.expander(f"Clinical Evidence ({len(data['risk_factors']) + len(data['protective_factors'])} factors)", expanded=True):
                                            table_html = """
                                            <table style="width:100%; font-size:0.8rem; border-collapse:collapse; margin-top:0.5rem;">
                                            <tr style="border-bottom:2px solid #E2E8F0;"><th style="padding:6px; text-align:left; color:#64748B; font-weight:600;">Metric</th><th style="padding:6px; text-align:left; color:#64748B;">Value</th><th style="padding:6px; text-align:left; color:#64748B;">Source</th></tr>
                                            """
                                            for rf in data["risk_factors"]:
                                                table_html += f'<tr style="border-bottom:1px solid #F1F5F9;"><td style="padding:6px;">{icon("triangle-alert", size=14, color="#DC2626")} {rf["factor"]}</td><td style="padding:6px;"><strong>{rf["value"]}</strong></td><td style="padding:6px; color:#94A3B8;">{rf["source"]}</td></tr>'
                                            for pf in data["protective_factors"]:
                                                table_html += f'<tr style="border-bottom:1px solid #F1F5F9;"><td style="padding:6px;">{icon("circle-check", size=14, color="#16A34A")} {pf["factor"]}</td><td style="padding:6px;"><strong>{pf["value"]}</strong></td><td style="padding:6px; color:#94A3B8;">{pf["source"]}</td></tr>'
                                            table_html += "</table>"
                                            st.markdown(table_html, unsafe_allow_html=True)

                with tab_docs:
                    st.markdown(f'<p class="section-header">{icon_label("folder", "Uploaded Documents", color="#94A3B8")}</p>', unsafe_allow_html=True)
                    try:
                        docs = api_client.get_patient_documents(patient['id'])
                    except Exception:
                        docs = []

                    if docs:
                        for doc in docs:
                            doc_icon_html = doc_type_icon(doc["doc_type"])
                            status_badge = f'<span class="badge-low">{icon("circle-check", size=12, color="#16A34A")} AI Ready</span>' if doc["is_processed"] else f'<span class="badge-medium">{icon("clock", size=12, color="#EA580C")} Pending</span>'

                            with st.expander(f"{doc['original_filename']} ({doc['doc_type'].replace('_', ' ').title()})"):
                                st.markdown(status_badge, unsafe_allow_html=True)
                                st.caption(f"Size: {doc['file_size'] / 1024:.1f} KB")

                                if doc.get('patient_summary') or doc.get('clinical_summary'):
                                    use_clinical = st.toggle("Switch to Clinical View", key=f"clin_toggle_{doc['id']}")

                                    if use_clinical and doc.get('clinical_summary'):
                                        st.markdown(f'<div class="alert-info">{icon("stethoscope", size=14, color="#0891B2")} <strong>Clinical Analysis:</strong><br>{doc["clinical_summary"]}</div>', unsafe_allow_html=True)
                                    elif doc.get('patient_summary'):
                                        st.markdown(f'<div class="alert-success">{icon("user", size=14, color="#065F46")} <strong>Patient Overview:</strong><br>{doc["patient_summary"]}</div>', unsafe_allow_html=True)
                                    else:
                                        st.markdown('<div class="alert-warning">Analysis pending or incomplete.</div>', unsafe_allow_html=True)

                                    st.caption("*AI-generated summary. Always verify against raw clinical documents.*")
                                elif doc["is_processed"]:
                                    st.markdown('<div class="alert-info">Select to parse text manually or trigger AI regeneration via Patient App.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="alert-info">No documents uploaded by this patient yet.</div>', unsafe_allow_html=True)

                with tab_fups:
                    st.markdown(f'<p class="section-header">{icon_label("calendar", "Patient Follow-ups", color="#94A3B8")}</p>', unsafe_allow_html=True)
                    try:
                        fups = api_client.get_patient_followups(patient['id'])
                    except Exception:
                        fups = []

                    if fups:
                        for f in fups:
                            with st.expander(f"{f['description']} (Due: {f['due_date'] or 'No Date'})"):
                                st.write(f"**Type:** {f['follow_up_type'].replace('_', ' ').title()}")
                                st.write(f"**Status:** {f['status'].title()}")
                                st.write(f"**Urgency:** {f['urgency'].title()}")
                                if f["notes"]:
                                    st.write(f"**Patient Notes:** {f['notes']}")
                                st.caption(f"Source: Document #{f['document_id']}" if f['document_id'] else "Source: Manual Clinical Entry")
                    else:
                        st.markdown('<div class="alert-info">No follow-ups recorded for this patient.</div>', unsafe_allow_html=True)

                    st.divider()
                    st.markdown(f'<p class="section-header">{icon_label("plus-circle", "Add Manual Follow-up", color="#94A3B8")}</p>', unsafe_allow_html=True)
                    with st.form(key=f"manual_fup_{patient['id']}"):
                        f_type = st.selectbox("Type", ["appointment", "lab_test", "referral", "imaging", "medication_review", "lifestyle", "other"])
                        f_desc = st.text_input("Description", placeholder="e.g. Return for HbA1c review")
                        f_date = st.date_input("Due Date")
                        f_urg = st.selectbox("Urgency", ["routine", "soon", "urgent"])
                        f_spec = st.text_input("Specialty (Optional)")

                        if st.form_submit_button("Save Follow-up"):
                            if not f_desc:
                                st.error("Description is required.")
                            else:
                                try:
                                    api_client.create_followup(
                                        patient_id=patient['id'],
                                        notes=f_desc,
                                        due_date=f_date.isoformat()
                                    )
                                    st.success("Follow-up saved!")
                                    st.rerun()
                                except Exception:
                                    st.error("Failed to save.")

                with tab_export:
                    import datetime
                    st.markdown("""
                    <div class="patient-card-light" style="padding: 24px;">
                        <h3 style="margin-bottom:8px; color:#0F172A;">FHIR R4 Export</h3>
                        <p style="color:#475569; margin-bottom:16px;">
                            Export this patient's complete health record as a FHIR R4 compliant JSON bundle.
                        </p>
                        <p style="color:#0F172A; font-weight:600; font-size:0.9rem; margin-bottom:4px;">This format is compatible with:</p>
                        <ul style="color:#475569; font-size:0.9rem; margin-bottom:16px; list-style:none; padding-left:0;">
                            <li>Epic EHR systems</li>
                            <li>Cerner EHR systems</li>
                            <li>India ABDM platform</li>
                            <li>Any FHIR R4 compliant system</li>
                        </ul>
                        <p style="color:#0F172A; font-weight:600; font-size:0.9rem; margin-bottom:4px;">Includes:</p>
                        <ul style="color:#475569; font-size:0.9rem; margin-bottom:24px; list-style:none; padding-left:0;">
                            <li>• Patient demographics</li>
                            <li>• Conditions and diagnoses</li>
                            <li>• Medications and prescriptions</li>
                            <li>• Allergies and intolerances</li>
                            <li>• Lab observations</li>
                            <li>• Encounter history</li>
                        </ul>
                    """, unsafe_allow_html=True)
                    try:
                        r_fhir = api_client.get_patient_fhir_export(patient['id'])
                        file_name = f"medbridge_fhir_{patient['full_name'].replace(' ', '_').lower()}_{datetime.datetime.utcnow().strftime('%Y%m%d')}.json"
                        st.download_button("Download FHIR Bundle", data=r_fhir.content, file_name=file_name, mime="application/fhir+json", type="primary")
                    except Exception:
                        st.error("Failed to generate FHIR Export.")
                        
                    st.markdown(f"""
                        <div style="margin-top:16px; font-size:0.8rem; color:#64748B;">
                            File format: JSON<br>
                            Standard: HL7 FHIR R4<br>
                            Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style="margin-top: 16px; font-size: 0.8rem; color: #64748B; background: #F8FAFC; padding: 12px; border-radius: 8px;">
                        <strong>Research and Development Notice</strong><br>
                        This FHIR export is generated for educational and portfolio demonstration purposes. In a production healthcare environment, FHIR exports must comply with local data protection regulations including HIPAA in the US and DISHA in India, and should only be transmitted over secure authenticated channels. This implementation follows HL7 FHIR R4 resource structure as documented at hl7.org/fhir.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("About This Feature"):
                        st.markdown("""
                        MedBridge implements **HL7 FHIR R4** — the international standard for health data interoperability. This aligns with India's Ayushman Bharat Digital Mission (ABDM) which uses FHIR as its data exchange standard, and the US 21st Century Cures Act which mandates FHIR API support for all certified EHR systems.
                        """)
