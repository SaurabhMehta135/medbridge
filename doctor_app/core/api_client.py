import requests
import streamlit as st
from .config import config

class APIClient:
    def __init__(self):
        self.base_url = config.API_BASE
        
    def _get_headers(self):
        token = st.session_state.get("dr_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
        
    def login(self, email: str, password: str) -> dict:
        r = requests.post(f"{self.base_url}/api/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        return r.json()
        
    def get_me(self) -> dict:
        r = requests.get(f"{self.base_url}/api/auth/me", headers=self._get_headers())
        r.raise_for_status()
        return r.json()
        
    def register(self, data: dict) -> dict:
        r = requests.post(f"{self.base_url}/api/auth/register", json=data)
        r.raise_for_status()
        return r.json()
        
    def get_fhir_export_all(self):
        r = requests.get(f"{self.base_url}/api/doctor/fhir-export-all", headers=self._get_headers())
        r.raise_for_status()
        return r
        
    def get_analytics(self) -> dict:
        r = requests.get(f"{self.base_url}/api/doctor/analytics", headers=self._get_headers())
        r.raise_for_status()
        return r.json()
        
    def verify_access_code(self, code: str) -> dict:
        r = requests.post(
            f"{self.base_url}/api/doctor/verify-code",
            json={"code": code},
            headers=self._get_headers(),
        )
        r.raise_for_status()
        return r.json()

    def get_patients(self) -> list:
        r = requests.get(f"{self.base_url}/api/doctor/patients", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def send_chat_message(self, patient_id: int, message: str) -> dict:
        r = requests.post(
            f"{self.base_url}/api/doctor/chat",
            json={"patient_id": patient_id, "message": message},
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def get_alerts(self, patient_id: int) -> list:
        r = requests.get(f"{self.base_url}/api/alerts/{patient_id}", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def get_patient_risk_score(self, patient_id: int) -> dict:
        r = requests.get(f"{self.base_url}/api/doctor/patients/{patient_id}/risk-score", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def get_patient_documents(self, patient_id: int) -> list:
        r = requests.get(f"{self.base_url}/api/doctor/patients/{patient_id}/docs", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def get_patient_followups(self, patient_id: int) -> list:
        r = requests.get(f"{self.base_url}/api/doctor/patients/{patient_id}/followups", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def create_followup(self, patient_id: int, notes: str, due_date: str) -> dict:
        r = requests.post(
            f"{self.base_url}/api/doctor/patients/{patient_id}/followups",
            json={"notes": notes, "due_date": due_date},
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def get_patient_fhir_export(self, patient_id: int):
        r = requests.get(f"{self.base_url}/api/doctor/patients/{patient_id}/fhir-export", headers=self._get_headers())
        r.raise_for_status()
        return r

api_client = APIClient()
