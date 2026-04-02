import os
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models.database import Document, FollowUp

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a medical follow-up extractor. Your job is to identify all follow-up instructions, appointments, tests, referrals, and action items mentioned in medical documents.

Extract every instruction that requires the patient to do something in the future. This includes:
- Follow-up appointments with specific or general timeframes
- Repeat lab tests or blood work
- Specialist referrals
- Medication reviews
- Imaging studies like X-ray, MRI, ultrasound
- Lifestyle changes with specific review dates
- Return to emergency conditions
- Vaccination due dates

For each item extract:
- follow_up_type: appointment, lab_test, referral, medication_review, imaging, lifestyle, emergency_warning, vaccination, other
- description: exact plain English description of what needs to be done
- timeframe_text: exact text from document like in 6 weeks or after 3 months or by March 2024 (null if no timeframe)
- due_date: format as strictly YYYY-MM-DD. Calculate this actual date using the BASE DOCUMENT DATE provided in the user prompt and the timeframe. If no timeframe is mentioned, output null.
- urgency: routine, soon, urgent
- specialty: which department if mentioned like cardiology, nephrology, general (null if unknown)

Return as a pure raw JSON array of objects. Do not include markdown formatting like ```json. If no follow-ups found return an empty array []. Return only valid JSON nothing else."""

def _call_groq_json(system_prompt: str, user_message: str) -> list:
    """Call the Groq API forcing a JSON output."""
    from openai import OpenAI
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY is not configured")
        
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=1500,
            temperature=0.1,
            response_format={"type": "json_object"} if "mixtral" not in model.lower() else None,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message + "\n\nRespond with a JSON object containing a 'follow_ups' array key."},
            ],
        )
        content = response.choices[0].message.content.strip()
        # Clean potential markdown wrapping if any leaked through
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        data = json.loads(content)
        if isinstance(data, dict):
            return data.get("follow_ups", [])
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Failed LLM extraction: {e}")
        return []

def extract_followups(document_id: int, db: Session):
    """
    Analyzes document text for follow-up orders, extracts them via LLM,
    and intelligently deduplicates/calculates dates before DB insertion.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not doc.content_text:
        return []

    base_date = doc.uploaded_at.strftime("%Y-%m-%d")
    user_prompt = f"BASE DOCUMENT DATE: {base_date}\n\nDOCUMENT TEXT:\n{doc.content_text}"

    extracted_items = _call_groq_json(SYSTEM_PROMPT, user_prompt)
    if not extracted_items:
        return []

    created_followups = []
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Pre-fetch recent followups to handle deductive deduplication
    recent_fups = db.query(FollowUp).filter(
        FollowUp.patient_id == doc.patient_id,
        FollowUp.created_at >= seven_days_ago
    ).all()

    for item in extracted_items:
        desc = item.get("description", "").strip()
        if not desc:
            continue
            
        f_type = item.get("follow_up_type", "other")
        
        # Deduplication Logic: If there's an existing followup within 7 days 
        # that has the exact same type and very similar timeframe/description, skip.
        is_duplicate = False
        for rf in recent_fups:
            if rf.follow_up_type == f_type and rf.document_id != doc.id:
                # Basic similarity heuristics 
                if rf.description.lower() == desc.lower():
                    is_duplicate = True
                    break
        if is_duplicate:
            continue
            
        # Date parsing
        parsed_date = None
        due_str = item.get("due_date")
        if due_str and isinstance(due_str, str):
            try:
                parsed_date = datetime.strptime(due_str.split("T")[0], "%Y-%m-%d").date()
            except ValueError:
                parsed_date = None
                
        new_fup = FollowUp(
            patient_id=doc.patient_id,
            document_id=doc.id,
            follow_up_type=f_type,
            description=desc,
            timeframe_text=item.get("timeframe_text"),
            due_date=parsed_date,
            urgency=item.get("urgency", "routine"),
            specialty=item.get("specialty"),
            status="pending"  # initial status
        )
        db.add(new_fup)
        created_followups.append(new_fup)

    if created_followups:
        db.commit()
    
    return created_followups
