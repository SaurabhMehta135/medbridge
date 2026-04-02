"""
MedBridge — Doctor Router

POST /api/doctor/verify-code         — verify an access code, link doctor
GET  /api/doctor/patients            — list patients the doctor has access to
GET  /api/doctor/patients/{pid}/docs — list documents for a specific patient
GET  /api/doctor/patients/{pid}/docs/{did} — get document detail
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import json
import io
import zipfile

from backend.models.database import get_db, User, Document, AccessCode, FollowUp
from backend.models.schemas import (
    AccessCodeVerify, AccessCodeOut, DocumentOut, DocumentDetail, UserOut, FollowUpOut, FollowUpCreate
)
from backend.utils.auth_utils import require_role
from backend.ai_pipeline.fhir_exporter import generate_patient_fhir_bundle
from backend.routers.risk_engine import run_extraction, calculate_risk_scores

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_valid_patient_ids(doctor_id: int, db: Session) -> list[int]:
    """Return patient IDs the doctor currently has valid (non-expired, non-revoked) access to."""
    now = datetime.utcnow()
    codes = (
        db.query(AccessCode)
        .filter(
            AccessCode.doctor_id == doctor_id,
            AccessCode.is_revoked == False,
            AccessCode.expires_at > now,
        )
        .all()
    )
    return list({c.patient_id for c in codes})


def _doctor_can_access_patient(doctor_id: int, patient_id: int, db: Session) -> bool:
    return patient_id in _get_valid_patient_ids(doctor_id, db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/verify-code", response_model=AccessCodeOut)
def verify_access_code(
    payload: AccessCodeVerify,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    ac = db.query(AccessCode).filter(AccessCode.code == payload.code).first()
    if not ac:
        raise HTTPException(status_code=404, detail="Access code not found")
    if ac.is_revoked:
        raise HTTPException(status_code=400, detail="Access code has been revoked")
    if ac.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Access code has expired")

    # Link doctor if not already linked
    if ac.doctor_id is None:
        ac.doctor_id = current_user.id
        db.commit()
        db.refresh(ac)
    elif ac.doctor_id != current_user.id:
        raise HTTPException(status_code=400, detail="Access code already claimed by another doctor")

    logger.info(f"Doctor {current_user.id} verified code {payload.code} for patient {ac.patient_id}")
    return ac


@router.get("/patients", response_model=list[UserOut])
def list_patients(
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    patient_ids = _get_valid_patient_ids(current_user.id, db)
    if not patient_ids:
        return []
    patients = db.query(User).filter(User.id.in_(patient_ids)).all()
    return patients


@router.get("/patients/{patient_id}/docs", response_model=list[DocumentOut])
def list_patient_documents(
    patient_id: int,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    if not _doctor_can_access_patient(current_user.id, patient_id, db):
        raise HTTPException(status_code=403, detail="You don't have access to this patient")

    docs = (
        db.query(Document)
        .filter(Document.patient_id == patient_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return docs


@router.get("/patients/{patient_id}/docs/{doc_id}", response_model=DocumentDetail)
def get_patient_document(
    patient_id: int,
    doc_id: int,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    if not _doctor_can_access_patient(current_user.id, patient_id, db):
        raise HTTPException(status_code=403, detail="You don't have access to this patient")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.patient_id == patient_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# ---------------------------------------------------------------------------
# FollowUps
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}/followups", response_model=list[FollowUpOut])
def list_doctor_patient_followups(
    patient_id: int,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    if not _doctor_can_access_patient(current_user.id, patient_id, db):
        raise HTTPException(status_code=403, detail="You don't have access to this patient")

    return db.query(FollowUp).filter(FollowUp.patient_id == patient_id).all()


@router.post("/patients/{patient_id}/followups", response_model=FollowUpOut, status_code=201)
def add_patient_followup(
    patient_id: int,
    payload: FollowUpCreate,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    if not _doctor_can_access_patient(current_user.id, patient_id, db):
        raise HTTPException(status_code=403, detail="You don't have access to this patient")

    fup = FollowUp(
        patient_id=patient_id,
        document_id=None, # Manually created logically separated from a document
        follow_up_type=payload.follow_up_type,
        description=payload.description,
        timeframe_text=payload.timeframe_text,
        due_date=payload.due_date,
        urgency=payload.urgency,
        specialty=payload.specialty,
        status="pending",
        notes=payload.notes,
    )
    db.add(fup)
    db.commit()
    db.refresh(fup)
    return fup

# ---------------------------------------------------------------------------
# FHIR Export
# ---------------------------------------------------------------------------

@router.get("/patients/{patient_id}/fhir-export")
def export_patient_fhir(
    patient_id: int,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    if not _doctor_can_access_patient(current_user.id, patient_id, db):
        raise HTTPException(status_code=403, detail="You don't have access to this patient")
        
    patient = db.query(User).filter(User.id == patient_id).first()
    bundle = generate_patient_fhir_bundle(patient, db)
    return Response(content=json.dumps(bundle, indent=2), media_type="application/fhir+json")

@router.get("/fhir-export-all")
def export_all_patients_fhir(
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    patient_ids = _get_valid_patient_ids(current_user.id, db)
    if not patient_ids:
        raise HTTPException(status_code=404, detail="No patients found")
        
    patients = db.query(User).filter(User.id.in_(patient_ids)).all()
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for p in patients:
            bundle = generate_patient_fhir_bundle(p, db)
            zip_file.writestr(
                f"medbridge_fhir_{p.full_name.replace(' ', '_').lower()}.json",
                json.dumps(bundle, indent=2)
            )
            
    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=medbridge_all_patients_fhir_{datetime.utcnow().strftime('%Y%m%d')}.zip"}
    )

# ---------------------------------------------------------------------------
# Analytics Dashboard
# ---------------------------------------------------------------------------

@router.get("/analytics")
def get_doctor_analytics(
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    patient_ids = _get_valid_patient_ids(current_user.id, db)
    if not patient_ids:
        return {
            "total_patients": 0, "high_risk_patients": 0, "followups_due_week": 0, "overdue_followups": 0,
            "attention_needed": [], "condition_dist": {}, "risk_dist": {"High Risk": 0, "Medium Risk": 0, "Low Risk": 0, "No Data": 0},
            "compliance_timeline": {}, "recent_activity": []
        }
        
    patients = db.query(User).filter(User.id.in_(patient_ids)).all()
    now = datetime.utcnow()
    
    # Init metrics
    high_risk_count = 0
    condition_counts = {"Hypertension": 0, "Type 2 Diabetes": 0, "Chronic Kidney Disease": 0, "Cardiac/Other": 0}
    risk_dist = {"High Risk": 0, "Medium Risk": 0, "Low Risk": 0, "No Data": 0}
    attention_needed = []
    recent_activity = []
    
    # Followup arrays
    all_followups = db.query(FollowUp).filter(FollowUp.patient_id.in_(patient_ids)).all()
    docs = db.query(Document).filter(Document.patient_id.in_(patient_ids)).order_by(Document.uploaded_at.desc()).limit(20).all()
    
    # Follow-up stats
    due_this_week = 0
    overdue_count = 0
    
    # Group followups by patient
    fup_by_patient = {pid: [] for pid in patient_ids}
    for f in all_followups:
        fup_by_patient[f.patient_id].append(f)
        
        # Timeline logic (last 6 months)
        if f.due_date and f.status != "pending":
            ra = f"fup_done|{f.patient_id}|{f.status}|{f.completed_at}|{f.description}"
            recent_activity.append((f.completed_at or f.due_date, f.patient_id, "completed a follow-up: " + f.description))
            
    # Add docs to recent activity
    for d in docs:
        recent_activity.append((d.uploaded_at, d.patient_id, "uploaded a new document: " + d.original_filename))
        
    for p in patients:
        urgency_tags = []
        patient_fups = fup_by_patient[p.id]
        
        # Check follow-ups
        has_overdue = False
        has_due_soon = False
        for f in patient_fups:
            if f.status == "pending" and f.due_date:
                days_diff = (f.due_date - now.date()).days
                if days_diff < 0 or f.status == "overdue":
                    has_overdue = True
                elif 0 <= days_diff <= 7:
                    has_due_soon = True
                    
        if has_overdue:
            overdue_count += 1
            urgency_tags.append("🔴 Overdue Follow-up")
        if has_due_soon:
            due_this_week += 1
            
        # Check new docs in last 24h
        p_docs = [d for d in docs if d.patient_id == p.id and (now - d.uploaded_at).days <= 1]
        if p_docs:
            urgency_tags.append("🟡 New Documents")
            
        # Run Risk Extraction
        extracted = run_extraction(p.id, db)
        risk_report = calculate_risk_scores(p, extracted)
        
        # Risk Distribution
        overall_score = risk_report.get("overall_score", 0)
        overall_level = "No Data"
        if risk_report["cardiovascular"]["status"] != "INSUFFICIENT_DATA":
            if overall_score > 65: overall_level = "High Risk"
            elif overall_score > 35: overall_level = "Medium Risk"
            else: overall_level = "Low Risk"
        risk_dist[overall_level] += 1
        
        if overall_level == "High Risk":
            high_risk_count += 1
            urgency_tags.append("🔴 High Risk")
            
        # Conditions
        if extracted.get("bp") and any((b.get("sys",0)>140 or b.get("dia",0)>90) for b in extracted["bp"]):
            condition_counts["Hypertension"] += 1
        if extracted.get("diabetes_dx") or (extracted.get("hba1c") and any(b.get("value",0)>6.4 for b in extracted["hba1c"])):
            condition_counts["Type 2 Diabetes"] += 1
        if extracted.get("ckd_dx") or (extracted.get("egfr") and any(b.get("value",100)<60 for b in extracted["egfr"])):
            condition_counts["Chronic Kidney Disease"] += 1
        if extracted.get("fhx_heart"):
            condition_counts["Cardiac/Other"] += 1
            
        if urgency_tags:
            # Sort by severity
            is_high = any("High" in t or "Overdue" in t for t in urgency_tags)
            attention_needed.append({
                "patient_id": p.id,
                "name": p.full_name,
                "initials": "".join([part[0] for part in p.full_name.split()][:2]),
                "tags": urgency_tags,
                "priority": 1 if is_high else 2,
                "last_active": p_docs[0].uploaded_at.strftime("%Y-%m-%d") if p_docs else p.created_at.strftime("%Y-%m-%d")
            })

    # Timeline compliance data
    timeline = []
    # Simplified mock for 6 months
    import calendar
    from dateutil.relativedelta import relativedelta
    
    month_names = []
    completed_trend = []
    missed_trend = []
    
    for i in range(5, -1, -1):
        m_date = now - relativedelta(months=i)
        month_names.append(m_date.strftime("%b %Y"))
        
        # count for this month
        c_done, c_miss = 0, 0
        for f in all_followups:
            if not f.due_date: continue
            if f.due_date.year == m_date.year and f.due_date.month == m_date.month:
                if f.status == "completed": c_done += 1
                elif f.status in ("overdue", "missed") or (f.status == "pending" and f.due_date < now.date()): c_miss += 1
        completed_trend.append(c_done)
        missed_trend.append(c_miss)
        
    timeline = {
        "months": month_names,
        "completed": completed_trend,
        "missed": missed_trend
    }
    
    # Sort Recent Activity
    recent_activity.sort(key=lambda x: x[0], reverse=True)
    recent_formatted = []
    for dt, pid, label in recent_activity[:10]:
        pname = next((p.full_name for p in patients if p.id == pid), "Patient")
        
        diff = now - (dt if isinstance(dt, datetime) else datetime.combine(dt, datetime.min.time()))
        if diff.days == 0:
            if diff.seconds < 3600: tz = f"{diff.seconds // 60} mins ago"
            else: tz = f"{diff.seconds // 3600} hours ago"
        elif diff.days == 1: tz = "yesterday"
        else: tz = f"{diff.days} days ago"

        recent_formatted.append({
            "patient_id": pid,
            "patient_name": pname,
            "action": label,
            "time_ago": tz
        })
        
    attention_needed.sort(key=lambda x: x["priority"])

    return {
        "total_patients": len(patients),
        "high_risk_patients": high_risk_count,
        "followups_due_week": due_this_week,
        "overdue_followups": overdue_count,
        "attention_needed": attention_needed[:8],
        "condition_dist": {k: v for k, v in condition_counts.items() if v > 0},
        "risk_dist": risk_dist,
        "compliance_timeline": timeline,
        "recent_activity": recent_formatted
    }
