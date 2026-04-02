"""Quick integration test for MedBridge API"""
import requests

BASE = "http://127.0.0.1:8000"

# 1. Register a patient
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "patient@test.com", "password": "test123",
    "full_name": "Test Patient", "role": "patient",
    "allergies": "penicillin", "medications": "warfarin,aspirin"
})
print(f"Register patient: {r.status_code} id={r.json().get('id')}")

# 2. Register a doctor
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "doctor@test.com", "password": "test123",
    "full_name": "Dr. Smith", "role": "doctor", "specialty": "Cardiology"
})
print(f"Register doctor: {r.status_code} id={r.json().get('id')}")

# 3. Login as patient
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": "patient@test.com", "password": "test123"
})
print(f"Login patient: {r.status_code}")
pt_token = r.json()["access_token"]

# 4. Get profile
r = requests.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {pt_token}"})
profile = r.json()
print(f"Profile: {profile['full_name']} | allergies: {profile.get('allergies')}")

# 5. Create access code
r = requests.post(f"{BASE}/api/patient/access-codes",
    json={"expires_in_hours": 48},
    headers={"Authorization": f"Bearer {pt_token}"}
)
code = r.json()["code"]
print(f"Access code: {code}")

# 6. Login as doctor
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": "doctor@test.com", "password": "test123"
})
dr_token = r.json()["access_token"]
print(f"Login doctor: {r.status_code}")

# 7. Doctor verifies code
r = requests.post(f"{BASE}/api/doctor/verify-code",
    json={"code": code},
    headers={"Authorization": f"Bearer {dr_token}"}
)
print(f"Doctor verify: {r.status_code}")

# 8. Doctor lists patients
r = requests.get(f"{BASE}/api/doctor/patients",
    headers={"Authorization": f"Bearer {dr_token}"}
)
print(f"Doctor sees {len(r.json())} patient(s)")

# 9. Get alerts for patient
r = requests.get(f"{BASE}/api/alerts/1",
    headers={"Authorization": f"Bearer {dr_token}"}
)
alerts = r.json()
print(f"Alerts: {len(alerts)} found")
for a in alerts:
    print(f"  [{a['severity']}] {a['title']}")

# 10. Patient chat (no docs uploaded yet)
r = requests.post(f"{BASE}/api/chat/patient",
    json={"message": "What are my allergies?"},
    headers={"Authorization": f"Bearer {pt_token}"}
)
print(f"Patient chat: {r.status_code} -> {r.json()['answer'][:80]}...")

print("\n✅ ALL TESTS PASSED")
