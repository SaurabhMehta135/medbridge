"""
MedBridge — BioBERT Embedding Wrapper

Uses sentence-transformers with a BioBERT model fine-tuned for medical NLI.
Provides embed_text() and embed_batch() for generating vector embeddings
of medical document chunks.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model = None
_MODEL_NAME = "pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-scinli"

# Fallback if the primary model fails to load
_FALLBACK_MODEL = "all-MiniLM-L6-v2"


def _get_model():
    """Lazy-load the sentence-transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {_MODEL_NAME}")
            _model = SentenceTransformer(_MODEL_NAME)
            logger.info("BioBERT model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load BioBERT model: {e}. Falling back to {_FALLBACK_MODEL}")
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(_FALLBACK_MODEL)
            logger.info(f"Fallback model {_FALLBACK_MODEL} loaded successfully")
    return _model


def embed_text(text: str) -> List[float]:
    """Generate an embedding vector for a single text string."""
    model = _get_model()
    embedding = model.encode(text, show_progress_bar=False)
    return embedding.tolist()


def embed_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Generate embeddings for a batch of text strings."""
    model = _get_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    return [e.tolist() for e in embeddings]


def get_embedding_dimension() -> int:
    """Return the dimension of the embedding vectors."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()
