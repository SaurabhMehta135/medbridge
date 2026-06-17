"""Patient App — Document Upload & Management Page"""

import streamlit as st
from core.api_client import api_client
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.icons import icon, icon_label, doc_type_icon_circle


def show_upload_page(api_base, api_headers_fn):
    st.markdown(f"""
    <div class="main-header">
        <h1>{icon('file-text', size=28, color='#0891B2')} My Documents</h1>
        <p>Upload and manage your medical records</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload section
    st.markdown(f'<p class="section-header">{icon_label("upload", "Upload New Document", color="#94A3B8")}</p>', unsafe_allow_html=True)
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
            submit = st.form_submit_button("Upload", use_container_width=True, type="primary")
        with col2:
            process_after = st.form_submit_button("Upload & Process with AI", use_container_width=True)

        if (submit or process_after) and file:
            with st.spinner("Uploading your document..."):
                files = {"file": (file.name, file.getvalue(), file.type)}
                data = {"doc_type": doc_type}
                try:
                    doc = api_client.upload_document(files, data)
                    st.success(f"Uploaded: {file.name}")

                    if process_after:
                        with st.spinner("Analyzing your document with AI..."):
                            try:
                                api_client.process_document(doc['id'])
                                st.success("Document processed! Summary generated.")
                                try:
                                    r_summ = api_client.get_document_summary(doc['id'])
                                    if r_summ.get('patient_summary'):
                                        st.markdown("### Your Report Explained")
                                        st.markdown(f'<div class="alert-success">{r_summ["patient_summary"]}</div>', unsafe_allow_html=True)
                                except Exception:
                                    pass
                            except Exception:
                                st.warning("Processing will be available once AI models are loaded.")
                except Exception as e:
                    st.error("Upload failed")

    st.markdown("")

    # Document list
    st.markdown(f'<p class="section-header">{icon_label("folder", "Your Documents", color="#94A3B8")}</p>', unsafe_allow_html=True)
    try:
        docs = api_client.get_documents()
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
        doc_icon_html = doc_type_icon_circle(doc["doc_type"], size=42)

        status_badge = f'<span class="badge-low">{icon("circle-check", size=14, color="#16A34A")} AI Ready</span>' if doc["is_processed"] else f'<span class="badge-medium">{icon("clock", size=14, color="#EA580C")} Not processed</span>'
        size_kb = doc["file_size"] / 1024
        uploaded = doc.get("uploaded_at", "")
        if uploaded:
            uploaded = uploaded.split("T")[0]

        # Styled card header
        st.markdown(f"""
        <div class="doc-list-card">
            <div style="display:flex; align-items:center; gap:14px;">
                {doc_icon_html}
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
                    if st.button("Process", key=f"proc_{doc['id']}", use_container_width=True):
                        with st.spinner("Processing..."):
                            try:
                                api_client.process_document(doc['id'])
                                st.success("Processed!")
                                st.rerun()
                            except Exception:
                                st.warning("Processing requires AI models to be loaded.")
                else:
                    if st.button("Regenerate Summary", key=f"regen_{doc['id']}", use_container_width=True):
                        with st.spinner("Analyzing your report..."):
                            try:
                                api_client.regenerate_document_summary(doc['id'])
                                st.success("Summary Regenerated!")
                                st.rerun()
                            except Exception:
                                st.error("Failed to regenerate.")

                if st.button("Delete", key=f"del_{doc['id']}", use_container_width=True):
                    try:
                        api_client.delete_document(doc['id'])
                        st.success("Deleted!")
                        st.rerun()
                    except Exception:
                        st.error("Failed to delete")
