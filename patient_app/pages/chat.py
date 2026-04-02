"""Patient App — Health Chat Page"""

import streamlit as st
import requests


def show_chat_page(api_base, api_headers_fn):
    st.markdown("""
    <div class="main-header" style="background: linear-gradient(135deg, #5B21B6 0%, #7C3AED 60%, #8B5CF6 100%); box-shadow: 0 4px 16px rgba(124,58,237,0.15);">
        <h1>💬 Health Assistant</h1>
        <p>Ask questions about your medical records in plain language</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-info">
        💡 <strong>Tip:</strong> Ask things like "What medications am I taking?",
        "Summarize my last lab results", or "Do I have any allergies listed?"
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Suggested questions when empty
    if not st.session_state.chat_history:
        st.markdown('<p class="section-header">💡 Suggested Questions</p>', unsafe_allow_html=True)
        cols = st.columns(3)
        suggestions = [
            "What medications am I taking?",
            "Summarize my last lab results",
            "Do I have any risk factors?"
        ]
        for col, suggestion in zip(cols, suggestions):
            with col:
                if st.button(suggestion, key=f"suggest_{suggestion[:10]}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": suggestion})
                    st.rerun()

        # Empty state illustration
        st.markdown("""
        <div class="chat-empty-state">
            <div class="icon">🩺</div>
            <div class="title">Your health records are ready</div>
            <div class="subtitle">Ask me anything about your medical history</div>
        </div>
        """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if msg.get("sources"):
                sources_html = " ".join([f'<span class="badge-info">{s}</span>' for s in msg["sources"]])
                st.markdown(f"📎 {sources_html}", unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask about your health records..."):
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Searching your records..."):
                try:
                    r = requests.post(
                        f"{api_base}/api/chat/patient",
                        json={"message": prompt},
                        headers=api_headers_fn(),
                    )
                    if r.status_code == 200:
                        data = r.json()
                        st.markdown(data["answer"])
                        if data.get("sources"):
                            sources_html = " ".join([f'<span class="badge-info">{s}</span>' for s in data["sources"]])
                            st.markdown(f"📎 {sources_html}", unsafe_allow_html=True)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": data["answer"],
                            "sources": data.get("sources", []),
                        })
                    else:
                        error_msg = "Sorry, I couldn't process your question. Please try again."
                        st.error(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = "Connection error: Please ensure the backend server is running."
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.session_state.chat_history:
        st.divider()
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
