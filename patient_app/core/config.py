import os
import streamlit as st

def get_config_value(name: str, default: str = "") -> str:
    """Retrieve configuration from env variables or Streamlit secrets."""
    if os.getenv(name):
        return os.getenv(name)
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

class Config:
    API_BASE = get_config_value("BACKEND_URL", "http://127.0.0.1:8000")
    PATIENT_PORTAL_URL = get_config_value("PATIENT_PORTAL_URL", "http://localhost:8501")
    DOCTOR_PORTAL_URL = get_config_value("DOCTOR_PORTAL_URL", "http://localhost:8502")

config = Config()
