"""
Question Answering Service

Implements two QA strategies:
  A) Extractive QA using DistilBERT (distilbert-base-cased-distilled-squad)
  B) Best-span sentence extraction using semantic similarity

Controlled by the USE_QA_MODEL environment variable (default: true).
"""

import os
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from transformers import pipeline
from app.services.document_processor import split_into_sentences

logger = logging.getLogger(__name__)


class QAService:
    """Dual-mode RAG answer extraction with citation generation."""

    def __init__(
        self,
        vector_store,
        qa_model_name: str = "distilbert-base-cased-distilled-squad",
    ):
        self.vector_store = vector_store
        self.qa_model_name = qa_model_name
        self.qa_pipeline = None

        self.use_qa_model_env = os.getenv("USE_QA_MODEL", "true").lower() == "true"

        if self.use_qa_model_env:
            self._load_qa_model()

    def _load_qa_model(self):
        """Load the HuggingFace extractive QA pipeline on CPU."""
        if self.qa_pipeline is not None:
            return
        try:
            logger.info(f"Loading QA model: {self.qa_model_name}...")
            self.qa_pipeline = pipeline(
                "question-answering",
                model=self.qa_model_name,
                device=-1,  # CPU
            )
            logger.info("QA model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load QA model: {e}. Will use best-span fallback.")
            self.qa_pipeline = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def answer_question(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        force_best_span: bool = False,
    ) -> Dict[str, Any]:
        """
        Answer a question given retrieved context chunks.

        Args:
            query:            User's natural-language question.
            retrieved_chunks: List of chunks from vector search.
            force_best_span:  Bypass DistilBERT and use sentence extraction.

        Returns:
            Dict with answer, confidence, citations list, and method used.
        """
        if not retrieved_chunks:
            return {
                "answer": (
                    "I could not find any relevant information in the "
                    "uploaded documents to answer your question."
                ),
                "confidence": 0.0,
                "citations": [],
                "method": "none",
            }

        use_qa = (
            self.use_qa_model_env
            and self.qa_pipeline is not None
            and not force_best_span
        )

        if use_qa:
            return self._answer_with_qa_model(query, retrieved_chunks)
        return self._answer_with_best_span(query, retrieved_chunks)

    # ------------------------------------------------------------------
    # Option A: DistilBERT extractive QA
    # ------------------------------------------------------------------
    def _answer_with_qa_model(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run extractive QA on each chunk and pick highest-confidence span."""
        best_answer = None
        best_score = -1.0
        best_chunk = None

        for chunk in chunks:
            try:
                result = self.qa_pipeline(question=query, context=chunk["text"])
                score = float(result.get("score", 0.0))
                answer = result.get("answer", "").strip()

                if score > best_score and len(answer) > 1:
                    best_score = score
                    best_answer = answer
                    best_chunk = chunk
            except Exception as e:
                logger.error(f"QA model error on chunk: {e}")

        # Fall back to best-span if confidence is too low
        if not best_answer or best_score < 0.05:
            logger.warning("QA model returned low confidence. Falling back to best-span.")
            return self._answer_with_best_span(query, chunks)

        return {
            "answer": best_answer,
            "confidence": round(best_score, 4),
            "citations": [
                {
                    "document_id": best_chunk["doc_id"],
                    "document": best_chunk["doc_name"],
                    "page": best_chunk["page_num"],
                    "excerpt": best_chunk["text"],
                }
            ],
            "method": "distilbert",
        }

    # ------------------------------------------------------------------
    # Option B: Best-span sentence extraction
    # ------------------------------------------------------------------
    def _answer_with_best_span(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Select the most semantically similar sentence from all chunks."""
        all_sentences: List[Tuple[str, Dict[str, Any]]] = []
        for chunk in chunks:
            for sent in split_into_sentences(chunk["text"]):
                all_sentences.append((sent, chunk))

        if not all_sentences:
            return {
                "answer": "No sentences could be extracted to form an answer.",
                "confidence": 0.0,
                "citations": [],
                "method": "best_span_fallback",
            }

        texts = [item[0] for item in all_sentences]
        query_emb = self.vector_store.get_embedding(query)
        sent_embs = self.vector_store.get_embeddings(texts)

        # Cosine similarity
        q_norm = np.linalg.norm(query_emb) or 1e-10
        norms = np.linalg.norm(sent_embs, axis=1)
        norms[norms == 0] = 1e-10

        similarities = np.dot(sent_embs, query_emb) / (norms * q_norm)

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])
        best_sentence, source_chunk = all_sentences[best_idx]

        # Normalize score to [0, 1]
        confidence = max(0.0, min(1.0, (best_score + 1) / 2))

        return {
            "answer": best_sentence,
            "confidence": round(confidence, 4),
            "citations": [
                {
                    "document_id": source_chunk["doc_id"],
                    "document": source_chunk["doc_name"],
                    "page": source_chunk["page_num"],
                    "excerpt": source_chunk["text"],
                }
            ],
            "method": "best_span",
        }
