"""Dependency-free extractive question answering for serverless use."""

from typing import Any, Dict, List, Tuple

from app.services.document_processor import split_into_sentences


class QAService:
    """Select the sentence most relevant to a question and cite its source."""

    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.qa_pipeline = None
        self.use_qa_model_env = False

    def answer_question(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        force_best_span: bool = False,
    ) -> Dict[str, Any]:
        if not retrieved_chunks:
            return {
                "answer": "I could not find relevant information in the uploaded documents.",
                "confidence": 0.0,
                "citations": [],
                "method": "none",
            }

        sentences: List[Tuple[str, Dict[str, Any]]] = []
        for chunk in retrieved_chunks:
            sentences.extend((sentence, chunk) for sentence in split_into_sentences(chunk["text"]))

        if not sentences:
            return {
                "answer": "No sentences could be extracted to form an answer.",
                "confidence": 0.0,
                "citations": [],
                "method": "lexical_best_span",
            }

        query_embedding = self.vector_store.get_embedding(query)
        best_sentence, best_chunk = max(
            sentences,
            key=lambda item: self.vector_store.similarity(
                query_embedding,
                self.vector_store.get_embedding(item[0]),
            ),
        )
        confidence = self.vector_store.similarity(
            query_embedding,
            self.vector_store.get_embedding(best_sentence),
        )

        return {
            "answer": best_sentence,
            "confidence": round(confidence, 4),
            "citations": [{
                "document_id": best_chunk["doc_id"],
                "document": best_chunk["doc_name"],
                "page": best_chunk["page_num"],
                "excerpt": best_chunk["text"],
            }],
            "method": "lexical_best_span",
        }
