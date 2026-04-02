"""
MedBridge — Chat Router

POST /api/chat/patient  — patient asks about their own records (RAG-powered)
POST /api/chat/doctor   — doctor asks about a specific patient's records (RAG-powered)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db, User, Document
from backend.models.schemas import ChatRequest, ChatResponse
from backend.utils.auth_utils import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _has_processed_docs(patient_id: int, db: Session) -> bool:
    """Check if the patient has any processed (embedded) documents."""
    return db.query(Document).filter(
        Document.patient_id == patient_id,
        Document.is_processed == True,
    ).first() is not None


def _simple_keyword_search(query: str, documents: list[Document]) -> dict:
    """
    Fallback keyword-based search when no documents have been embedded yet.
    """
    query_lower = query.lower()
    keywords = query_lower.split()
    relevant_snippets = []
    sources = []

    for doc in documents:
        if not doc.content_text:
            continue
        text_lower = doc.content_text.lower()
        if any(kw in text_lower for kw in keywords):
            snippet = doc.content_text[:500]
            relevant_snippets.append(f"[From: {doc.original_filename}]\n{snippet}")
            sources.append(doc.original_filename)

    if relevant_snippets:
        context = "\n\n---\n\n".join(relevant_snippets[:3])
        answer = (
            f"Based on your records, here's what I found:\n\n{context}\n\n"
            f"*Note: Documents are being processed for AI-powered search. "
            f"Results will improve once processing is complete.*"
        )
    else:
        answer = (
            "I couldn't find specific information about that in the uploaded documents. "
            "Try uploading more records or rephrasing your question."
        )

    return {"answer": answer, "sources": sources[:5]}


@router.post("/patient", response_model=ChatResponse)
def patient_chat(
    payload: ChatRequest,
    current_user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
):
    """Patient asks about their own health records — RAG-powered."""
    documents = (
        db.query(Document)
        .filter(Document.patient_id == current_user.id)
        .all()
    )

    if not documents:
        return ChatResponse(
            answer="You haven't uploaded any documents yet. Please upload your medical records first.",
            sources=[],
        )

    # Use RAG if documents have been processed, otherwise fallback
    if _has_processed_docs(current_user.id, db):
        try:
            from ai_pipeline.rag import generate_rag_response
            result = generate_rag_response(
                patient_id=current_user.id,
                user_message=payload.message,
                mode="patient",
            )
            return ChatResponse(answer=result["answer"], sources=result["sources"])
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            # Fall back to keyword search
            result = _simple_keyword_search(payload.message, documents)
            return ChatResponse(**result)
    else:
        result = _simple_keyword_search(payload.message, documents)
        return ChatResponse(**result)


@router.post("/doctor", response_model=ChatResponse)
def doctor_chat(
    payload: ChatRequest,
    current_user: User = Depends(require_role("doctor")),
    db: Session = Depends(get_db),
):
    """Doctor asks about a specific patient's records — RAG-powered."""
    if not payload.patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required for doctor chat")

    from backend.routers.doctor import _doctor_can_access_patient
    if not _doctor_can_access_patient(current_user.id, payload.patient_id, db):
        raise HTTPException(status_code=403, detail="You don't have access to this patient")

    documents = (
        db.query(Document)
        .filter(Document.patient_id == payload.patient_id)
        .all()
    )

    if not documents:
        return ChatResponse(
            answer="This patient has no uploaded documents yet.",
            sources=[],
        )

    if _has_processed_docs(payload.patient_id, db):
        try:
            from ai_pipeline.rag import generate_rag_response
            result = generate_rag_response(
                patient_id=payload.patient_id,
                user_message=payload.message,
                mode="doctor",
            )
            return ChatResponse(answer=result["answer"], sources=result["sources"])
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}")
            result = _simple_keyword_search(payload.message, documents)
            return ChatResponse(**result)
    else:
        result = _simple_keyword_search(payload.message, documents)
        return ChatResponse(**result)
