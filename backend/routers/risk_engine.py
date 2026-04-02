"""
MedBridge — Health Risk Score Engine
Reads unstructured Document content and extracts clinical markers via regex,
then grades the patient's Cardiovascular, Diabetes, and Kidney risk dimensions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re
from datetime import datetime

from backend.models.database import get_db, Document, User
from backend.utils.auth_utils import get_current_user

router = APIRouter(prefix="/api", tags=["risk_engine"])


# ---------------------------------------------------------------------------
# Extraction Logic
# ---------------------------------------------------------------------------

def extract_metric(pattern: str, text: str):
    """Finds the first occurrence of a regex pattern in text and returns the capturing groups."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.groups() if match else None

def extract_keyword(pattern: str, text: str):
    """Returns True if keyword pattern is found in text."""
    return bool(re.search(pattern, text, re.IGNORECASE))


def run_extraction(patient_id: int, db: Session):
    """
    Sweeps through all documents belonging to a patient and extracts recent metrics.
    Returns dictionaries containing the extracted values.
    """
    docs = db.query(Document).filter(
        Document.patient_id == patient_id, 
        Document.content_text.isnot(None)
    ).order_by(Document.uploaded_at.desc()).all()

    extracted = {
        "bp": [], "ldl": [], "bmi": [], "hba1c": [], "glucose": [], 
        "creatinine": [], "egfr": [],
        "smoker": [], "fhx_heart": [], "diabetes_dx": [], "proteinuria": [], "ckd_dx": []
    }

    # Iterate over documents (most recent first)
    for doc in docs:
        text = doc.content_text
        source_info = {"file": doc.original_filename, "date": doc.uploaded_at.strftime("%Y-%m-%d")}

        # Quantitative Metrics
        if bp := extract_metric(r'(?:bp|blood pressure)[\s:=]*(\d{2,3})\s*/\s*(\d{2,3})', text):
            extracted["bp"].append({"value": f"{bp[0]}/{bp[1]}", "sys": int(bp[0]), "dia": int(bp[1]), **source_info})
        
        if ldl := extract_metric(r'(?:ldl|low[-\s]density lipoprotein)[\s:=]*(\d{2,3}(?:\.\d+)?)', text):
            extracted["ldl"].append({"value": float(ldl[0]), **source_info})

        if bmi := extract_metric(r'(?:bmi|body mass index)[\s:=]*(\d{2}(?:\.\d+)?)', text):
            extracted["bmi"].append({"value": float(bmi[0]), **source_info})

        if hba1c := extract_metric(r'(?:hba1c|a1c|hemoglobin a1c)[\s:=]*(\d+(?:\.\d+)?)', text):
            extracted["hba1c"].append({"value": float(hba1c[0]), **source_info})

        if glu := extract_metric(r'(?:fasting glucose|fbs|fasting blood sugar)[\s:=]*(\d{2,3}(?:\.\d+)?)', text):
            extracted["glucose"].append({"value": float(glu[0]), **source_info})

        if cr := extract_metric(r'(?:creatinine|cr)[\s:=]*(\d+(?:\.\d+)?)', text):
            extracted["creatinine"].append({"value": float(cr[0]), **source_info})

        if egfr := extract_metric(r'(?:egfr|gfr|estimated glomerular filtration rate)[\s:=]*(\d+(?:\.\d+)?)', text):
            extracted["egfr"].append({"value": float(egfr[0]), **source_info})

        # Qualitative Keywords
        if extract_keyword(r'\b(smoker|smoking|tobacco use)\b', text):
            extracted["smoker"].append({"value": "Yes", **source_info})
            
        if extract_keyword(r'\b(family history.*heart|fhx.*heart|family.*cardiovascular)\b', text):
            extracted["fhx_heart"].append({"value": "Yes", **source_info})
            
        if extract_keyword(r'\b(diabetes|type 2|type 1|t2dm|t1dm)\b(?!\s*negative|\s*none)', text):
            extracted["diabetes_dx"].append({"value": "Yes", **source_info})
            
        if extract_keyword(r'\b(proteinuria|protein in urine)\b', text):
            extracted["proteinuria"].append({"value": "Yes", **source_info})
            
        if extract_keyword(r'\b(ckd|chronic kidney disease)\b(?!\s*negative|\s*none)', text):
            extracted["ckd_dx"].append({"value": "Yes", **source_info})

    return extracted

# ---------------------------------------------------------------------------
# Scoring Logic
# ---------------------------------------------------------------------------

