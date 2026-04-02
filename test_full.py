"""Full end-to-end test: register, upload medical data, chat with LLM via Groq"""
import requests
import os

BASE = "http://127.0.0.1:8000"

# 1. Register patient with medical profile
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "alice@test.com", "password": "test123",
    "full_name": "Alice Johnson", "role": "patient",
    "blood_type": "O+",
    "allergies": "penicillin,sulfa",
    "medications": "metformin,lisinopril",
    "date_of_birth": "1985-03-15",
    "emergency_contact_name": "Bob Johnson",
    "emergency_contact_phone": "+1-555-0123",
})
print(f"1. Register: {r.status_code}")

# 2. Login
r = requests.post(f"{BASE}/api/auth/login", json={"email": "alice@test.com", "password": "test123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"2. Login: {r.status_code}")

# 3. Upload a sample medical document (create a fake text file with medical content)
sample_medical_text = """
PATIENT: Alice Johnson
DOB: 03/15/1985
DATE: 01/15/2026

DISCHARGE SUMMARY

CHIEF COMPLAINT: Chest pain and shortness of breath.

HISTORY OF PRESENT ILLNESS:
Patient is a 40-year-old female presenting with intermittent chest pain for 3 days.
Pain is described as pressure-like, radiating to the left arm, worse with exertion.
Associated with mild shortness of breath and diaphoresis.

PAST MEDICAL HISTORY:
- Type 2 Diabetes Mellitus (diagnosed 2018)
- Hypertension (diagnosed 2019)
- Hyperlipidemia

MEDICATIONS:
- Metformin 1000mg BID
- Lisinopril 20mg daily
- Atorvastatin 40mg daily

ALLERGIES: Penicillin (rash), Sulfa drugs (anaphylaxis)

PHYSICAL EXAMINATION:
- BP: 145/92 mmHg
- HR: 88 bpm
- RR: 18
- SpO2: 97% on room air
- Heart: Regular rate and rhythm, no murmurs
- Lungs: Clear to auscultation bilaterally

LABORATORY RESULTS:
- Troponin I: 0.02 ng/mL (normal <0.04)
- BNP: 125 pg/mL (mildly elevated)
- HbA1c: 7.8% (above target)
- Creatinine: 1.1 mg/dL
- eGFR: 72 mL/min
- Total Cholesterol: 220 mg/dL
- LDL: 140 mg/dL (above target)
- Fasting Glucose: 165 mg/dL (elevated)

ECG: Normal sinus rhythm, no ST changes.

ASSESSMENT:
1. Chest pain - likely musculoskeletal, cardiac workup negative
2. Type 2 DM - suboptimally controlled (HbA1c 7.8%)
3. Hypertension - not at goal
4. Hyperlipidemia - LDL above target

PLAN:
1. Increase Metformin to 1500mg BID
2. Add Amlodipine 5mg daily for BP control
3. Continue Atorvastatin, consider dose increase
4. Cardiac stress test as outpatient
5. Follow up in 2 weeks
"""

# Upload as a text file
files = {"file": ("discharge_summary_2026.txt", sample_medical_text.encode(), "text/plain")}
data = {"doc_type": "discharge_summary"}
r = requests.post(f"{BASE}/api/patient/documents/upload", files=files, data=data, headers=headers)
doc_id = r.json()["id"]
print(f"3. Upload doc: {r.status_code} (id={doc_id})")

# 4. Get alerts
r = requests.get(f"{BASE}/api/alerts/{1}", headers=headers)
alerts = r.json()
print(f"4. Alerts: {len(alerts)} found")
for a in alerts:
    sev = a["severity"]
    print(f"   [{sev}] {a['title']}")

# 5. Patient chat (keyword-based, since doc not yet processed for RAG)
r = requests.post(f"{BASE}/api/chat/patient",
    json={"message": "What were my lab results?"},
    headers=headers
)
print(f"5. Chat (keyword): {r.status_code}")
print(f"   Answer: {r.json()['answer'][:150]}...")

# 6. Test Groq API directly (quick validation)
print(f"\n6. Testing Groq LLM directly...")
try:
    from openai import OpenAI
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        raise ValueError("GROQ_API_KEY is not set")
    client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        max_tokens=150,
        temperature=0.3,
        messages=[
            {"role": "system", "content": "You are a medical assistant. Be concise."},
            {"role": "user", "content": "What does an HbA1c of 7.8% mean for a diabetic patient?"},
        ],
    )
    answer = resp.choices[0].message.content
    print(f"   Model: {resp.model}")
    print(f"   Answer: {answer[:200]}...")
    print(f"   ✅ Groq LLaMA 4 Scout is WORKING!")
except Exception as e:
    print(f"   ❌ Groq error: {e}")

print("\n✅ ALL TESTS COMPLETE")
