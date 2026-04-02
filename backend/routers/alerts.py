"""
MedBridge — Alerts Router

GET /api/alerts/{patient_id}  — get drug interaction & allergy alerts for a patient

This is a rule-based stub. The full AI-powered drug checker
(ai_pipeline/drug_checker.py) will be wired in Phase 2.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db, User, Document
from backend.models.schemas import AlertOut
from backend.utils.auth_utils import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# ---------------------------------------------------------------------------
# Known Drug Interactions (simplified rule-based list)
# Will be replaced by ai_pipeline/drug_checker.py in Phase 2
# ---------------------------------------------------------------------------

KNOWN_INTERACTIONS = {
    frozenset({"warfarin", "aspirin"}): {
        "severity": "critical",
        "title": "Warfarin + Aspirin Interaction",
        "description": "Concurrent use significantly increases bleeding risk. Monitor INR closely.",
    },
    frozenset({"metformin", "contrast dye"}): {
        "severity": "warning",
        "title": "Metformin + Contrast Dye Risk",
        "description": "Metformin should be paused 48h before and after contrast imaging to prevent lactic acidosis.",
    },
    frozenset({"lisinopril", "potassium"}): {
        "severity": "warning",
        "title": "ACE Inhibitor + Potassium Risk",
        "description": "ACE inhibitors increase potassium retention. Supplemental potassium may cause hyperkalemia.",
    },
    frozenset({"ssri", "maoi"}): {
        "severity": "critical",
        "title": "SSRI + MAOI Interaction",
        "description": "Concurrent use can cause serotonin syndrome, a potentially life-threatening condition.",
    },
    frozenset({"simvastatin", "amiodarone"}): {
        "severity": "warning",
        "title": "Simvastatin + Amiodarone Interaction",
        "description": "Increased risk of rhabdomyolysis. Simvastatin dose should not exceed 20mg.",
    },
}

COMMON_ALLERGENS = {
    "penicillin", "sulfa", "latex", "iodine", "nsaid", "aspirin",
    "codeine", "morphine", "cephalosporin",
}


def _parse_list(text: str | None) -> list[str]:
    if not text:
        return []
    return [item.strip().lower() for item in text.split(",") if item.strip()]


def _check_interactions(medications: list[str]) -> list[AlertOut]:
    alerts = []
    meds_set = set(medications)
    for pair, info in KNOWN_INTERACTIONS.items():
        if pair.issubset(meds_set):
            alerts.append(AlertOut(
                alert_type="drug_interaction",
                severity=info["severity"],
                title=info["title"],
                description=info["description"],
                related_drugs=list(pair),
            ))
    return alerts


def _check_allergies(allergies: list[str], medications: list[str]) -> list[AlertOut]:
    alerts = []
    allergy_set = set(allergies)
    med_set = set(medications)

    # Simple cross-check: if a medication name appears in allergies
    overlap = allergy_set & med_set
    for drug in overlap:
        alerts.append(AlertOut(
            alert_type="allergy",
            severity="critical",
            title=f"Allergy Alert: {drug.title()}",
            description=f"Patient is allergic to {drug} but it appears in their current medications.",
            related_drugs=[drug],
        ))

    # Penicillin ↔ cephalosporin cross-reactivity
    if "penicillin" in allergy_set and "cephalosporin" in med_set:
        alerts.append(AlertOut(
            alert_type="allergy",
            severity="warning",
            title="Penicillin–Cephalosporin Cross-Reactivity",
            description="Patient has penicillin allergy. Cephalosporins may trigger a cross-reaction (~1-2% risk).",
            related_drugs=["penicillin", "cephalosporin"],
        ))

    return alerts


@router.get("/{patient_id}", response_model=list[AlertOut])
def get_alerts(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate alerts for a patient based on their profile and documents.
    Accessible by the patient themselves or a doctor with valid access.
    """
    # Authorization check
    if current_user.role == "patient" and current_user.id != patient_id:
        raise HTTPException(status_code=403, detail="You can only view your own alerts")

    if current_user.role == "doctor":
        from backend.routers.doctor import _doctor_can_access_patient
        if not _doctor_can_access_patient(current_user.id, patient_id, db):
            raise HTTPException(status_code=403, detail="You don't have access to this patient")

    # Fetch patient
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    allergies = _parse_list(patient.allergies)
    medications = _parse_list(patient.medications)

    all_alerts: list[AlertOut] = []
    all_alerts.extend(_check_interactions(medications))
    all_alerts.extend(_check_allergies(allergies, medications))

    # Also scan document text for medication mentions (basic)
    docs = db.query(Document).filter(Document.patient_id == patient_id).all()
    doc_meds_found = set()
    for doc in docs:
        if doc.content_text:
            text_lower = doc.content_text.lower()
            for allergen in allergies:
                if allergen in text_lower and allergen not in medications:
                    doc_meds_found.add(allergen)

    for drug in doc_meds_found:
        all_alerts.append(AlertOut(
            alert_type="allergy",
            severity="warning",
            title=f"Potential Allergen Found in Records: {drug.title()}",
            description=f"The allergen '{drug}' was mentioned in uploaded documents. Please verify.",
            related_drugs=[drug],
        ))

    return all_alerts
