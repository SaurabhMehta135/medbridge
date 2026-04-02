"""Doctor App — Clinical Chat Page"""

import streamlit as st
import requests


def show_clinical_chat(api_base, api_headers_fn):
    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #0891B2, #0E7490);">
        <h1>💬 Clinical Chat</h1>
        <p>AI-powered analysis scoped to a specific patient's records</p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch patients
    try:
        r = requests.get(f"{api_base}/api/doctor/patients", headers=api_headers_fn())
        patients = r.json() if r.status_code == 200 else []
    except Exception:
        patients = []

    if not patients:
        st.markdown("""
        <div class="info-box">
            You need to have at least one patient connected.
            Enter an access code first to link with a patient.
        </div>
        """, unsafe_allow_html=True)
        return

    # Patient selector
    patient_options = {f"{p['full_name']} (ID: {p['id']})": p for p in patients}
    selected = st.selectbox("Select Patient", list(patient_options.keys()))
    patient = patient_options[selected]

    # Patient summary bar
    initials = "".join(w[0] for w in patient["full_name"].split()[:2]).upper()
    st.markdown(f"""
    <div class="medbridge-card" style="border-left: 4px solid #0891B2; display:flex; align-items:center; gap:16px;">
        <div style="width:42px;height:42px;border-radius:50%;background:#0891B2;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;flex-shrink:0;">{initials}</div>
        <div>
            <strong style="color:#0F172A;">{patient['full_name']}</strong> &nbsp;|&nbsp;
            🩸 {patient.get('blood_type', 'N/A')} &nbsp;|&nbsp;
            ⚠️ Allergies: {patient.get('allergies', 'None')} &nbsp;|&nbsp;
            💊 Meds: {patient.get('medications', 'None')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-warning" style="font-size:0.85rem;">
        ⚕️ <strong>Clinical mode:</strong> Responses use precise clinical terminology
        with references to specific documents. <em>For professional use only.</em>
    </div>
    """, unsafe_allow_html=True)

    # Chat history (per patient)
    chat_key = f"dr_chat_{patient['id']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Display chat
    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"], avatar="🩺" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if msg.get("sources"):
                sources_html = " ".join([f'<span class="badge-info">{s}</span>' for s in msg["sources"]])
                st.markdown(f"📎 {sources_html}", unsafe_allow_html=True)

    # Quick action buttons (teal pills)
    if not st.session_state[chat_key]:
        st.markdown('<p class="section-header">Quick Actions</p>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Summarize records", use_container_width=True):
                _send_message(api_base, api_headers_fn, patient["id"], chat_key,
                             "Please provide a comprehensive clinical summary of this patient's medical records.")
        with col2:
            if st.button("🔬 Recent labs", use_container_width=True):
                _send_message(api_base, api_headers_fn, patient["id"], chat_key,
                             "What are the most recent lab results? Highlight any abnormal values.")
        with col3:
            if st.button("⚠️ Risk factors", use_container_width=True):
                _send_message(api_base, api_headers_fn, patient["id"], chat_key,
                             "What are the key risk factors and concerns for this patient based on their records?")

        # Empty state illustration
        st.markdown("""
        <div class="chat-empty-state">
            <div class="icon">🩺</div>
            <div class="title">Clinical AI Assistant</div>
            <div class="subtitle">Select a patient and ask clinical questions</div>
        </div>
        """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask about this patient's records..."):
        _send_message(api_base, api_headers_fn, patient["id"], chat_key, prompt)


def _send_message(api_base, api_headers_fn, patient_id, chat_key, message):
    """Send a message and display the response."""
    with st.chat_message("user", avatar="🩺"):
        st.markdown(message)
    st.session_state[chat_key].append({"role": "user", "content": message})

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Analyzing patient records..."):
            try:
                r = requests.post(
                    f"{api_base}/api/chat/doctor",
                    json={"message": message, "patient_id": patient_id},
                    headers=api_headers_fn(),
                )
                if r.status_code == 200:
                    data = r.json()
                    st.markdown(data["answer"])
                    if data.get("sources"):
                        sources_html = " ".join([f'<span class="badge-info">{s}</span>' for s in data["sources"]])
                        st.markdown(f"📎 {sources_html}", unsafe_allow_html=True)
                    st.session_state[chat_key].append({
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data.get("sources", []),
                    })
                else:
                    st.error("Failed to get a response")
            except Exception as e:
                st.error(f"Connection error: {e}")

    st.rerun()
