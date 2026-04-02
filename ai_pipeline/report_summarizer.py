import os
import logging
from sqlalchemy.orm import Session
from backend.models.database import Document

logger = logging.getLogger(__name__)

PATIENT_SYSTEM_PROMPT = """You are a friendly medical report interpreter helping a patient understand their health documents. Your job is to explain medical reports in simple everyday language that anyone can understand without medical training.

Rules:
- Never use medical jargon without immediately explaining it
- Always tell the patient what a value means for their health
- Be honest about concerning values but never alarming
- Always recommend discussing findings with their doctor
- Never make a diagnosis
- Structure your response exactly as specified
- Use simple short sentences
- If a value is abnormal explain why it matters in plain terms
- Always end with actionable next steps for the patient
- Always show a disclaimer below every summary: "This summary is AI-generated to help you understand your documents. It is not a medical diagnosis. Always discuss your results with your doctor."

SPECIAL CASES TO HANDLE:
- If document text is too short or unclear, just return: "Could not generate summary — document may be incomplete or unclear"
- If document is a radiology report, note that imaging interpretation requires a radiologist and only summarize the written findings section.
- If document is in a language other than English, attempt to detect the language and translate before summarizing.
"""

CLINICAL_SYSTEM_PROMPT = """You are a clinical decision support assistant summarizing medical documents for a qualified physician.

Rules:
- Use precise clinical terminology
- Include exact values with units and reference ranges
- Flag clinically significant findings clearly
- Note any values that have changed from previous readings if context is available
- Highlight urgent or actionable findings at the top
- Be concise and direct — the reader is a medical professional
- Do not add unnecessary caveats or patient-friendly language

SPECIAL CASES TO HANDLE:
- If document text is too short or unclear, just return: "Could not generate summary — document may be incomplete or unclear"
- If document is a radiology report, only summarize the clinical findings.
- If document is in a language other than English, translate to clinical English.
"""

def _call_groq(system_prompt: str, user_message: str) -> str:
    """Call the Groq API."""
    from openai import OpenAI
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not configured")
        
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    
    # Using LLaMA 3.3 70B Versatile for clinical reasoning
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    response = client.chat.completions.create(
        model=model,
        max_tokens=1500,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content

def generate_report_summary(document_id: int, db: Session):
    """
    Generates both patient-facing and clinical summaries for a given document using Claude.
    Saves the results directly to the database record.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not doc.content_text:
        return None

    # Do not regenerate if they already exist, unless this function was called manually for a refresh
    # For now, let's just generate and overwrite unconditionally to support the refresh use case.

    text = doc.content_text
    
    # Step 1: Detect Document Type (basic heuristic to help the LLM)
    # The LLM is smart enough to structure it correctly if given the raw text.
    user_prompt = f"DOCUMENT TYPE: {doc.doc_type}\n\nDOCUMENT TEXT:\n{text}\n\nGenerate the summary based on your system instructions."

    try:
        # Generate Patient Summary
        patient_summary = _call_groq(PATIENT_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        logger.error(f"Failed to generate patient summary for doc {document_id}: {e}")
        patient_summary = "Summary generation failed. You can try again or ask the chatbot about this document."
        
    try:
        # Generate Clinical Summary
        clinical_summary = _call_groq(CLINICAL_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        logger.error(f"Failed to generate clinical summary for doc {document_id}: {e}")
        clinical_summary = "Summary generation failed. You can try again or ask the chatbot about this document."

    # Save to db
    doc.patient_summary = patient_summary
    doc.clinical_summary = clinical_summary
    db.commit()
    db.refresh(doc)
    
    return doc
