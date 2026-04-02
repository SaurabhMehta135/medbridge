"""
MedBridge — Patient Router

GET    /api/patient/documents          — list patient's own documents
POST   /api/patient/documents/upload   — upload a medical document (PDF/TXT)
GET    /api/patient/documents/{id}     — get document detail
DELETE /api/patient/documents/{id}     — delete a document
POST   /api/patient/access-codes       — generate a sharing access code
GET    /api/patient/access-codes       — list active access codes
DELETE /api/patient/access-codes/{id}  — revoke an access code
"""

import os
import uuid
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.models.database import get_db, User, Document, AccessCode, FollowUp
from backend.models.schemas import (
    DocumentOut, DocumentDetail, AccessCodeCreate, AccessCodeOut, FollowUpOut, FollowUpUpdate
)
from backend.utils.auth_utils import require_role
from backend.utils.pdf_utils import extract_text_from_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patient", tags=["patient"])

UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

@router.get("/documents", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    docs = (
        db.query(Document)
        .filter(Document.patient_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return docs


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="general"),
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    # Validate file type
    allowed_extensions = {".pdf", ".txt"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported. Use PDF or TXT.")

    # Read and save file
    file_bytes = await file.read()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract text
    content_text = extract_text_from_file(file_bytes, file.filename)

    doc = Document(
        patient_id=current_user.id,
        filename=stored_name,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(file_bytes),
        content_text=content_text,
        doc_type=doc_type,
        is_processed=False,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"Patient {current_user.id} uploaded document {doc.id}: {file.filename}")
    return doc


@router.get("/documents/{doc_id}", response_model=DocumentDetail)
def get_document(
    doc_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.patient_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/documents/{doc_id}/process", response_model=DocumentOut)
def process_document_endpoint(
    doc_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    """Trigger AI processing (chunking + embedding) for a document."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.patient_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.is_processed:
        return doc  # Already processed

    if not doc.content_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text to process")

    try:
        from ai_pipeline.document_processor import process_document
        from ai_pipeline.report_summarizer import generate_report_summary
        
        num_chunks = process_document(
            patient_id=current_user.id,
            document_id=doc.id,
            content_text=doc.content_text,
            original_filename=doc.original_filename,
            doc_type=doc.doc_type,
        )
        doc.is_processed = True
        db.commit()
        db.refresh(doc)
        
        # Trigger the LLM Medical Report Summarizer to populate plain english fields
        generate_report_summary(doc.id, db)
        
        # Trigger the LLM Follow-Up Extractor
        try:
            from ai_pipeline.followup_extractor import extract_followups
            extracted_items = extract_followups(doc.id, db)
            logger.info(f"Document {doc.id}: extracted {len(extracted_items)} follow-up instructions.")
        except Exception as extractor_err:
            logger.error(f"Failed extracting follow-ups from doc {doc.id}: {extractor_err}")
        
        logger.info(f"Document {doc.id} processed: {num_chunks} chunks embedded")
    except Exception as e:
        logger.error(f"Failed to process document {doc.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return doc


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.patient_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete physical file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Delete ChromaDB chunks if processed
    if doc.is_processed:
        try:
            from ai_pipeline.document_processor import delete_document_chunks
            delete_document_chunks(current_user.id, doc.id)
        except Exception as e:
            logger.warning(f"Failed to delete ChromaDB chunks for doc {doc.id}: {e}")

    db.delete(doc)
    db.commit()


@router.get("/documents/{doc_id}/summary")
def get_document_summary(
    doc_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.patient_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "patient_summary": doc.patient_summary,
        "clinical_summary": doc.clinical_summary,
        "is_processed": doc.is_processed
    }


@router.post("/documents/{doc_id}/regenerate-summary")
def regenerate_document_summary(
    doc_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.patient_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        from ai_pipeline.report_summarizer import generate_report_summary
        updated_doc = generate_report_summary(doc.id, db)
        return {
            "patient_summary": updated_doc.patient_summary if updated_doc else None,
            "clinical_summary": updated_doc.clinical_summary if updated_doc else None
        }
    except Exception as e:
        logger.error(f"Failed to regenerate summary for doc {doc.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

# ---------------------------------------------------------------------------
# Access Codes
# ---------------------------------------------------------------------------

def _generate_code() -> str:
    """Generate a short, human-readable access code like MB-A3F9K2."""
    raw = uuid.uuid4().hex[:6].upper()
    return f"MB-{raw}"


@router.post("/access-codes", response_model=AccessCodeOut, status_code=201)
def create_access_code(
    payload: AccessCodeCreate,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    code = _generate_code()
    # Ensure uniqueness (very unlikely collision, but be safe)
    while db.query(AccessCode).filter(AccessCode.code == code).first():
        code = _generate_code()

    ac = AccessCode(
        patient_id=current_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(hours=payload.expires_in_hours),
    )
    db.add(ac)
    db.commit()
    db.refresh(ac)

    logger.info(f"Patient {current_user.id} created access code {code}")
    return ac


@router.get("/access-codes", response_model=list[AccessCodeOut])
def list_access_codes(
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    codes = (
        db.query(AccessCode)
        .filter(AccessCode.patient_id == current_user.id)
        .order_by(AccessCode.created_at.desc())
        .all()
    )
    return codes


@router.delete("/access-codes/{code_id}", status_code=204)
def revoke_access_code(
    code_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    ac = db.query(AccessCode).filter(
        AccessCode.id == code_id,
        AccessCode.patient_id == current_user.id,
    ).first()
    if not ac:
        raise HTTPException(status_code=404, detail="Access code not found")

    ac.is_revoked = True
    db.commit()


# ---------------------------------------------------------------------------
# FollowUps
# ---------------------------------------------------------------------------

@router.get("/followups", response_model=list[FollowUpOut])
def list_patient_followups(
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    return db.query(FollowUp).filter(FollowUp.patient_id == current_user.id).all()


@router.put("/followups/{followup_id}/complete", response_model=FollowUpOut)
def complete_followup(
    followup_id: int,
    payload: FollowUpUpdate,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    fup = db.query(FollowUp).filter(FollowUp.id == followup_id, FollowUp.patient_id == current_user.id).first()
    if not fup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
        
    fup.status = "completed"
    fup.completed_at = datetime.utcnow()
    fup.notes = payload.notes
    db.commit()
    db.refresh(fup)
    return fup


@router.put("/followups/{followup_id}/reschedule", response_model=FollowUpOut)
def reschedule_followup(
    followup_id: int,
    payload: FollowUpUpdate,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    fup = db.query(FollowUp).filter(FollowUp.id == followup_id, FollowUp.patient_id == current_user.id).first()
    if not fup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
        
    fup.due_date = payload.due_date
    if fup.status == "overdue":
        fup.status = "pending"
    db.commit()
    db.refresh(fup)
    return fup


@router.delete("/followups/{followup_id}")
def delete_followup(
    followup_id: int,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    fup = db.query(FollowUp).filter(FollowUp.id == followup_id, FollowUp.patient_id == current_user.id).first()
    if not fup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
        
    db.delete(fup)
    db.commit()
    return {"message": "Follow-up deleted"}
