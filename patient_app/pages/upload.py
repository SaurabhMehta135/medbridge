"""Patient App — Document Upload & Management Page"""

import streamlit as st
import requests


def show_upload_page(api_base, api_headers_fn):
    st.markdown("""
    <div class="main-header">
        <h1>📄 My Documents</h1>
        <p>Upload and manage your medical records</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload section
    st.markdown('<p class="section-header">📤 Upload New Document</p>', unsafe_allow_html=True)
    with st.form("upload_form", clear_on_submit=True):
        file = st.file_uploader(
            "Choose a medical document",
            type=["pdf", "txt"],
            help="Supported: PDF, TXT files up to 10MB",
        )
        doc_type = st.selectbox("Document Type", [
            "general", "lab_report", "prescription", "discharge_summary",
            "imaging", "pathology", "consultation_note", "vaccination",
            "insurance", "other",
        ])
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("⬆️ Upload", use_container_width=True, type="primary")
        with col2:
            process_after = st.form_submit_button("🤖 Upload & Process with AI", use_container_width=True)

        if (submit or process_after) and file:
            with st.spinner("Uploading your document..."):
                files = {"file": (file.name, file.getvalue(), file.type)}
                data = {"doc_type": doc_type}
                r = requests.post(
                    f"{api_base}/api/patient/documents/upload",
                    files=files, data=data,
                    headers=api_headers_fn(),
                )
                if r.status_code == 201:
                    doc = r.json()
                    st.success(f"✅ Uploaded: {file.name}")

                    if process_after:
                        with st.spinner("🤖 Analyzing your document with AI..."):
                            r2 = requests.post(
                                f"{api_base}/api/patient/documents/{doc['id']}/process",
                                headers=api_headers_fn(),
                            )
                            if r2.status_code == 200:
                                st.success("🧠 Document processed! Summary generated.")
                                r_summ = requests.get(f"{api_base}/api/patient/documents/{doc['id']}/summary", headers=api_headers_fn())
                                if r_summ.status_code == 200 and r_summ.json().get('patient_summary'):
                                    st.markdown("### 📝 Your Report Explained")
                                    st.markdown(f'<div class="alert-success">{r_summ.json()["patient_summary"]}</div>', unsafe_allow_html=True)
                            else:
                                st.warning("Processing will be available once AI models are loaded.")
                else:
                    st.error(f"Upload failed: {r.json().get('detail', 'Unknown error')}")

    st.markdown("")

    # Document list
    st.markdown('<p class="section-header">📁 Your Documents</p>', unsafe_allow_html=True)
    try:
        r = requests.get(f"{api_base}/api/patient/documents", headers=api_headers_fn())
        docs = r.json() if r.status_code == 200 else []
    except Exception:
        docs = []

    if not docs:
        st.markdown("""
        <div class="alert-info">
            <strong>No documents yet.</strong> Upload your medical records above to get started with AI-powered analysis.
        </div>
        """, unsafe_allow_html=True)
        return

    for doc in docs:
        icon = {
            "lab_report": "🔬", "prescription": "💊", "discharge_summary": "🏥",
            "imaging": "📸", "pathology": "🧫", "consultation_note": "📝",
            "vaccination": "💉", "insurance": "📋",
        }.get(doc["doc_type"], "📄")

        icon_bg = {
            "lab_report": "#DBEAFE", "prescription": "#DCFCE7", "discharge_summary": "#FFF7ED",
            "imaging": "#F3E8FF", "pathology": "#FCE7F3", "consultation_note": "#DBEAFE",
            "vaccination": "#DCFCE7", "insurance": "#F1F5F9",
        }.get(doc["doc_type"], "#F1F5F9")

        status_badge = '<span class="badge-low">🧠 AI Ready</span>' if doc["is_processed"] else '<span class="badge-medium">⏳ Not processed</span>'
        size_kb = doc["file_size"] / 1024
        uploaded = doc.get("uploaded_at", "")
        if uploaded:
            uploaded = uploaded.split("T")[0]

        # Styled card header
        st.markdown(f"""
        <div class="doc-list-card">
            <div style="display:flex; align-items:center; gap:14px;">
                <div class="doc-icon-circle" style="background:{icon_bg};">{icon}</div>
                <div style="flex:1; min-width:0;">
                    <div style="font-weight:700; color:#0F172A; font-size:0.9rem;">{doc['original_filename']}</div>
                    <div style="font-size:0.8rem; color:#64748B;">{doc['doc_type'].replace('_', ' ').title()} · {size_kb:.1f} KB</div>
                    <div style="font-size:0.75rem; color:#94A3B8; margin-top:2px;">{uploaded}</div>
                </div>
                <div>{status_badge}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Details — {doc['original_filename']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                if doc["is_processed"] and doc.get("patient_summary"):
                    st.markdown(f'<div class="alert-success" style="margin-top:8px;">{doc["patient_summary"]}</div>', unsafe_allow_html=True)
                elif not doc["is_processed"]:
                    st.caption("This document has not been processed by AI yet.")

            with col2:
                if not doc["is_processed"]:
                    if st.button("🤖 Process", key=f"proc_{doc['id']}", use_container_width=True):
                        with st.spinner("Processing..."):
                            r = requests.post(
                                f"{api_base}/api/patient/documents/{doc['id']}/process",
                                headers=api_headers_fn(),
                            )
                            if r.status_code == 200:
                                st.success("Processed!")
                                st.rerun()
                            else:
                                st.warning("Processing requires AI models to be loaded.")
                else:
                    if st.button("🔄 Regenerate Summary", key=f"regen_{doc['id']}", use_container_width=True):
                        with st.spinner("Analyzing your report..."):
                            r_regen = requests.post(
                                f"{api_base}/api/patient/documents/{doc['id']}/regenerate-summary",
                                headers=api_headers_fn()
                            )
                            if r_regen.status_code == 200:
                                st.success("Summary Regenerated!")
                                st.rerun()
                            else:
                                st.error("Failed to regenerate.")

                if st.button("🗑️ Delete", key=f"del_{doc['id']}", use_container_width=True):
                    r = requests.delete(
                        f"{api_base}/api/patient/documents/{doc['id']}",
                        headers=api_headers_fn(),
                    )
                    if r.status_code == 204:
                        st.success("Deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete")
