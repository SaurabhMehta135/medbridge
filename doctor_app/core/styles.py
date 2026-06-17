import streamlit as st
import os

def load_css():
    css_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'style.css')
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {css_file}")
