"""
MedBridge — Document Processor

Handles the full pipeline:
  1. Split extracted text into overlapping chunks
  2. Generate BioBERT embeddings for each chunk
  3. Store chunks + embeddings in ChromaDB

Used after a patient uploads a document and text has been extracted.
"""

import os
import logging
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from ai_pipeline.embeddings import embed_batch

logger = logging.getLogger(__name__)

# ChromaDB persistent storage
CHROMA_DIR = os.path.join("data", "chromadb")
os.makedirs(CHROMA_DIR, exist_ok=True)

_chroma_client = None


def _get_chroma_client():
    """Get or create the persistent ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        logger.info(f"ChromaDB client initialized at {CHROMA_DIR}")
    return _chroma_client


def _get_collection(patient_id: int):
    """Get or create a ChromaDB collection for a specific patient."""
    client = _get_chroma_client()
    collection_name = f"patient_{patient_id}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Text Chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[str]:
    """
    Split text into overlapping chunks of approximately `chunk_size` characters.
    Tries to split on sentence boundaries when possible.
    """
    if not text or not text.strip():
        return []

    # Clean up whitespace
    text = " ".join(text.split())

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If we're not at the end, try to find a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the end
            search_start = max(end - 50, start)
            best_break = -1
            for sep in [". ", ".\n", "! ", "? ", "\n\n"]:
                idx = text.rfind(sep, search_start, end + 50)
                if idx > best_break:
                    best_break = idx + len(sep)

            if best_break > start:
                end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward with overlap
        start = end - chunk_overlap if end < len(text) else len(text)

    return chunks


# ---------------------------------------------------------------------------
# Process & Store
# ---------------------------------------------------------------------------

def process_document(
    patient_id: int,
    document_id: int,
    content_text: str,
    original_filename: str,
    doc_type: str = "general",
) -> int:
    """
    Process a document's extracted text:
      1. Chunk the text
      2. Generate embeddings
      3. Store in ChromaDB

    Returns the number of chunks stored.
    """
    if not content_text or not content_text.strip():
        logger.warning(f"Document {document_id} has no text content to process")
        return 0

    chunks = chunk_text(content_text)
    if not chunks:
        logger.warning(f"Document {document_id} produced no chunks")
        return 0

    logger.info(f"Processing document {document_id}: {len(chunks)} chunks")

    # Generate embeddings
    embeddings = embed_batch(chunks)

    # Prepare metadata for each chunk
    ids = [f"doc{document_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "patient_id": patient_id,
            "chunk_index": i,
            "source_file": original_filename,
            "doc_type": doc_type,
        }
        for i in range(len(chunks))
    ]

    # Store in ChromaDB
    collection = _get_collection(patient_id)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(f"Stored {len(chunks)} chunks for document {document_id} in ChromaDB")
    return len(chunks)


def delete_document_chunks(patient_id: int, document_id: int):
    """Remove all chunks for a specific document from ChromaDB."""
    try:
        collection = _get_collection(patient_id)
        # Get all IDs matching this document
        results = collection.get(
            where={"document_id": document_id},
        )
        if results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
    except Exception as e:
        logger.error(f"Error deleting chunks for document {document_id}: {e}")


def query_patient_documents(
    patient_id: int,
    query_text: str,
    n_results: int = 5,
) -> List[dict]:
    """
    Query ChromaDB for the most relevant chunks to a given question.

    Returns a list of dicts with keys: text, source_file, doc_type, score
    """
    from ai_pipeline.embeddings import embed_text

    collection = _get_collection(patient_id)

    # Check if collection has any documents
    if collection.count() == 0:
        return []

    query_embedding = embed_text(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
    )

    formatted = []
    for i in range(len(results["documents"][0])):
        formatted.append({
            "text": results["documents"][0][i],
            "source_file": results["metadatas"][0][i].get("source_file", "Unknown"),
            "doc_type": results["metadatas"][0][i].get("doc_type", "general"),
            "score": 1 - results["distances"][0][i],  # cosine sim = 1 - distance
        })

    return formatted
