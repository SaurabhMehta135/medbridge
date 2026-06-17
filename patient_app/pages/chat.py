"""Patient App — Health Chat Page"""

import streamlit as st
from core.api_client import api_client
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from shared.icons import icon, icon_label


def show_chat_page(api_base, api_headers_fn):
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon('message-circle', size=28, color='#0891B2')} Health Assistant</h1>
        <p>Ask questions about your medical records in plain language</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="alert-info">
        {icon('lightbulb', size=16, color='#0891B2')} <strong>Tip:</strong> Ask things like "What medications am I taking?",
        "Summarize my last lab results", or "Do I have any allergies listed?"
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Suggested questions when empty
    if not st.session_state.chat_history:
        st.markdown(f'<p class="section-header">{icon_label("lightbulb", "Suggested Questions", color="#94A3B8")}</p>', unsafe_allow_html=True)
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
        st.markdown(f"""
        <div class="chat-empty-state">
            <div class="icon">{icon('stethoscope', size=36, color='#94A3B8')}</div>
            <div class="title">Your health records are ready</div>
            <div class="subtitle">Ask me anything about your medical history</div>
        </div>
        """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                sources_html = " ".join([f'<span class="badge-info">{s}</span>' for s in msg["sources"]])
                st.markdown(f"{icon('paperclip', size=14, color='#0891B2')} {sources_html}", unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask about your health records..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your records..."):
                try:
                    data = api_client.send_chat_message(prompt)
                    answer = data.get("answer", data.get("reply", "No response received."))
                    st.markdown(answer)
                    if data.get("sources"):
                        sources_html = " ".join([f'<span class="badge-info">{s}</span>' for s in data["sources"]])
                        st.markdown(f"{icon('paperclip', size=14, color='#0891B2')} {sources_html}", unsafe_allow_html=True)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": data.get("sources", []),
                    })
                except Exception:
                    error_msg = "Failed to connect to AI service."
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.session_state.chat_history:
        st.divider()
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
