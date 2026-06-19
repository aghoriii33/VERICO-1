"""
FAISS Vector Store

Manages in-memory document embeddings using SentenceTransformers (all-MiniLM-L6-v2)
and a FAISS IndexFlatIP (inner-product / cosine similarity) index.

Falls back gracefully to NumPy-based cosine similarity when FAISS is unavailable.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Try to import FAISS; fall back to pure NumPy if not installed
try:
    import faiss

    FAISS_AVAILABLE = True
    logger.info("FAISS-CPU successfully imported.")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS-CPU not found. Falling back to NumPy-based vector search.")


class VectorStore:
    """Semantic embedding store with FAISS / NumPy cosine similarity search."""

    DIMENSION = 384  # all-MiniLM-L6-v2 output dimensionality

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name, device="cpu")

        # Internal storage
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings_list: List[np.ndarray] = []

        # FAISS index (rebuilt after every mutation)
        self.faiss_index = None

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------
    def get_embedding(self, text: str) -> np.ndarray:
        """Generate a single embedding vector."""
        return self.model.encode(text, convert_to_numpy=True)

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Batch-encode a list of texts."""
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------
    def add_documents(
        self,
        doc_id: str,
        doc_name: str,
        doc_chunks: List[Dict[str, Any]],
    ):
        """Embed and index chunks from a document."""
        if not doc_chunks:
            return

        texts = [chunk["text"] for chunk in doc_chunks]
        embeddings = self.get_embeddings(texts)

        for i, chunk in enumerate(doc_chunks):
            self.chunks.append({
                "doc_id": doc_id,
                "doc_name": doc_name,
                "page_num": chunk["metadata"]["page_num"],
                "text": chunk["text"],
            })
            self.embeddings_list.append(embeddings[i])

        self._build_index()

    def remove_document(self, doc_id: str):
        """Remove a document's vectors and rebuild the index."""
        keep = [i for i, c in enumerate(self.chunks) if c["doc_id"] != doc_id]
        self.chunks = [self.chunks[i] for i in keep]
        self.embeddings_list = [self.embeddings_list[i] for i in keep]
        self._build_index()

    def clear(self):
        """Wipe all vectors."""
        self.chunks = []
        self.embeddings_list = []
        self.faiss_index = None

    def _build_index(self):
        """Rebuild the FAISS inner-product index from current embeddings."""
        if not self.embeddings_list:
            self.faiss_index = None
            return

        matrix = np.vstack(self.embeddings_list).astype("float32")

        if FAISS_AVAILABLE:
            try:
                self.faiss_index = faiss.IndexFlatIP(self.DIMENSION)
                faiss.normalize_L2(matrix)
                self.faiss_index.add(matrix)
                logger.info(f"Rebuilt FAISS index with {len(self.chunks)} vectors.")
            except Exception as e:
                logger.error(f"FAISS index build failed: {e}. Falling back to NumPy.")
                self.faiss_index = None
        else:
            self.faiss_index = None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search for a query string.

        Args:
            query:   Natural-language question.
            top_k:   Number of results to return.
            doc_ids: Optional filter to restrict search to specific documents.

        Returns:
            List of matching chunks with similarity scores.
        """
        if not self.chunks:
            return []

        query_emb = self.get_embedding(query).astype("float32")
        results: List[Dict[str, Any]] = []

        # --- FAISS path ---
        if FAISS_AVAILABLE and self.faiss_index is not None:
            try:
                q = query_emb.reshape(1, -1)
                faiss.normalize_L2(q)

                search_k = min(len(self.chunks), top_k * 3 if doc_ids else top_k)
                distances, indices = self.faiss_index.search(q, search_k)

                for score, idx in zip(distances[0], indices[0]):
                    if idx == -1:
                        continue
                    chunk = self.chunks[idx]
                    if doc_ids and chunk["doc_id"] not in doc_ids:
                        continue
                    results.append({
                        "doc_id": chunk["doc_id"],
                        "doc_name": chunk["doc_name"],
                        "page_num": chunk["page_num"],
                        "text": chunk["text"],
                        "score": float(score),
                    })
                    if len(results) >= top_k:
                        break
                return results
            except Exception as e:
                logger.error(f"FAISS search failed: {e}. Falling back to NumPy.")

        # --- NumPy fallback ---
        q_norm = np.linalg.norm(query_emb) or 1e-10

        scored = []
        for idx, emb in enumerate(self.embeddings_list):
            chunk = self.chunks[idx]
            if doc_ids and chunk["doc_id"] not in doc_ids:
                continue
            e_norm = np.linalg.norm(emb) or 1e-10
            score = float(np.dot(emb, query_emb) / (e_norm * q_norm))
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        for score, chunk in scored[:top_k]:
            results.append({
                "doc_id": chunk["doc_id"],
                "doc_name": chunk["doc_name"],
                "page_num": chunk["page_num"],
                "text": chunk["text"],
                "score": score,
            })
        return results
