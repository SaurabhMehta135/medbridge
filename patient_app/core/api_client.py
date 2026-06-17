import requests
import streamlit as st
from .config import config

class APIClient:
    def __init__(self):
        self.base_url = config.API_BASE
        
    def _get_headers(self):
        token = st.session_state.get("token")
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
        
    def reset_password(self, email: str, new_password: str) -> dict:
        r = requests.post(f"{self.base_url}/api/auth/reset-password", json={"email": email, "new_password": new_password})
        r.raise_for_status()
        return r.json()
        
    def get_documents(self) -> list:
        r = requests.get(f"{self.base_url}/api/patient/documents", headers=self._get_headers())
        r.raise_for_status()
        return r.json()
        
    def get_access_codes(self) -> list:
        r = requests.get(f"{self.base_url}/api/patient/access-codes", headers=self._get_headers())
        r.raise_for_status()
        return r.json()
        
    def get_alerts(self, user_id: int) -> list:
        r = requests.get(f"{self.base_url}/api/alerts/{user_id}", headers=self._get_headers())
        r.raise_for_status()
        return r.json()
        
    def regenerate_document_summary(self, doc_id: int) -> dict:
        r = requests.post(f"{self.base_url}/api/patient/documents/{doc_id}/regenerate-summary", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def get_patient_risk_score(self) -> dict:
        r = requests.get(f"{self.base_url}/api/patient/risk-score", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def get_patient_followups(self) -> list:
        r = requests.get(f"{self.base_url}/api/patient/followups", headers=self._get_headers())
        r.raise_for_status()
        return r.json()

    def send_chat_message(self, message: str) -> dict:
        r = requests.post(
            f"{self.base_url}/api/chat/patient",
            json={"message": message},
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def mark_followup_complete(self, followup_id: int, notes: str) -> dict:
        r = requests.put(
            f"{self.base_url}/api/patient/followups/{followup_id}/complete",
            json={"notes": notes},
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def generate_access_code(self, expires_in_days: int) -> dict:
        r = requests.post(
            f"{self.base_url}/api/patient/access-codes",
            json={"expires_in_days": expires_in_days},
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def revoke_access_code(self, code: str) -> dict:
        r = requests.delete(
            f"{self.base_url}/api/patient/access-codes/{code}",
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def upload_document(self, files: dict, data: dict) -> dict:
        r = requests.post(
            f"{self.base_url}/api/patient/documents",
            files=files,
            data=data,
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def process_document(self, doc_id: int) -> dict:
        r = requests.post(
            f"{self.base_url}/api/patient/documents/{doc_id}/process",
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def get_document_summary(self, doc_id: int) -> dict:
        r = requests.get(
            f"{self.base_url}/api/patient/documents/{doc_id}/summary",
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

    def delete_document(self, doc_id: int) -> dict:
        r = requests.delete(
            f"{self.base_url}/api/patient/documents/{doc_id}",
            headers=self._get_headers()
        )
        r.raise_for_status()
        return r.json()

api_client = APIClient()