def _determine_level(score):
    if score <= 35: return "LOW"
    if score <= 65: return "MEDIUM"
    return "HIGH"

def calculate_risk_scores(patient: User, extracted: dict):
    report = {
        "cardiovascular": {"score": 0, "level": "LOW", "risk_factors": [], "protective_factors": [], "discuss": [], "data_points": 0},
        "diabetes": {"score": 0, "level": "LOW", "risk_factors": [], "protective_factors": [], "discuss": [], "data_points": 0},
        "kidney": {"score": 0, "level": "LOW", "risk_factors": [], "protective_factors": [], "discuss": [], "data_points": 0},
    }

    # Extract single strongest/latest signals for scoring
    # ── CARDIOVASCULAR ──
    v_cardio = report["cardiovascular"]
    cardio_score = 0
    
    # Age factor
    if patient.date_of_birth:
        age_days = (datetime.utcnow().date() - patient.date_of_birth).days
        age_years = age_days / 365.25
        if age_years > 50:
            cardio_score += 20
            v_cardio["risk_factors"].append({"factor": "Age above 50", "value": f"{int(age_years)} years", "source": "Profile", "date": ""})
            v_cardio["data_points"] += 1

    if extracted["bp"]:
        v_cardio["data_points"] += 1
        latest = extracted["bp"][0]
        if latest["sys"] > 140 or latest["dia"] > 90:
            cardio_score += 25
            v_cardio["risk_factors"].append({"factor": "High Blood Pressure", "value": latest["value"], "source": latest["file"], "date": latest["date"]})
            v_cardio["discuss"].append("Discuss blood pressure management and potential medication.")
        else:
            v_cardio["protective_factors"].append({"factor": "Normal Blood Pressure", "value": latest["value"], "source": latest["file"], "date": latest["date"]})

    if extracted["ldl"]:
        v_cardio["data_points"] += 1
        latest = extracted["ldl"][0]
        if latest["value"] > 130:
            cardio_score += 25
            v_cardio["risk_factors"].append({"factor": "Elevated LDL Cholesterol", "value": f"{latest['value']} mg/dL", "source": latest["file"], "date": latest["date"]})
            v_cardio["discuss"].append("Review dietary changes or statin therapy for cholesterol.")
        else:
            v_cardio["protective_factors"].append({"factor": "Controlled LDL", "value": f"{latest['value']} mg/dL", "source": latest["file"], "date": latest["date"]})

    if extracted["bmi"]:
        v_cardio["data_points"] += 1
        latest = extracted["bmi"][0]
        if latest["value"] > 25:
            cardio_score += 15
            v_cardio["risk_factors"].append({"factor": "Overweight BMI", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})
        else:
            v_cardio["protective_factors"].append({"factor": "Healthy BMI", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})

    if extracted["smoker"]:
        v_cardio["data_points"] += 1
        latest = extracted["smoker"][0]
        cardio_score += 30
        v_cardio["risk_factors"].append({"factor": "Smoking History", "value": "Yes", "source": latest["file"], "date": latest["date"]})
        v_cardio["discuss"].append("Discuss smoking cessation programs.")

    if extracted["fhx_heart"]:
        v_cardio["data_points"] += 1
        latest = extracted["fhx_heart"][0]
        cardio_score += 15
        v_cardio["risk_factors"].append({"factor": "Family History of Heart Disease", "value": "Yes", "source": latest["file"], "date": latest["date"]})

    v_cardio["score"] = min(100, cardio_score)
    v_cardio["level"] = _determine_level(v_cardio["score"])


    # ── DIABETES ──
    v_diab = report["diabetes"]
    diab_score = 0

    if extracted["hba1c"]:
        v_diab["data_points"] += 1
        latest = extracted["hba1c"][0]
        if latest["value"] > 6.5:
            diab_score += 70  # Instant high risk
            v_diab["risk_factors"].append({"factor": "High HbA1c (Diabetic Range)", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})
            v_diab["discuss"].append("Review aggressive A1c management protocols.")
        elif latest["value"] >= 5.7:
            diab_score += 45  # Medium risk
            v_diab["risk_factors"].append({"factor": "Elevated HbA1c (Prediabetic)", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})
            v_diab["discuss"].append("Discuss lifestyle interventions to prevent diabetes progression.")
        else:
            v_diab["protective_factors"].append({"factor": "Normal HbA1c", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})

    # Trending upward check
    if len(extracted["hba1c"]) >= 2:
        diff = extracted["hba1c"][0]["value"] - extracted["hba1c"][-1]["value"]
        if diff > 0.2:
            diab_score += 20
            v_diab["risk_factors"].append({"factor": "Trending Upward", "value": f"+{diff:.1f} since oldest record", "source": "Aggregate", "date": ""})

    if extracted["glucose"]:
        v_diab["data_points"] += 1
        latest = extracted["glucose"][0]
        if latest["value"] > 126:
            diab_score += 30
            v_diab["risk_factors"].append({"factor": "High Fasting Glucose", "value": f"{latest['value']} mg/dL", "source": latest["file"], "date": latest["date"]})
        else:
            v_diab["protective_factors"].append({"factor": "Normal Fasting Glucose", "value": f"{latest['value']} mg/dL", "source": latest["file"], "date": latest["date"]})

    if extracted["diabetes_dx"]:
        v_diab["data_points"] += 1
        latest = extracted["diabetes_dx"][0]
        diab_score += 50
        v_diab["risk_factors"].append({"factor": "Diabetes Diagnosis present in notes", "value": "Yes", "source": latest["file"], "date": latest["date"]})

    v_diab["score"] = min(100, diab_score)
    v_diab["level"] = _determine_level(v_diab["score"])


    # ── KIDNEY FUNCTION ──
    v_kidney = report["kidney"]
    kid_score = 0

    if extracted["creatinine"]:
        v_kidney["data_points"] += 1
        latest = extracted["creatinine"][0]
        # Simplification: we'll use > 1.2 as risk threshold for both since gender isn't readily available without complex extraction
        if latest["value"] > 1.2:
            kid_score += 30
            v_kidney["risk_factors"].append({"factor": "Elevated Creatinine", "value": f"{latest['value']} mg/dL", "source": latest["file"], "date": latest["date"]})
            v_kidney["discuss"].append("Monitor kidney function / creatinine levels.")
        else:
            v_kidney["protective_factors"].append({"factor": "Normal Creatinine", "value": f"{latest['value']} mg/dL", "source": latest["file"], "date": latest["date"]})

    if extracted["egfr"]:
        v_kidney["data_points"] += 1
        latest = extracted["egfr"][0]
        if latest["value"] < 60:
            kid_score += 70  # Instant high risk
            v_kidney["risk_factors"].append({"factor": "Low eGFR", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})
            v_kidney["discuss"].append("Urgent review of eGFR decline and kidney sparing strategies.")
        elif latest["value"] > 90:
            v_kidney["protective_factors"].append({"factor": "Healthy eGFR", "value": str(latest["value"]), "source": latest["file"], "date": latest["date"]})

    if extracted["proteinuria"]:
        v_kidney["data_points"] += 1
        latest = extracted["proteinuria"][0]
        kid_score += 40
        v_kidney["risk_factors"].append({"factor": "Protein in Urine", "value": "Yes", "source": latest["file"], "date": latest["date"]})
        v_kidney["discuss"].append("Follow up on proteinuria findings.")

    if extracted["ckd_dx"]:
        v_kidney["data_points"] += 1
        latest = extracted["ckd_dx"][0]
        kid_score += 50
        v_kidney["risk_factors"].append({"factor": "CKD Diagnosis present in notes", "value": "Yes", "source": latest["file"], "date": latest["date"]})

    v_kidney["score"] = min(100, kid_score)
    v_kidney["level"] = _determine_level(v_kidney["score"])

    # ── INSUFFICIENT DATA CHECK ──
    for dim in ["cardiovascular", "diabetes", "kidney"]:
        if report[dim]["data_points"] < 2:
            report[dim]["status"] = "INSUFFICIENT_DATA"
            report[dim]["score"] = 0
            report[dim]["level"] = "UNKNOWN"
        else:
            report[dim]["status"] = "CALCULATED"

    # Overall score (average of valid domains)
    valid_scores = [report[d]["score"] for d in ["cardiovascular", "diabetes", "kidney"] if report[d]["status"] == "CALCULATED"]
    
    report["overall_score"] = int(sum(valid_scores) / len(valid_scores)) if valid_scores else 0
    report["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    return report


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@router.get("/patient/risk-score")
def get_patient_risk_score(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    extracted = run_extraction(current_user.id, db)
    return calculate_risk_scores(current_user, extracted)


@router.get("/doctor/patients/{patient_id}/risk-score")
def get_doctor_patient_risk_score(patient_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    extracted = run_extraction(patient_id, db)
    return calculate_risk_scores(patient, extracted)
