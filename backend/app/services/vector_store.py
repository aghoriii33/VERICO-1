"""Lightweight in-memory document search for serverless deployments."""

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class VectorStore:
    """Document store using dependency-free lexical cosine similarity."""

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings_list: List[Counter] = []
        self.faiss_index = None

    @staticmethod
    def get_embedding(text: str) -> Counter:
        return Counter(TOKEN_PATTERN.findall(text.lower()))

    def get_embeddings(self, texts: List[str]) -> List[Counter]:
        return [self.get_embedding(text) for text in texts]

    @staticmethod
    def similarity(left: Counter, right: Counter) -> float:
        if not left or not right:
            return 0.0
        shared = left.keys() & right.keys()
        dot = sum(left[token] * right[token] for token in shared)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

    def add_documents(
        self,
        doc_id: str,
        doc_name: str,
        doc_chunks: List[Dict[str, Any]],
    ):
        for chunk in doc_chunks:
            text = chunk["text"]
            self.chunks.append({
                "doc_id": doc_id,
                "doc_name": doc_name,
                "page_num": chunk["metadata"]["page_num"],
                "text": text,
            })
            self.embeddings_list.append(self.get_embedding(text))

    def remove_document(self, doc_id: str):
        keep = [i for i, chunk in enumerate(self.chunks) if chunk["doc_id"] != doc_id]
        self.chunks = [self.chunks[i] for i in keep]
        self.embeddings_list = [self.embeddings_list[i] for i in keep]

    def clear(self):
        self.chunks = []
        self.embeddings_list = []

    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        query_embedding = self.get_embedding(query)
        scored = []

        for chunk, embedding in zip(self.chunks, self.embeddings_list):
            if doc_ids and chunk["doc_id"] not in doc_ids:
                continue
            scored.append((self.similarity(query_embedding, embedding), chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {**chunk, "score": float(score)}
            for score, chunk in scored[:top_k]
        ]
