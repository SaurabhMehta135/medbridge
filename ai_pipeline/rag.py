"""
MedBridge — RAG (Retrieval-Augmented Generation) Pipeline

Combines ChromaDB vector search with LLM generation to answer
questions about a patient's medical records.

Supports LLM providers (checked in priority order):
  1. Groq  (GROQ_API_KEY)  — recommended, uses llama-4-scout
  2. Anthropic (ANTHROPIC_API_KEY) — Claude
  3. OpenAI (OPENAI_API_KEY) — GPT-4o-mini
  4. Fallback — keyword-based, no LLM

Supports two response modes:
  - Patient mode: simplified, empathetic language
  - Doctor mode: clinical, detailed, evidence-based language
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model Configuration
# ---------------------------------------------------------------------------

# Primary: LLaMA 4 Scout on Groq — 30K context, MoE architecture, best for medical RAG
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
# Fallback Groq model (70B, stronger reasoning but smaller context)
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


# ---------------------------------------------------------------------------
# Provider Detection
# ---------------------------------------------------------------------------

def _get_llm_client():
    """Get the appropriate LLM client based on available API keys.
    Priority: Groq > Anthropic > OpenAI > None
    """
    groq_key = os.getenv("GROQ_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key and groq_key != "your_groq_api_key_here":
        return "groq", groq_key
    elif anthropic_key and anthropic_key != "your_anthropic_api_key_here":
        return "anthropic", anthropic_key
    elif openai_key and openai_key != "your_openai_api_key_here":
        return "openai", openai_key
    else:
        return None, None


# ---------------------------------------------------------------------------
# Context Building
# ---------------------------------------------------------------------------

def _build_context(chunks: List[dict]) -> str:
    """Format retrieved chunks into a context string for the LLM prompt."""
    if not chunks:
        return "No relevant medical records found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source_file", "Unknown")
        score = chunk.get("score", 0)
        text = chunk.get("text", "")
        context_parts.append(
            f"[Source {i}: {source} (relevance: {score:.2f})]\n{text}"
        )

    return "\n\n---\n\n".join(context_parts)


# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

PATIENT_SYSTEM_PROMPT = """You are MedBridge Health Assistant, helping a patient understand their medical records.

Rules:
- Use simple, clear language a non-medical person can understand
- Be empathetic and reassuring while remaining accurate
- Always recommend consulting their doctor for medical decisions
- If the records don't contain relevant information, say so clearly
- Never make up medical information — only use what's in the provided records
- Cite which document the information comes from when possible

Context from the patient's medical records:
{context}"""

DOCTOR_SYSTEM_PROMPT = """You are MedBridge Clinical Assistant, helping a doctor review a patient's medical records efficiently.

Rules:
- Use precise clinical terminology
- Highlight critical findings, abnormal values, and potential concerns
- Note any contradictions or gaps in the records
- Reference specific documents and sections
- Flag potential drug interactions or allergy risks if relevant
- Be concise and evidence-based

Context from the patient's medical records:
{context}"""


# ---------------------------------------------------------------------------
# LLM Callers
# ---------------------------------------------------------------------------

def _call_groq(api_key: str, system_prompt: str, user_message: str) -> str:
    """
    Call the Groq API using llama-4-scout (OpenAI-compatible endpoint).
    Falls back to llama-3.3-70b if the primary model fails.
    """
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
        )

        model = GROQ_MODEL
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=1024,
                temperature=0.3,  # lower temperature for medical accuracy
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            logger.info(f"Groq response generated using {model}")
            return response.choices[0].message.content

        except Exception as primary_error:
            logger.warning(f"Primary model {model} failed: {primary_error}. Trying fallback...")
            # Try fallback model
            response = client.chat.completions.create(
                model=GROQ_FALLBACK_MODEL,
                max_tokens=1024,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            logger.info(f"Groq response generated using fallback {GROQ_FALLBACK_MODEL}")
            return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise


def _call_anthropic(api_key: str, system_prompt: str, user_message: str) -> str:
    """Call the Anthropic Claude API."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        raise


def _call_openai(api_key: str, system_prompt: str, user_message: str) -> str:
    """Call the OpenAI API."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise


# ---------------------------------------------------------------------------
# Fallback (no LLM)
# ---------------------------------------------------------------------------

def _fallback_response(chunks: List[dict], user_message: str, mode: str) -> str:
    """
    Generate a structured response WITHOUT an LLM when no API key is available.
    Uses the retrieved chunks directly.
    """
    if not chunks:
        return (
            "I couldn't find relevant information in the medical records for your question. "
            "Please try rephrasing or ensure the relevant documents have been uploaded."
        )

    response_parts = ["Based on the uploaded medical records, here's what I found:\n"]

    for i, chunk in enumerate(chunks[:3], 1):
        source = chunk.get("source_file", "Unknown")
        text = chunk["text"]
        if len(text) > 300:
            text = text[:300] + "..."
        response_parts.append(f"**{i}. From: {source}**\n{text}\n")

    if mode == "patient":
        response_parts.append(
            "\n💡 *This is a keyword-based search of your records. "
            "For AI-powered analysis, add your GROQ_API_KEY to the .env file. "
            "Always consult your doctor for medical advice.*"
        )
    else:
        response_parts.append(
            "\n📋 *Keyword-based retrieval (no LLM configured). "
            "Configure GROQ_API_KEY for AI-powered clinical summaries using LLaMA 4 Scout.*"
        )

    return "\n".join(response_parts)


# ---------------------------------------------------------------------------
# Main RAG Pipeline
# ---------------------------------------------------------------------------

def generate_rag_response(
    patient_id: int,
    user_message: str,
    mode: str = "patient",  # "patient" or "doctor"
    n_chunks: int = 5,
) -> dict:
    """
    Full RAG pipeline:
      1. Retrieve relevant chunks from ChromaDB
      2. Build context prompt
      3. Call LLM (Groq/Anthropic/OpenAI or fallback)
      4. Return answer + sources

    Returns: {"answer": str, "sources": List[str]}
    """
    from ai_pipeline.document_processor import query_patient_documents

    # Step 1: Retrieve relevant document chunks
    chunks = query_patient_documents(patient_id, user_message, n_results=n_chunks)
    sources = list({c["source_file"] for c in chunks})

    # Step 2: Build context + system prompt
    context = _build_context(chunks)
    system_prompt = (
        PATIENT_SYSTEM_PROMPT if mode == "patient" else DOCTOR_SYSTEM_PROMPT
    ).format(context=context)

    # Step 3: Generate response via LLM
    provider, api_key = _get_llm_client()

    try:
        if provider == "groq":
            answer = _call_groq(api_key, system_prompt, user_message)
        elif provider == "anthropic":
            answer = _call_anthropic(api_key, system_prompt, user_message)
        elif provider == "openai":
            answer = _call_openai(api_key, system_prompt, user_message)
        else:
            logger.info("No LLM API key configured — using fallback response")
            answer = _fallback_response(chunks, user_message, mode)
    except Exception as e:
        logger.error(f"LLM call failed, falling back: {e}")
        answer = _fallback_response(chunks, user_message, mode)

    return {"answer": answer, "sources": sources}
